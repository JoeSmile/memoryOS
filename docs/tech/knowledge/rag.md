# LangGraph+RAG 第一性原理深度学习指南

**核心原则**：不背API、不抄模板、不迷信"最佳实践"。先拆到**不可再分的物理原子**，理解每个原子的"存在意义"和"边界条件"，再从头推导所有组合逻辑。

---

## 第一阶段：彻底拆解到底层原子（根基层，必须100%吃透）

### 一、RAG 底层原子拆解（每个都要回答"为什么必须有它"）

| 原子名称   | 本质定义                                          | 存在的根本原因                                                                                                 | 没有它会发生什么                                       | 核心边界条件                                                        |
| ---------- | ------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------ | ------------------------------------------------------------------- |
| 文本切块   | 将长文本分割为固定/可变长度的语义片段             | 1. LLM上下文窗口有物理上限<br>2. 长文本注意力衰减，尾部信息几乎丢失<br>3. 向量检索的精度与片段语义完整性正相关 | 无法处理超过上下文窗口的文档；检索结果要么太泛要么太碎 | 切块大小必须匹配嵌入模型的最大输入长度和LLM的上下文窗口             |
| 文本嵌入   | 将自然语言文本映射为固定维度的数值向量            | 计算机无法直接理解语义，只能计算数值相似度                                                                     | 无法实现"语义检索"，只能做关键词匹配                   | 同一嵌入模型生成的向量才能比较相似度；向量维度决定语义表达能力      |
| 向量存储   | 高效存储和索引高维向量的数据库                    | 普通数据库无法在毫秒级完成百万级向量的最近邻搜索                                                               | 检索速度慢到无法使用                                   | 支持近似最近邻搜索(ANN)是核心能力，精确最近邻搜索(NN)只适合小数据集 |
| 相似度检索 | 计算查询向量与库中向量的距离，返回最相似的Top-K个 | 从海量文档中快速筛选出与问题相关的片段                                                                         | 只能返回随机文档，RAG完全失效                          | 余弦相似度是最常用的语义相似度度量方式                              |
| 上下文拼接 | 将检索到的多个片段按规则组合成提示词              | LLM只能处理连续的文本输入                                                                                      | 无法将检索到的信息传递给LLM                            | 拼接后的总长度不能超过LLM的上下文窗口                               |
| LLM生成    | 基于拼接后的上下文和用户问题生成回答              | 利用LLM的推理和语言生成能力，将检索到的信息整合成自然语言回答                                                  | RAG只能返回原始文档片段，无法直接回答问题              | 生成结果必须严格基于提供的上下文，不能编造信息                      |

### 二、LangGraph 底层原子拆解（LangGraph的灵魂是状态机，不是图）

| 原子名称                     | 本质定义                                             | 存在的根本原因                                                                    | 没有它会发生什么                                                         | 核心边界条件                                                         |
| ---------------------------- | ---------------------------------------------------- | --------------------------------------------------------------------------------- | ------------------------------------------------------------------------ | -------------------------------------------------------------------- |
| **State(状态)**              | 一个全局可读写的数据结构，存储整个流程的所有中间结果 | 传统LangChain链是**无状态**的，每个步骤只能接收前一个步骤的输出，无法访问全局信息 | 无法实现复杂的多轮决策、反思迭代、错误修正；流程一旦开始就无法中断和恢复 | 状态必须是可序列化的，才能支持持久化和分布式执行                     |
| **Node(节点)**               | 一个**纯函数**，接收当前状态，返回状态的更新         | 流程的最小执行单元，封装具体的业务逻辑                                            | 流程无法执行任何实际操作                                                 | 节点函数只能修改状态，不能有其他副作用；相同的输入必须产生相同的输出 |
| **Edge(边)**                 | 定义状态从一个节点流向另一个节点的规则               | 连接不同的节点，构成完整的流程                                                    | 节点之间无法关联，流程无法推进                                           | 边只能连接节点，不能直接连接其他边                                   |
| **条件边(Conditional Edge)** | 根据当前状态的某个值，动态决定下一个执行的节点       | 实现分支逻辑，让流程可以根据不同情况走不同的路径                                  | 只能执行线性流程，无法处理复杂的决策场景                                 | 条件判断函数必须返回一个节点名称或END                                |
| **循环(Loop)**               | 状态从一个节点流回之前的某个节点                     | 实现反思迭代、重试机制，让LLM可以不断修正自己的输出                               | 只能执行一次流程，无法处理需要多次尝试的任务                             | 必须设置最大循环次数，防止无限循环                                   |
| **图执行器(Graph Executor)** | 负责按照边的规则，依次执行节点，更新状态             | 管理整个流程的执行生命周期                                                        | 图只是一个静态的定义，无法运行                                           | 执行器必须处理节点执行失败、超时等异常情况                           |

---

## 第二阶段：剥离所有封装，逐个验证原子功能

**绝对禁止**一开始就用`langchain_community`、`langgraph`的高级封装。用最基础的Python代码手写每个原子，验证其功能。

### 1. 手写RAG最小原子（不使用任何LangChain组件）

```python
import openai
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# 1. 手写文本切块器
def chunk_text(text, chunk_size=500, chunk_overlap=50):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - chunk_overlap
    return chunks

# 2. 手写文本嵌入函数
def embed_text(text):
    response = openai.Embedding.create(
        input=text,
        model="text-embedding-ada-002"
    )
    return np.array(response['data'][0]['embedding'])

# 3. 手写向量存储（用Python列表模拟）
vector_store = []
def add_to_vector_store(chunks):
    for chunk in chunks:
        vector = embed_text(chunk)
        vector_store.append({"text": chunk, "vector": vector})

# 4. 手写相似度检索
def search_vector_store(query, top_k=3):
    query_vector = embed_text(query)
    similarities = []
    for item in vector_store:
        sim = cosine_similarity([query_vector], [item['vector']])[0][0]
        similarities.append((item['text'], sim))
    similarities.sort(key=lambda x: x[1], reverse=True)
    return [text for text, sim in similarities[:top_k]]

# 5. 手写上下文拼接和LLM生成
def generate_answer(query, context):
    prompt = f"""基于以下上下文回答问题：
上下文：{context}
问题：{query}
如果上下文中没有相关信息，请回答"我不知道"。"""
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response['choices'][0]['message']['content']

# 测试完整的基础RAG
if __name__ == "__main__":
    with open("document.txt", "r", encoding="utf-8") as f:
        text = f.read()
    chunks = chunk_text(text)
    add_to_vector_store(chunks)
    query = "什么是第一性原理？"
    context = "\n\n".join(search_vector_store(query))
    answer = generate_answer(query, context)
    print(answer)
```

**必须理解的问题**：

- 为什么切块要有重叠？如果没有重叠会发生什么？
- 为什么用余弦相似度而不是欧氏距离？
- 如果top_k设置得太大或太小会有什么问题？
- 为什么提示词里要加"如果上下文中没有相关信息，请回答我不知道"？
