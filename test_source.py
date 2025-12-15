import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

print("Loading model for Source test...")
model_id = "Qwen/Qwen2.5-3B-Instruct"
tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(model_id, device_map="auto", torch_dtype=torch.float16, trust_remote_code=True)

prompt = """將以下粵語口語句子轉換為標準書面語。保持原意，只改變口語表達方式。

1. 有人投訴都搵你
2. 鼎爺私房菜嘅創辦人
3. 你覺得呢啲叫做辛苦來路

只輸出結果，保持編號格式："""

messages = [{"role": "user", "content": prompt}]
text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
inputs = tokenizer([text], return_tensors="pt").to("cuda")

with torch.no_grad():
    outputs = model.generate(**inputs, max_new_tokens=512, temperature=0.3, do_sample=True)

response = tokenizer.decode(outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
print("=== Source Result ===")
print(response)
