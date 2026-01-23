# ============================================================
# HYBRID QLoRA NF4 Training Script (FAST ≤ 5.8 GB VRAM)
# Qwen2.5-Coder-7B
# ============================================================

import torch
import gc
import psutil
import time
from datasets import load_dataset
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    TrainingArguments,
    Trainer,
    BitsAndBytesConfig,
    DataCollatorForLanguageModeling,
    TrainerCallback,
)
from peft import (
    LoraConfig,
    get_peft_model,
    prepare_model_for_kbit_training,
    TaskType,
)

# ------------------------------------------------------------
# VRAM / Compute
# ------------------------------------------------------------
torch.set_float32_matmul_precision("medium")

# ------------------------------------------------------------
# Paths
# ------------------------------------------------------------
MODEL_PATH = "/mnt/d/AI-Models/training/Qwen2.5-Coder-7b/Original/Qwen2.5-Coder-7B"
TRAIN_FILE = "/mnt/c/Users/marku/Documents/Github/artqcid/ai-projects/qwen2.5-7b-training/python/dataset_juce8_complete_full/train.jsonl"
VAL_FILE   = "/mnt/c/Users/marku/Documents/Github/artqcid/ai-projects/qwen2.5-7b-training/python/dataset_juce8_complete_full/val.jsonl"

OUTPUT_DIR = "/mnt/d/AI-Models/training/Qwen2.5-Coder-7b/Trained"

MAX_SEQ_LEN = 512
BATCH_SIZE = 1
GRAD_ACC = 48   # 🚀 faster, still < 5.8 GB

# ------------------------------------------------------------
# Clean start
# ------------------------------------------------------------
torch.cuda.empty_cache()
gc.collect()

# ------------------------------------------------------------
# Dataset
# ------------------------------------------------------------
print("📥 Loading dataset...")
dataset = load_dataset(
    "json",
    data_files={"train": TRAIN_FILE, "validation": VAL_FILE}
)

# ------------------------------------------------------------
# Tokenizer
# ------------------------------------------------------------
tokenizer = AutoTokenizer.from_pretrained(
    MODEL_PATH,
    trust_remote_code=True,
)
tokenizer.pad_token = tokenizer.eos_token
tokenizer.pad_token_id = tokenizer.eos_token_id
tokenizer.padding_side = "right"

def tokenize(example):
    messages = [
        {"role": "user", "content": example["prompt"]},
        {"role": "assistant", "content": example["completion"]},
    ]
    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=False,
    )
    return tokenizer(
        text,
        truncation=True,
        max_length=MAX_SEQ_LEN,
    )

print("🔧 Tokenizing dataset...")
dataset = dataset.map(
    tokenize,
    remove_columns=dataset["train"].column_names,
)

# ------------------------------------------------------------
# QLoRA NF4 Config
# ------------------------------------------------------------
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True,
)

# ------------------------------------------------------------
# Load Model (CRITICAL: device_map)
# ------------------------------------------------------------
print("🤖 Loading model...")
model = AutoModelForCausalLM.from_pretrained(
    MODEL_PATH,
    quantization_config=bnb_config,
    device_map={"": 0},
    trust_remote_code=True,
    use_cache=False,
    low_cpu_mem_usage=True,
)

# ------------------------------------------------------------
# Prepare for k-bit training
# ------------------------------------------------------------
model = prepare_model_for_kbit_training(model)
model.config.use_cache = False

# ------------------------------------------------------------
# LoRA
# ------------------------------------------------------------
lora_config = LoraConfig(
    task_type=TaskType.CAUSAL_LM,
    r=16,
    lora_alpha=32,
    lora_dropout=0.05,
    target_modules=["q_proj", "v_proj"],
    bias="none",
)

model = get_peft_model(model, lora_config)
model.print_trainable_parameters()

# 🚀 LoRA weights BF16 (faster, minimal VRAM increase)
for p in model.parameters():
    if p.requires_grad:
        p.data = p.data.bfloat16()

# Gradient checkpointing (KEEP for VRAM safety)
model.gradient_checkpointing_enable(
    gradient_checkpointing_kwargs={"use_reentrant": False}
)

# ------------------------------------------------------------
# Data Collator
# ------------------------------------------------------------
data_collator = DataCollatorForLanguageModeling(
    tokenizer=tokenizer,
    mlm=False,
)

# ------------------------------------------------------------
# Memory Monitor
# ------------------------------------------------------------
class MemoryMonitorCallback(TrainerCallback):
    def on_step_end(self, args, state, control, **kwargs):
        if state.global_step % 50 == 0:
            gpu = torch.cuda.memory_allocated() / 1e9
            res = torch.cuda.memory_reserved() / 1e9
            ram = psutil.virtual_memory().percent
            print(f"[Step {state.global_step}] GPU {gpu:.2f}/{res:.2f} GB | RAM {ram}%")

# ------------------------------------------------------------
# Performance Callback (zero overhead)
# ------------------------------------------------------------
class PerfCallback(TrainerCallback):
    def __init__(self, eff_bs):
        self.eff_bs = eff_bs
        self.last_step = 0
        self.last_time = None

    def on_train_begin(self, args, state, control, **kwargs):
        self.last_time = time.time()
        self.last_step = 0

    def on_log(self, args, state, control, logs=None, **kwargs):
        if not logs or "loss" not in logs:
            return
        now = time.time()
        ds = state.global_step - self.last_step
        dt = now - self.last_time
        if ds > 0 and dt > 0:
            sps = ds / dt
            print(
                f"⚡ step {state.global_step:>5} | "
                f"loss {logs['loss']:.4f} | "
                f"{sps:.4f} steps/s | "
                f"{sps * self.eff_bs:.3f} samples/s"
            )
        self.last_step = state.global_step
        self.last_time = now

# ------------------------------------------------------------
# Training Arguments
# ------------------------------------------------------------
training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,

    per_device_train_batch_size=BATCH_SIZE,
    gradient_accumulation_steps=GRAD_ACC,

    num_train_epochs=3,
    learning_rate=2e-4,
    weight_decay=0.01,
    warmup_ratio=0.05,
    lr_scheduler_type="cosine",

    optim="paged_adamw_8bit",

    fp16=False,
    bf16=False,
    max_grad_norm=0.3,

    logging_strategy="steps",
    logging_steps=10,

    save_strategy="steps",
    save_steps=500,
    save_total_limit=2,

    eval_strategy="steps",
    eval_steps=500,

    remove_unused_columns=True,
    dataloader_num_workers=0,
    dataloader_pin_memory=False,

    ddp_find_unused_parameters=False,
    report_to="none",
    seed=42,
)

# ------------------------------------------------------------
# Trainer
# ------------------------------------------------------------
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=dataset["train"],
    eval_dataset=dataset["validation"],
    data_collator=data_collator,
    callbacks=[
        MemoryMonitorCallback(),
        PerfCallback(BATCH_SIZE * GRAD_ACC),
    ],
)

# ------------------------------------------------------------
# Safety run
# ------------------------------------------------------------
print("🧪 SAFETY CHECK (2 steps)...")
trainer.args.max_steps = 2
trainer.train()
trainer.args.max_steps = -1

# ------------------------------------------------------------
# Full Training
# ------------------------------------------------------------
print("🚀 Starting full training...")
trainer.train()

# ------------------------------------------------------------
# Save + Merge
# ------------------------------------------------------------
trainer.save_model(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)

print("🔧 Merging LoRA...")
merged_model = model.merge_and_unload()
merged_model.save_pretrained(f"{OUTPUT_DIR}_merged")
tokenizer.save_pretrained(f"{OUTPUT_DIR}_merged")

print("✅ Training finished")
