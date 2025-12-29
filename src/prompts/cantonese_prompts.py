"""
Cantonese processing prompts for Canto-beats V2.0.

Contains all prompt templates for LLM processing.
"""

# =============================================================================
# 基礎校對 Prompt (用於入門/CPU模式)
# =============================================================================

BASIC_CORRECTION_PROMPT = """# Role:
你是一個精通香港粵語的專業字幕編輯。

# Task:
你的任務是處理一段由語音識別（ASR）轉錄的原始文本。你需要執行以下兩個步驟：
1.  **全文校對**：修正文本中的所有錯別字、同音字錯誤（例如「C度」->「喺度」），並確保用詞符合香港粵語的口語習慣。
2.  **語義斷句與重組**：這段文本可能包含因為語速過快而被錯誤切分嘅片段，請根據語義將佢哋智能地合併或重新切分，成為多個獨立、通順的句子。

# Rules:
- **校對規則**:
    - 使用最地道的粵語口語詞彙（例如保留「搞掂」、「冇問題」、「勁」）。
    - 如有潮語的粵語口語詞彙可這樣翻譯(例如「甩底」等於「爽約」,「大癲」等於「非常誇張」,「好Kam」等於「十分尷尬」)
    - 確保標點符號使用正確，特別是句末的語氣詞（如「呀、啦、喎、囉」）。
- **斷句規則**:
    - 每個句子都應該是一個完整的思想單元。
    - 即使原文沒有標點，也要根據語氣和停頓智能地切分。
- **輸出格式**:
    - 嚴格按照 Python List of Strings 的 JSON 格式輸出，例如 `["句子一。", "句子二。"]`。
    - **絕對不要**在最終輸出中包含任何 markdown 標記 (例如 ```json) 或任何解釋性文字。

# ASR 原始文本:
{text}
"""

# =============================================================================
# 口語轉書面語 Prompt (專門用於風格轉換)
# =============================================================================

COLLOQUIAL_TO_WRITTEN_PROMPT = """將以下粵語口語轉換成標準書面語。只輸出翻譯後的文字，不要添加任何前綴或解釋。

口語轉書面語對照：
係→是、喺→在、佢→他、嘅→的、唔→不、冇→沒有、咗→了、嚟→來、而家→現在、成日→經常、返到→回到、俾→給、話→說、諗→想、睇→看、搵→找

原文：{text}

書面語："""

# =============================================================================
# 複雜度判斷 Prompt (用於全功能模式預處理)
# =============================================================================

COMPLEXITY_JUDGE_PROMPT = """# Role:
你是一個文本分析專家。

# Task:
分析以下粵語文本的處理複雜度，判斷是否需要深度加工。

# 判斷標準:
- **simple**: 文本簡短、清晰，沒有俚語、潮語，無需書面語翻譯
- **complex**: 文本包含俚語、潮語、複雜表達，需要深度處理

# Rules:
- 只回答一個詞: "simple" 或 "complex"
- 不要有其他任何輸出

# 文本:
{text}
"""

# =============================================================================
# 簡化處理 Prompt (當判斷為simple時)
# =============================================================================

SIMPLE_PROCESS_PROMPT = """# Role:
你是一個精通香港粵語的字幕編輯。

# Task:
處理以下文本，執行以下操作：
1. 校對錯別字
2. 切分成短句
3. 盡力提供一個書面語版本（可以不完美）

# Rules:
- 輸出JSON格式
- 每個句子包含: "colloquial" (口語) 和 "formal" (書面語)

# 輸出格式:
[
  {{"colloquial": "口語句子", "formal": "書面語句子"}},
  ...
]

# 文本:
{text}
"""

# =============================================================================
# 終極加工 Prompt V3 (當判斷為complex時，或全功能模式)
# =============================================================================

FULL_PROCESS_PROMPT_V3 = """# Role:
你是一位精通香港語言文化的資深編輯，擅長在口語與書面語之間進行精準轉換。

# Context:
你正在處理一段來自粵語短影片的、人聲清晰的字幕文本。

# Task:
你的任務是將這段文本進行深度加工，並提供兩種風格的輸出。請執行以下操作：

1. **口語校對與風格化 (Colloquial Version):**
   - 精準校對所有錯別字
   - 保持並潤色文本，使其完全符合香港年輕人的口語風格，大膽使用網絡潮語
   - 將文本切分成適合快速閱讀的短句（每句不超過20個字）

2. **書面語翻譯 (Formal Translation):**
   - 在理解口語原意的基礎上，將其翻譯成通順、達意、無歧義的標準書面語
   - 此版本旨在讓不熟悉粵語口語或潮語的觀眾也能準確理解內容

# 潮語對照表（供參考）:
- 「甩底」= 爽約
- 「大癲」= 非常誇張
- 「好Kam」= 十分尷尬
- 「屈機」= 作弊或不公平
- 「Chur」= 辛苦、拼命
- 「收皮」= 閉嘴、住口
- 「佛系」= 隨緣、不強求
- 「躺平」= 放棄努力

# Rules:
- **格式要求**: 嚴格按照指定的JSON格式輸出，不要有任何偏差或額外解釋
- **專有名詞保護**: 文本中形如 `[PROTECTED_X]` 的標籤是專有名詞，必須原樣保留在兩種版本的對應位置
- **每句限制**: 口語和書面語每句都不要超過20個字

# 輸出格式 (JSON):
輸出一個物件列表，每個物件代表一個句子單元，包含以下兩個鍵:
- "colloquial_sentence": (String) 口語風格的最終短句
- "formal_sentence": (String) 對應的書面語翻譯

範例:
[
  {{"colloquial_sentence": "佢琴日甩咗我底呀！", "formal_sentence": "他昨天爽約了。"}},
  {{"colloquial_sentence": "真係好Kam呀...", "formal_sentence": "真的非常尷尬..."}}
]

# ASR 原始文本:
{text}
"""

# =============================================================================
# 專有名詞保護的預處理和後處理
# =============================================================================

def protect_proper_nouns(text: str, noun_list: list) -> tuple:
    """
    Replace proper nouns with protected tokens.
    
    Args:
        text: Original text
        noun_list: List of proper nouns to protect
        
    Returns:
        Tuple of (protected_text, mapping_dict)
    """
    mapping = {}
    protected_text = text
    
    for i, noun in enumerate(noun_list):
        token = f"[PROTECTED_{i}]"
        if noun in protected_text:
            protected_text = protected_text.replace(noun, token)
            mapping[token] = noun
    
    return protected_text, mapping


def restore_proper_nouns(text: str, mapping: dict) -> str:
    """
    Restore protected tokens back to proper nouns.
    
    Args:
        text: Text with protected tokens
        mapping: Token to noun mapping
        
    Returns:
        Text with restored proper nouns
    """
    restored = text
    for token, noun in mapping.items():
        restored = restored.replace(token, noun)
    return restored


# =============================================================================
# Prompt選擇器
# =============================================================================

def get_prompt_for_tier(tier: str, text: str, is_complex: bool = None) -> str:
    """
    Get the appropriate prompt based on performance tier and complexity.
    
    Args:
        tier: Performance tier ("ultimate", "mainstream", "entry", "cpu_only")
        text: Text to process
        is_complex: Optional complexity override
        
    Returns:
        Formatted prompt string
    """
    if tier in ("entry", "cpu_only"):
        # Basic mode - fast correction only
        return BASIC_CORRECTION_PROMPT.format(text=text)
    
    # Full feature mode (mainstream, ultimate)
    if is_complex is None:
        # Return complexity judge prompt first
        return COMPLEXITY_JUDGE_PROMPT.format(text=text)
    elif is_complex:
        return FULL_PROCESS_PROMPT_V3.format(text=text)
    else:
        return SIMPLE_PROCESS_PROMPT.format(text=text)
