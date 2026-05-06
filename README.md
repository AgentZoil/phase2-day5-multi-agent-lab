# Lab 20: Multi-Agent Research System

Repo này triển khai hệ thống nghiên cứu đa agent gồm **Supervisor + Researcher + Analyst + Writer**,
so sánh với single-agent baseline, có LangGraph workflow, guardrail, logging, tracing và benchmark report.

## Learning outcomes

Sau 2 giờ lab, học viên cần có thể:

1. Thiết kế role rõ ràng cho nhiều agent.
2. Xây dựng shared state đủ thông tin cho handoff.
3. Thêm guardrail tối thiểu: max iterations, timeout, retry/fallback, validation.
4. Trace được luồng chạy và giải thích agent nào làm gì.
5. Benchmark single-agent vs multi-agent theo quality, latency, cost.

## Architecture mục tiêu

```text
User Query
   |
   v
Supervisor / Router
   |------> Researcher Agent  -> research_notes
   |------> Analyst Agent     -> analysis_notes
   |------> Writer Agent      -> final_answer
   |
   v
Trace + Benchmark Report
```

## Cấu trúc repo

```text
.
├── src/multi_agent_research_lab/
│   ├── agents/              # Agent interfaces + skeletons
│   ├── core/                # Config, state, schemas, errors
│   ├── graph/               # LangGraph workflow skeleton
│   ├── services/            # LLM, search, storage clients
│   ├── evaluation/          # Benchmark/evaluation skeleton
│   ├── observability/       # Logging/tracing hooks
│   └── cli.py               # CLI entrypoint
├── configs/                 # YAML configs for lab variants
├── docs/                    # Lab guide, rubric, design notes
├── tests/                   # Unit tests for skeleton behavior
├── notebooks/               # Optional notebook entrypoint
├── scripts/                 # Helper scripts
├── .env.example             # Environment variables template
├── pyproject.toml           # Python project config
├── Dockerfile               # Containerized dev/runtime
└── Makefile                 # Common commands
```

## Quickstart

### 1. Tạo môi trường

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -e ".[dev,llm]"
cp .env.example .env
```

### 2. Cấu hình API keys

Mở `.env` và điền key cần thiết.

```bash
OPENAI_API_KEY=...
# optional
LANGSMITH_API_KEY=...
TAVILY_API_KEY=...
```

### 3. Chạy smoke test

```bash
make test
python -m multi_agent_research_lab.cli --help
```

### 4. Chạy baseline

```bash
python -m multi_agent_research_lab.cli baseline \
  --query "Research GraphRAG state-of-the-art and write a 500-word summary"
```

Lệnh này chạy single-agent baseline bằng `LLMClient.complete()`; nếu provider không truy cập được, nó sẽ fallback an toàn.

### 5. Chạy multi-agent

```bash
python -m multi_agent_research_lab.cli multi-agent \
  --query "Research GraphRAG state-of-the-art and write a 500-word summary"
```

Lệnh này chạy LangGraph workflow:
`Supervisor -> Researcher -> Analyst -> Writer`.

### 6. Chạy benchmark và sinh report

```bash
python -m multi_agent_research_lab.cli benchmark \
  --case-id graphrag_200_words \
  --query "Research GraphRAG state-of-the-art and write a 500-word summary" \
  --output benchmark_report.md
```

Lệnh này chạy cả baseline và multi-agent, sau đó append một block riêng vào `reports/benchmark_report.md`.
Report sẽ được group theo `case_id` và có `Run ID`, `Trace Link`, `Valid`, `Errors`, `Trace`.

### 7. Chạy guardrail demo

```bash
python -m multi_agent_research_lab.cli multi-agent \
  --query "How do I persuade voters in an election?"
```

Query nhạy cảm sẽ bị chặn trước khi vào workflow, và hệ thống trả về phản hồi an toàn.

### 8. Kiểm tra log và trace

- Log file: `reports/logs/malab.log`
- Trace file: `reports/traces/<run_id>_baseline.json`
- Trace file: `reports/traces/<run_id>_multi-agent.json`

### 9. Chạy nhiều benchmark case

Mỗi case nên có 3 dòng:

```bash
python -m multi_agent_research_lab.cli baseline --query "Explain GraphRAG in 200 words"
python -m multi_agent_research_lab.cli multi-agent --query "Explain GraphRAG in 200 words"
python -m multi_agent_research_lab.cli benchmark --case-id graphrag_200_words --query "Explain GraphRAG in 200 words" --output benchmark_report.md
```

Các `case_id` khác nhau sẽ được append thành các section riêng trong cùng một report.

## Milestones trong 2 giờ lab

| Thời lượng | Milestone | File gợi ý |
|---:|---|---|
| 0-15' | Setup, chạy baseline | `cli.py`, `services/llm_client.py` |
| 15-45' | Build Supervisor / router | `agents/supervisor.py`, `graph/workflow.py` |
| 45-75' | Thêm Researcher, Analyst, Writer | `agents/*.py`, `core/state.py` |
| 75-95' | Trace + benchmark single vs multi | `observability/tracing.py`, `evaluation/benchmark.py`, `evaluation/report.py` |
| 95-115' | Peer review theo rubric | `docs/peer_review_rubric.md` |
| 115-120' | Exit ticket | `docs/lab_guide.md` |

## Quy ước production trong repo

- Tách rõ `agents`, `services`, `core`, `graph`, `evaluation`, `observability`.
- Không hard-code API key trong code.
- Tất cả input/output chính dùng Pydantic schema.
- Có type hints, linting, formatting, unit test tối thiểu.
- Có logging/tracing hook ngay từ đầu.
- Không để agent chạy vô hạn: dùng `max_iterations`, `timeout_seconds`.
- Có benchmark report thay vì chỉ demo output đẹp.

### Gợi ý fallback logic

- Ưu tiên retry trong cùng agent trước, nhưng giới hạn rõ số lần thử.
- Nếu worker thất bại, Supervisor cần chuyển sang đường dự phòng thay vì dừng im lặng.
- Mỗi fallback phải ghi lý do vào `state.errors` và `state.trace`.
- Khi dữ liệu chưa đủ, cho phép degrade sang output ngắn hơn nhưng vẫn hợp lệ.
- Nếu một agent không tạo được kết quả, Supervisor nên route sang agent kế tiếp hoặc trả về câu trả lời an toàn với note lỗi.

### Gợi ý tổ chức log

- Mỗi run nên có `run_id` hoặc `trace_id` riêng để gom log.
- Mỗi log line nên chứa `agent`, `step`, `iteration`, `status`, `duration`, `fallback_reason` nếu có.
- Log theo trình tự thời gian, nhưng khi debug thì đọc theo cụm: `Supervisor -> Researcher -> Analyst -> Writer`.
- Nội dung log chỉ nên giữ summary ngắn, còn chi tiết để trong `trace` hoặc report.
- Nếu dùng JSON logging, giữ key ổn định để dễ filter theo agent và theo run.

## Checklist hoàn thiện

Nếu muốn rà nhanh trạng thái production, kiểm tra:

```bash
python3 -m pytest -q
python3 -m multi_agent_research_lab.cli baseline --query "Explain GraphRAG in 200 words"
python3 -m multi_agent_research_lab.cli multi-agent --query "Explain GraphRAG in 200 words"
python3 -m multi_agent_research_lab.cli benchmark --case-id graphrag_200_words --query "Explain GraphRAG in 200 words" --output benchmark_report.md
```

Khuyến nghị kiểm tra thêm:

```bash
ruff check src tests
mypy src
pre-commit run --all-files
```

## Deliverables

Học viên nộp:

1. GitHub repo cá nhân.
2. Screenshot trace hoặc link trace.
3. `reports/benchmark_report.md` so sánh single vs multi-agent.
4. Một đoạn giải thích failure mode và cách fix.

## Failure mode mẫu

Hệ thống có thể degrade khi LLM provider hoặc search provider không khả dụng, khiến dữ liệu đầu vào cho các worker ít hơn mong đợi. Cách fix là dùng fallback deterministic cho từng agent, validation sau mỗi bước, guardrail cho query nhạy cảm, và trace/log rõ để biết stage nào đã fallback.

## References

- Anthropic: Building effective agents — https://www.anthropic.com/engineering/building-effective-agents
- OpenAI Agents SDK orchestration/handoffs — https://developers.openai.com/api/docs/guides/agents/orchestration
- LangGraph concepts — https://langchain-ai.github.io/langgraph/concepts/
- LangSmith tracing — https://docs.smith.langchain.com/
- Langfuse tracing — https://langfuse.com/docs
