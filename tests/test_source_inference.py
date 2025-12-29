import sys
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

print("Loading model...")
model_id = "Qwen/Qwen2.5-3B-Instruct"

tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    device_map="auto",
    torch_dtype=torch.float16,
    trust_remote_code=True
)

print("Model loaded. Testing inference...")

test_prompt = """將以下粵語口語轉成書面語：
1. 有人投訴都搵你
2. 鼎爺私房菜

只輸出結果，保持編號："""

messages = [{"role": "user", "content": test_prompt}]
text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
inputs = tokenizer([text], return_tensors="pt").to("cuda")

with torch.no_grad():
    outputs = model.generate(**inputs, max_new_tokens=128, temperature=0.3, do_sample=True)

response = tokenizer.decode(outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
print("Response:")
print(response)
