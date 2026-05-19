import torch
from transformers import pipeline
import time

print("Testing Qwen2.5-1.5B-Instruct...")
start_time = time.time()
try:
    pipe = pipeline(
        "text-generation",
        model="Qwen/Qwen2.5-1.5B-Instruct",
        device_map="auto" if torch.cuda.is_available() else None,
        device=-1 if not torch.cuda.is_available() else None,
        model_kwargs={"torch_dtype": torch.float32, "low_cpu_mem_usage": True}
    )
    print(f"Model loaded in {time.time() - start_time:.2f}s")
    
    prompt = "Explain quantum physics in 2 sentences."
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": prompt}
    ]
    
    # Qwen2.5 uses different chat template, but pipeline handles it usually
    res = pipe(prompt, max_new_tokens=50)
    print(f"Result: {res[0]['generated_text']}")
except Exception as e:
    print(f"Error: {e}")
