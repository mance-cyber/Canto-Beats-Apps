import json

# Read existing mapping
with open('src/resources/english_mapping.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

# Add business terms
new_terms = {
    "compliance": "合規",
    "compliant": "合規的",
    "day 1": "第一天",
    "day one": "第一天",
    "onboarding": "入職流程",
    "workflow": "工作流程",
    "pipeline": "流程",
    "funnel": "漏斗",
    "lead": "潛在客戶",
    "leads": "潛在客戶",
    "follow up": "跟進",
    "follow-up": "跟進",
    "that's why": "這就是為什麼",
    "because": "因為",
    "however": "然而",
    "therefore": "因此",
    "actually": "其實",
    "basically": "基本上",
    "literally": "真的",
    "honestly": "老實講"
}

d.update(new_terms)

# Write back
with open('src/resources/english_mapping.json', 'w', encoding='utf-8') as f:
    json.dump(d, f, ensure_ascii=False, indent=4)

print(f"Added {len(new_terms)} business terms to english_mapping.json")
