# PostgreSQL + SQLAlchemy 全栈实战总结（RAG后端专属）

## 一、事务与并发控制：数据库的立身之本

### 核心原理

PostgreSQL基于**MVCC（多版本并发控制）**实现读写不互斥，读不加锁，写只锁行。每个事务看到的是数据的一个快照，而非实时数据，这是它比MySQL更适合高并发场景的核心原因。

### 隔离级别选择

| 隔离级别                    | 问题               | 适用场景             |
| --------------------------- | ------------------ | -------------------- |
| READ UNCOMMITTED            | 脏读               | 无                   |
| **READ COMMITTED（默认）**  | 不可重复读         | 简单查询场景         |
| **REPEATABLE READ（推荐）** | 幻读（几乎无感知） | 所有写操作场景       |
| SERIALIZABLE                | 无                 | 金融级严格一致性场景 |

**核心结论**：全局升级为`REPEATABLE READ`，性能几乎无损失，且彻底解决不可重复读问题。不要使用SERIALIZABLE，并发高时会大量报错。

### 并发更新机制

- **规则**：先提交的事务获胜，后冲突的事务直接报错回滚，绝对不会出现数据覆盖
- **底层**：每行数据有隐藏的`xmax`字段，记录最后修改的事务ID，更新时会检查版本
- **解决方案**：
  1. **优先使用`SELECT FOR UPDATE`加行锁**：强制排队执行，结果完全可控
  2. **捕获异常自动重试**：适用于冲突概率低的场景

### 避坑点

1. ❌ 不要使用长事务：会导致死元组无法清理，占用大量磁盘空间
2. ❌ 不要忘记回滚：异常时必须调用`db.rollback()`，否则会话会一直持有事务
3. ❌ 不要在事务中执行耗时操作：如网络请求、文件读写等
4. ❌ 不要依赖默认隔离级别：默认的READ COMMITTED会导致同一个请求内两次查询结果不一致

## 二、表结构设计：从源头避免问题

### 主键设计

- **强制使用**：`BIGINT GENERATED ALWAYS AS IDENTITY`
- **为什么不用SERIAL**：有安全漏洞，允许用户手动修改自增序列
- **为什么不用UUID**：插入性能差10倍以上，外键占用更多磁盘和内存
- **例外**：分布式系统多库多表或需要客户端生成ID时才考虑UUID

### 核心字段设计

- **外键**：必须加`ON DELETE CASCADE`，自动清理孤儿数据
- **时间戳**：统一使用`TIMESTAMPTZ`（带时区），不要用`TIMESTAMP`
- **枚举**：使用PostgreSQL原生枚举类型代替CHECK约束
  ```sql
  CREATE TYPE message_role AS ENUM ('user', 'assistant', 'system');
  ALTER TYPE message_role ADD VALUE 'tool'; -- 扩展无需修改表结构
  ```
- **命名规范**：表名小写+下划线复数形式，列名小写+下划线，避免保留字

### 避坑点

1. ❌ 不要允许不必要的NULL：非空列必须加`NOT NULL`
2. ❌ 不要用TEXT类型存储短字符串：用VARCHAR(n)更节省空间
3. ❌ 不要在数据库层做复杂业务逻辑：如计算、格式化等，应该放在应用层
4. ❌ 不要忘记加CHECK约束：在数据库层强制数据合法性，比应用层更可靠

## 三、索引：性能的核心

### 三种核心索引类型

1. **B树索引（默认）**
   - 原理：平衡多路搜索树，所有数据在叶子节点，叶子节点用双向链表连接
   - 适用：等值查询、范围查询、排序、前缀匹配
   - 占比：90%的场景使用

2. **GIN索引（倒排索引）**
   - 原理：将"文档→关键词"反转成"关键词→文档"
   - 适用：数组查询、JSONB查询、全文搜索
   - RAG用途：文档标签、元数据过滤

3. **GiST索引（通用搜索树）**
   - 原理：将相似数据放在同一个树节点
   - 适用：向量数据、地理数据、范围类型
   - RAG用途：pgvector向量相似度搜索的核心

### 组合索引黄金法则

- **最左前缀原则**：索引`(a,b,c)`可以命中`a`、`a,b`、`a,b,c`查询
- **等值在前，范围在后**：正确`(conversation_id, created_at)`，错误`(created_at, conversation_id)`
- **覆盖索引**：使用`INCLUDE`子句包含查询需要的列，避免回表
  ```sql
  CREATE INDEX idx_conversations_user_id_cover ON conversations(user_id) INCLUDE (title, created_at);
  ```

### 索引维护

- **更新机制**：索引实时更新，每次增删改都会更新所有相关索引
- **重建索引**：每3-6个月用`REINDEX INDEX CONCURRENTLY`重建，提升2-10倍查询速度
- **监控使用率**：定期查询未使用的索引并删除
  ```sql
  SELECT indexrelname FROM pg_stat_user_indexes WHERE idx_scan = 0;
  ```

### 避坑点

1. ❌ 不要给低基数列建索引：如性别、状态只有几个值，全表扫描更快
2. ❌ 不要建太多索引：每个索引都会增加写入开销
3. ❌ 不要在索引列上做运算：会导致索引失效
   ```sql
   -- 错误
   SELECT * FROM messages WHERE DATE(created_at) = '2024-01-01';
   -- 正确
   SELECT * FROM messages WHERE created_at >= '2024-01-01' AND created_at < '2024-01-02';
   ```
4. ❌ 不要忘记更新统计信息：统计信息过时会导致查询规划器选错索引
   ```sql
   ANALYZE messages;
   ```

## 四、SQLAlchemy ORM：高效开发与避坑

### 核心概念

- **Engine**：数据库连接池入口，全局单例
- **Session**：数据库会话，每个请求一个，自带事务机制
- **Model**：数据库表的Python类映射
- **Relationship**：Python层面的关联关系，不是数据库字段

### 事务管理

- **同一个Session = 同一个事务**：修改任意多个表都自动在一个事务里
- **原子性保证**：要么全部成功提交，要么全部失败回滚
- **标准模板**：
  ```python
  try:
      # 所有增删改操作
      db.commit()
  except SQLAlchemyError as e:
      db.rollback()
      raise
  ```

### 懒加载与N+1查询

- **问题**：`relationship`默认是懒加载，访问时才执行SQL，循环访问会产生N+1查询
- **解决方案**：使用`joinedload`或`selectinload`预加载

  ```python
  # 错误：N+1查询
  conversations = db.query(Conversation).all()
  for conv in conversations:
      print(conv.messages)

  # 正确：一次查询获取所有数据
  from sqlalchemy.orm import joinedload
  conversations = db.query(Conversation).options(joinedload(Conversation.messages)).all()
  ```

### 避坑点

1. ❌ 不要在循环里访问关联属性：一定会产生N+1查询
2. ❌ 不要用全局Session：会导致线程安全问题
3. ❌ 不要忘记关闭Session：请求结束后必须关闭
4. ❌ 不要在生产环境开启`echo=True`：会打印所有SQL，严重影响性能
5. ❌ 不要用`autocommit=True`：会失去事务的原子性保证

## 五、pgvector：RAG系统的向量数据库首选

### 核心结论

**对于90%的中小型RAG系统，pgvector完全可以代替专门的向量数据库**。只有当向量数量超过1000万时，才需要考虑迁移到Pinecone/Weaviate等专门的向量数据库。

### 优势

- ACID严格合规，数据一致性有保障
- 与SQL无缝集成，支持复杂的元数据过滤
- 部署维护成本极低，不需要额外的服务
- 性能足够：百万级向量毫秒级查询

### 距离度量选择

| 操作符 | 距离类型 | 适用场景             |
| ------ | -------- | -------------------- |
| `<->`  | L2距离   | 未归一化向量         |
| `<#>`  | 内积距离 | 归一化向量，速度最快 |
| `<=>`  | 余弦距离 | 未归一化向量         |

**最佳实践**：所有向量先归一化，然后使用`<#>`内积距离，速度比余弦距离快2-3倍。

### 避坑点

1. ❌ 不要用未归一化的向量：会导致相似度计算结果不准确
2. ❌ 不要在大表上用全表扫描做向量搜索：一定要建GiST索引
   ```sql
   CREATE INDEX idx_chunks_embedding ON chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
   ```
3. ❌ 不要一开始就上专门的向量数据库：会大大增加系统复杂度和维护成本
4. ❌ 不要用太高的向量维度：维度越高，查询速度越慢，OpenAI ada-002的1536维是最佳平衡

## 六、最终总结

今天我们讨论的所有知识点，都是围绕**如何构建一个高性能、高可靠、易维护的RAG后端**展开的。核心要点可以概括为：

1. **事务**：用REPEATABLE READ隔离级别，加行锁解决并发冲突
2. **表结构**：用自增主键、外键级联、原生枚举、带时区时间戳
3. **索引**：B树为主，GIN和GiST为辅，遵循最左前缀原则，定期重建
4. **ORM**：用同一个Session管理事务，预加载关联数据避免N+1查询
5. **向量搜索**：优先用pgvector，归一化向量后用内积距离

这些都是生产环境中经过验证的最佳实践，按照这些原则设计和开发，你可以避免90%以上的PostgreSQL和SQLAlchemy相关的问题。
