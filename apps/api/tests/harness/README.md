# API Harness（L1 契约测试）

Agent / LLM 功能的**确定性回归**放此目录；与 `tests/unit/` 区分。

## 运行

```bash
cd apps/api
conda activate memoryos-api   # 或 source .venv/bin/activate
pip install pytest pytest-asyncio httpx   # EP00 可写入 requirements-dev.txt
pytest tests/harness -q
```

## 分层（见 docs/tech/ai-collab-stack.md）

| 层 | 目录约定 |
|:---|:---------|
| L1 | `test_*_contract.py` — HTTP 状态、JSON 字段 |
| L2 | `cases/*.yaml` + 评测脚本（EP02+） |
| L3 | 多轮统计报告（EP05+） |
