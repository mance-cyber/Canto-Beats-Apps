# AI翻译安装和使用指南

## 当前状态
正在安装依赖包，包括 torch 2.6+ 和 transformers...

## 安装完成后的测试步骤

### 1. 测试AI翻译
```bash
python test_translation.py
```

这将测试：
- MarianMT模型加载
- 英译中功能
- 7个测试用例

### 2. 在应用中启用AI翻译

AI翻译会在以下情况自动使用：
- 英文短语（2+单词）
- 词典中没有的词汇
- 翻译模式设为"翻譯"

### 3. 第一次使用注意

首次运行时，系统会下载翻译模型（约300MB）：
- 模型：Helsinki-NLP/opus-mt-en-zh
- 位置：~/.cache/huggingface/

下载完成后，后续使用会很快。

## 翻译策略（优先级）

1. **检查完整短语** - "day one" → "第一天"
2. **逐词翻译** - "set" + "up" → "設立"  
3. **AI翻译** - 未知短语用AI
4. **保留原文** - 所有方法都失败

## 性能提示

- GPU加速：自动使用CUDA（如果可用）
- 首次翻译：需加载模型（约5-10秒）
- 后续翻译：即时响应
- 批量翻译：会缓存结果

## 故障排除

如果安装失败，请检查：
```bash
python -c "import torch; print(torch.__version__)"
pip list | findstr transformers
```

需要的最小版本：
- torch >= 2.6.0
- transformers >= 4.35.0
