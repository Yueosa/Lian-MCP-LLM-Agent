# Lfind - 向量检索工具库

> 轻量级、开箱即用的文本向量化与检索工具

## 简介

**Lfind** 是 `mylib.kit` 工具包中的核心组件之一，专注于提供简单易用的 Embedding 生成与向量检索功能。它封装了主流的 Embedding 模型接口（目前支持 OpenAI/DeepSeek 兼容接口），为上层的 RAG（检索增强生成）系统提供底层支持。

## 核心功能

1.  **文本向量化 (Embedding Generation)**
    *   支持将任意文本转换为高维向量。
    *   内置缓存机制（可选），减少重复计算。
    *   自动处理长文本截断。

2.  **向量计算**
    *   提供余弦相似度 (Cosine Similarity) 计算函数。
    *   支持向量归一化。

## 快速开始

### 1. 配置环境

在 `mylib/kit/Lfind/.env` 中配置 API Key（或复用全局 LLM 配置）：

```bash
OPENAI_API_KEY=sk-xxxxxx
OPENAI_BASE_URL=https://api.deepseek.com
```

### 2. 使用示例

```python
from mylib.kit.Lfind.embedding import get_embedding, cosine_similarity

# 1. 获取向量
text1 = "猫娘是一种可爱的生物"
text2 = "小恋是傲娇的白猫魔女"
vec1 = get_embedding(text1)
vec2 = get_embedding(text2)

# 2. 计算相似度
similarity = cosine_similarity(vec1, vec2)
print(f"相似度: {similarity:.4f}")
```

## 集成场景

Lfind 目前广泛应用于本系统的 **RAGAgent** 中：
1.  用户输入 -> `Lfind` -> Query Vector
2.  数据库记忆 -> `Lfind` -> Memory Vectors
3.  计算相似度 -> 检索 Top-K 相关记忆
