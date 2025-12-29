import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

print("=== Testing SOURCE with style_processor EXACT prompt ===")
model_id = "Qwen/Qwen2.5-3B-Instruct"
tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(model_id, device_map="auto", torch_dtype=torch.float16, trust_remote_code=True)

combined = """1. 你成日話你做生意,你係老闆
2. 有人投訴都搵你
3. 好多香港老闆做咗幾十年"""

prompt = f"""【任務】粵語口語  書面語

【規則】
1. 所有粵語詞彙必須轉換成對應書面語
2. 保持原意，不可增刪
3. 繁體輸出，標點優化

【風格】繁體中文書面語，清晰自然。嚴格度：最高，凡是口語化表達一律改成書面語。

【輸入】
{combined}

【輸出】（只輸出結果，保持編號）"""

messages = [{"role": "user", "content": prompt}]
text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
inputs = tokenizer([text], return_tensors="pt").to("cuda")

with torch.no_grad():
    outputs = model.generate(**inputs, max_new_tokens=1024, temperature=0.1, do_sample=True)

response = tokenizer.decode(outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
print("=== Raw AI Response ===")
print(response)
print("=== End ===")
