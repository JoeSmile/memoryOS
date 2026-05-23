### 2. 手写LangGraph最小原子（不使用LangGraph库）

```python
# 1. 手写状态（用字典模拟）
state = {
    "query": "",
    "context": "",
    "answer": "",
    "retrieval_count": 0,
    "max_retrieval_count": 2
}

# 2. 手写节点函数
def retrieve_node(state):
    """检索节点：从向量库中获取上下文"""
    context = search_vector_store(state["query"])
    state["context"] = "\n\n".join(context)
    state["retrieval_count"] += 1
    return state

def generate_node(state):
    """生成节点：基于上下文生成回答"""
    answer = generate_answer(state["query"], state["context"])
    state["answer"] = answer
    return state

def should_continue_node(state):
    """判断节点：是否需要继续检索"""
    if "我不知道" in state["answer"] and state["retrieval_count"] < state["max_retrieval_count"]:
        return "retrieve"
    else:
        return "end"

# 3. 手写图执行器
def run_graph(state):
    current_node = "retrieve"
    while current_node != "end":
        if current_node == "retrieve":
            state = retrieve_node(state)
            current_node = "generate"
        elif current_node == "generate":
            state = generate_node(state)
            current_node = should_continue_node(state)
    return state

# 测试手写的状态机RAG
if __name__ == "__main__":
    state["query"] = "什么是第一性原理？"
    final_state = run_graph(state)
    print(final_state["answer"])
```

**必须理解的问题**：

- 为什么需要一个全局的state字典？如果把所有数据都作为函数参数传递会有什么问题？
- 为什么判断节点要返回下一个节点的名称，而不是直接调用下一个节点？
- 如果没有max_retrieval_count限制会发生什么？
- 这个手写的状态机和LangGraph的核心区别是什么？

---

## 第三阶段：从零开始逐级拼装，推导组合逻辑

**每一步都只添加一个功能**，确保完全理解为什么要添加这个功能，以及它解决了什么问题。

### 一阶：线性RAG图（最基础的LangGraph RAG）

- 节点：检索 → 生成
- 边：检索 → 生成 → END
- 解决的问题：将RAG流程结构化，便于维护和扩展

### 二阶：带反思的RAG图（解决"检索不充分"问题）

- 节点：检索 → 生成 → 判断是否需要重检索
- 边：检索 → 生成 → 判断 → 检索/END
- 解决的问题：当第一次检索到的信息不足以回答问题时，自动进行二次检索

### 三阶：带工具调用的RAG图（解决"静态知识不足"问题）

- 节点：检索 → 生成 → 判断是否需要调用工具 → 工具调用 → 生成
- 边：检索 → 生成 → 判断 → 工具调用/END；工具调用 → 生成
- 解决的问题：当检索到的信息和LLM的内部知识都不足以回答问题时，调用外部工具获取实时信息

### 四阶：多文档路由RAG图（解决"多领域文档检索"问题）

- 节点：路由判断 → 文档A检索 → 文档B检索 → 生成
- 边：路由判断 → 文档A检索/文档B检索 → 生成 → END
- 解决的问题：根据问题的领域，自动选择对应的文档库进行检索，提高检索精度

### 五阶：带对话记忆的RAG图（解决"多轮对话"问题）

- 节点：记忆加载 → 检索 → 生成 → 记忆保存
- 边：记忆加载 → 检索 → 生成 → 记忆保存 → END
- 解决的问题：在多轮对话中，LLM可以记住之前的对话内容，回答更连贯

---

## 第四阶段：基于第一性原理进行创新和优化

当你完全理解了所有底层原子和组合逻辑后，就可以脱离所有"最佳实践"，根据自己的需求设计最优的RAG流程。

### 常见优化方向（基于底层原理推导）

1. **文本切块优化**：
   - 不是所有文档都适合固定大小切块
   - 可以根据文档的结构（标题、段落、列表）进行语义切块
   - 可以使用LLM对长文档进行摘要，生成"摘要向量"和"原文向量"两层索引

2. **检索优化**：
   - 不是Top-K越大越好，要在精度和速度之间做权衡
   - 可以使用重排序模型(Re-ranker)对第一次检索的结果进行二次排序
   - 可以使用查询重写(Query Rewriting)技术，将用户的问题转换为更适合检索的形式

3. **状态流转优化**：
   - 不是所有问题都需要经过相同的流程
   - 可以设计更复杂的条件判断，让简单的问题走更短的流程
   - 可以使用并行节点，同时执行多个检索或工具调用，提高速度

4. **幻觉抑制优化**：
   - 不是所有生成的回答都是可信的
   - 可以添加一个"事实核查节点"，让LLM自己检查回答是否基于上下文
   - 可以在回答中添加引用来源，让用户可以验证信息的真实性

---

## 学习路线图（按周规划）

- **第1周**：完成第二阶段，手写所有RAG和LangGraph的最小原子，不使用任何框架
- **第2周**：完成第三阶段的一阶和二阶，用LangGraph实现线性RAG和带反思的RAG
- **第3周**：完成第三阶段的三阶和四阶，实现带工具调用和多文档路由的RAG
- **第4周**：完成第三阶段的五阶，实现带对话记忆的RAG，并开始进行第四阶段的优化

**验证标准**：当你遇到任何一个RAG相关的问题时，能够立刻定位到是哪个原子出了问题，并且知道如何修改代码来解决它，而不是去Google搜索"如何解决RAG幻觉"然后复制粘贴别人的代码。
