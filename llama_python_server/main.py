def _read_stderr_tail(lines: int = 300) -> str:
    """Read the last N lines from the llama_stderr.log file for diagnostics."""
    stderr_log = os.path.join(LOG_DIR, 'llama_stderr.log')
    try:
        with open(stderr_log, 'rb') as f:
            data = f.read()
        text = data.decode('utf-8', errors='replace')
        tail_lines = text.splitlines()[-lines:]
        return "\n".join(tail_lines)
    except FileNotFoundError:
        return "(no stderr log yet)"
def _wait_for_gpu_free(timeout: int = 30, poll_interval: float = 1.0) -> bool:
    """Wait until no processes are using the GPU (per nvidia-smi) or timeout."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        procs = _gpu_processes()
        if not procs:
            return True
        time.sleep(poll_interval)
    return False

import os
from .fallbacks import _attempt_start_with_fallbacks
import sys
import subprocess
import requests
import time
import threading
import json

import psutil
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, List
import uvicorn



# --- Move all helper function definitions above their first usage ---



def start_llama_server(config_path=None, model_path=None):
    global llama_process, current_model, last_used_config
    with process_lock:
        cfg_path = config_path or QWEN_CONFIG
        config = load_config(cfg_path)
        if model_path:
            config['modelPath'] = model_path
        if llama_process and llama_process.poll() is None:
            print(f"[INFO] Stoppe aktuellen llama-server Prozess...")
            llama_process.terminate()
            try:
                llama_process.wait(timeout=15)
            except Exception:
                llama_process.kill()
        gpu_free = _wait_for_gpu_free(timeout=30)
        if not gpu_free:
            tail = _read_stderr_tail()
            _write_last_error_log(tail)
            print("[ERROR] GPU still in use after waiting 30s; refusing to start new model until GPU is free")
            globals()['last_start_error'] = tail
            return False
        # Enforce GPU usage: n-gpu-layers must be > 0
        if int(config.get('gpuLayers', 0)) <= 0:
            msg = "[ERROR] Refusing to start: n-gpu-layers must be > 0 for GPU mode."
            _write_last_error_log(msg)
            globals()['last_start_error'] = msg
            print(msg)
            return False
        print(f"[INFO] Starte llama-server mit Config: {cfg_path} (model: {config['modelPath']})")
        model_path_val = config['modelPath'].lower()
        if 'qwen' in model_path_val:
            if str(config.get('cacheV', '')).lower() not in ("auto", "f16", "q4_0", "q4_1", "q5_0", "q5_1", "q8_0"):
                config['cacheV'] = "auto"
            if str(config.get('flashAttn', '')).lower() not in ("auto", "1", "0"):
                config['flashAttn'] = "auto"
        elif 'mistral' in model_path_val:
            if str(config.get('cacheV', '')).lower() not in ("q8_0", "auto", "f16", "q4_0", "q4_1", "q5_0", "q5_1"):
                config['cacheV'] = "q8_0"
            if str(config.get('flashAttn', '')).lower() not in ("0", "auto", "1"):
                config['flashAttn'] = "0"
        cmd = [
            config.get('llamaCppPath', LLAMA_SERVER_EXE),
            "--model", config['modelPath'],
            "--chat-template", config.get('chatTemplate', 'chatml'),
            "--host", "127.0.0.1",
            "--port", str(config['port']),
            "--ctx-size", str(config['ctxSize']),
            "--batch-size", str(config['batchSize']),
            "--ubatch-size", str(config['ubatchSize']),
            "--parallel", str(config['parallel']),
            "--threads", str(config['threads']),
            "--n-gpu-layers", str(config['gpuLayers']),
            "--cache-type-k", config['cacheK'],
            "--cache-type-v", config['cacheV'],
            "--temp", str(config['temp']),
            "--top-k", str(config['topK']),
            "--top-p", str(config['topP']),
            "--repeat-penalty", str(config['repeatPen']),
            "--mirostat", str(config['mirostat']),
            "--flash-attn", str(config.get('flashAttn', 'auto'))
        ]
        stdout_log = os.path.join(LOG_DIR, 'llama_stdout.log')
        stderr_log = os.path.join(LOG_DIR, 'llama_stderr.log')
        out_f = open(stdout_log, 'ab')
        err_f = open(stderr_log, 'ab')
        creationflags = 0
        try:
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW
        except Exception:
            creationflags = 0
        llama_process = subprocess.Popen(
            cmd,
            stdout=out_f,
            stderr=err_f,
            cwd=os.path.dirname(config.get('llamaCppPath', LLAMA_SERVER_EXE)),
            creationflags=creationflags,
            close_fds=False
        )
        current_model = config['modelPath']
        last_used_config = cfg_path
        port = config.get('port')
        start_time = time.time()
        ready = False
        for _ in range(12):
            if llama_process.poll() is not None:
                break
            try:
                resp = requests.get(f"http://127.0.0.1:{port}/health", timeout=1.0)
                if resp.status_code == 200:
                    ready = True
                    break
            except Exception:
                pass
            time.sleep(1)
        if ready:
            print(f"[OK] llama-server gestartet (PID {llama_process.pid}) mit Modell: {current_model}")
            try:
                globals()['last_start_error'] = None
                globals()['restart_fail_count'] = 0
            except Exception:
                pass
            return True
        stderr_tail = _read_stderr_tail()
        globals()['last_start_error'] = stderr_tail
        _write_last_error_log(stderr_tail)
        print(f"[WARN] llama-server start failed, trying fallbacks (see logs/last_start_error.log)")
        if llama_process and llama_process.poll() is None:
            try:
                llama_process.terminate()
                llama_process.wait(timeout=5)
            except Exception:
                llama_process.kill()
        ok = _attempt_start_with_fallbacks(cfg_path, model_override=model_path)
        if ok:
            return True
        print(f"[ERROR] Alle Startversuche fehlgeschlagen für {cfg_path}")
        return False

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        start_llama_server(QWEN_CONFIG)
    except Exception as e:
        print(f"[LIFESPAN][WARN] initial start failed: {e}")
    t = threading.Thread(target=monitor_llama_process, daemon=True)
    t.start()
    try:
        yield
    finally:
        global llama_process
        if llama_process and llama_process.poll() is None:
            try:
                llama_process.terminate()
                llama_process.wait(timeout=10)
            except Exception:
                llama_process.kill()

app = FastAPI(title="Llama.cpp Server Proxy with Model Switching", lifespan=lifespan)

# Pfad zum llama-server.exe
LLAMA_SERVER_EXE = r"C:\llama\llama-server.exe"

# Config-Pfade
QWEN_CONFIG = r"../llama_config.json"
MISTRAL_CONFIG = r"../mistral_config.json"

# Globaler Prozess und Lock
llama_process = None
process_lock = threading.Lock()
current_model = None
last_used_config = None
# last_start_error enthält die letzten stderr-Tail-Zeilen, wenn Start fehlschlägt
last_start_error: str | None = None
# Zähler für fehlschläge zur Backoff-Berechnung im Monitor
restart_fail_count = 0
LOG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "logs"))
os.makedirs(LOG_DIR, exist_ok=True)

CONTINUE_CONFIG = os.path.expanduser(r"~/.continue/config.yaml")

class CompletionRequest(BaseModel):
    prompt: str
    n_predict: Optional[int] = 200
    temperature: Optional[float] = 0.7
    stop: Optional[List[str]] = None
    model: Optional[str] = None

class SwitchModelRequest(BaseModel):
    model_path: str

def load_config(config_path):
    with open(config_path, 'r') as f:
        return json.load(f)['llama_cpp']


def _gpu_processes():
    """Return a list of dicts with GPU-using processes via nvidia-smi, or [] if none / not available.
    Each dict: {'pid': int, 'process_name': str, 'used_memory_mib': int}
    """
    try:
        out = subprocess.check_output([
            'nvidia-smi',
            '--query-compute-apps=pid,process_name,used_gpu_memory',
            '--format=csv,noheader,nounits'
        ], stderr=subprocess.DEVNULL)
        text = out.decode('utf-8', errors='replace').strip()
        if not text:
            return []
        procs = []
        for line in text.splitlines():
            parts = [p.strip() for p in line.split(',')]
            if len(parts) < 3:
                continue
            pid_s, pname, mem_s = parts[0:3]
            try:
                pid = int(pid_s)
                mem = int(mem_s)
            except Exception:
                continue
            procs.append({'pid': pid, 'process_name': pname, 'used_memory_mib': mem})
        return procs
    except FileNotFoundError:
        # nvidia-smi not available on system — return empty so we don't block
        return []
    except Exception:
        return []



# Lifespan handles startup/shutdown

@app.post("/v1/completions")
def completions(req: CompletionRequest):
    """Simple completion endpoint used internally and by lightweight clients.
    Supports `model` field with values: 'mistral' -> `mistral_config.json`, anything else -> `qwen_config.json`.
    """
    global current_model
    # map short model names to configs
    model_map = {
        'mistral': MISTRAL_CONFIG,
        'qwen': QWEN_CONFIG,
        'qwen2.5': QWEN_CONFIG,
        'qwen2.5-coder': QWEN_CONFIG
    }
    target_config = model_map.get((req.model or '').lower(), QWEN_CONFIG)
    target_model = load_config(target_config)['modelPath']

    if current_model != target_model:
        print(f"[INFO] Wechsle Modell zu: {target_model}")
        ok = start_llama_server(target_config)
        if not ok:
            # surface helpful error to client
            raise HTTPException(status_code=503, detail={
                'error': 'model_start_failed',
                'model': req.model,
                'hint': 'see /last_start_error and logs/last_start_error.log',
            })

    if not llama_process or llama_process.poll() is not None:
        raise HTTPException(status_code=503, detail={
            'error': 'server_unavailable',
            'hint': 'llama-server not running; check /last_start_error'
        })

    # Forward to llama-server HTTP API
    config = load_config(target_config)
    port = config['port']
    url = f"http://127.0.0.1:{port}/completion"
    data = {
        "prompt": req.prompt,
        "n_predict": req.n_predict or config.get('nPredict', 200),
        "temperature": req.temperature or config.get('temp', 0.7),
        "stop": req.stop or []
    }

def _write_last_error_log(text: str):
    log_path = os.path.join(LOG_DIR, 'last_start_error.log')
    try:
        with open(log_path, 'w', encoding='utf-8') as f:
            f.write(text)
    except Exception as e:
        print(f"[ERROR] Failed to write last error log: {e}")


@app.post('/admin/stop_all_project_processes')
def admin_stop_all_project_processes():
    """Force-stopps any processes that look like they're from this workspace (llama-server, proxy python).
    Use when you need to completely free GPU + host RAM before starting a new model.
    """
    stopped = []
    # Stop llama-server processes
    for p in (GetProcessesByName := []):
        pass
    # best-effort: stop processes with command lines containing the workspace folder name
    workspace_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    try:
        import psutil
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'exe', 'memory_info']):
            try:
                cmd = ' '.join(proc.info.get('cmdline') or [])
            except Exception:
                cmd = ''
            if not cmd:
                continue
            if 'llama-server' in (proc.info.get('name') or '').lower() or workspace_path.lower() in cmd.lower():
                pid = proc.info['pid']
                try:
                    proc.kill()
                    stopped.append({'pid': pid, 'name': proc.info.get('name')})
                except Exception:
                    pass
    except Exception:
        # fallback: try to stop known process names via taskkill
        try:
            subprocess.run(['taskkill', '/F', '/IM', 'llama-server.exe'], check=False)
        except Exception:
            pass
    return {'stopped': stopped}



def monitor_llama_process():
    """Überwacht den llama-server Prozess und versucht Neustart bei Absturz.
    Implementiert exponentiellen Backoff bei wiederholten Abstürzen.
    """
    global llama_process, last_used_config, restart_fail_count
    while True:
        time.sleep(3)
        with process_lock:
            if llama_process is None:
                continue
            if llama_process.poll() is not None:
                restart_fail_count = min(restart_fail_count + 1, 10)
                backoff = min(2 ** restart_fail_count, 60)
                print(f"[MONITOR] llama-server beendet mit Code {llama_process.returncode}, restart_try={restart_fail_count}, sleeping {backoff}s before restart...")
        # sleep outside lock to give other threads access
        time.sleep(backoff)
        with process_lock:
            if last_used_config:
                try:
                    ok = start_llama_server(last_used_config)
                    if not ok:
                        print("[MONITOR][ERROR] Restart attempts failed; will retry with backoff")
                except Exception as e:
                    print(f"[MONITOR][ERROR] Neustart fehlgeschlagen: {e}")

@app.get("/health")
def health():
    if llama_process and llama_process.poll() is None:
        return {"status": "ok", "model_path": current_model}
    else:
        return {"status": "error", "model_path": current_model}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8080)