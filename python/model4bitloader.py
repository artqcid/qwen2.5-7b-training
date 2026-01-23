import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

model_path = "/mnt/d/AI-Models/training/Qwen2.5-Coder-7b/Original/Qwen2.5-Coder-7B"

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,
)

tokenizer = AutoTokenizer.from_pretrained(
    model_path,
    trust_remote_code=True
)

model = AutoModelForCausalLM.from_pretrained(
    model_path,
    quantization_config=bnb_config,
    device_map={"": "cuda"},
    torch_dtype=torch.float16,
    trust_remote_code=True
)
print("Qwen2.5-Coder-7B loaded in 4-bit on GPU")
