# Design Template

## Problem

Xây dựng một research assistant có thể nhận câu hỏi kỹ thuật, thu thập thông tin, phân tích và viết câu trả lời cuối cùng.
Yêu cầu so sánh rõ cách làm single-agent với multi-agent để xem multi-agent có lợi ở đâu, tốn gì, và fail ở đâu.

## Why multi-agent?

Single-agent có thể làm được bài toán đơn giản, nhưng khi cần tách vai trò, trace theo từng bước, và xử lý fallback rõ ràng thì multi-agent dễ kiểm soát hơn.

Trong project này:
- `Supervisor` quyết định route.
- `Researcher` thu thập nguồn và research notes.
- `Analyst` rút ý chính và đánh giá khoảng trống.
- `Writer` tổng hợp thành final answer.

## Agent roles

| Agent | Responsibility | Input | Output | Failure mode |
|---|---|---|---|---|
| Supervisor | Chọn agent tiếp theo, dừng đúng lúc | `ResearchState` | `route_history`, `iteration`, trace route | Route sai, lặp vô hạn nếu thiếu stop condition |
| Researcher | Tìm nguồn và tạo research notes | Query + nguồn tìm kiếm | `sources`, `research_notes` | Không có nguồn, search provider fail, LLM fail |
| Analyst | Chuyển notes thành phân tích có cấu trúc | `research_notes`, `sources` | `analysis_notes` | Thiếu research notes, synthesis yếu |
| Writer | Viết final answer | `research_notes`, `analysis_notes`, `sources` | `final_answer` | Thiếu context, answer quá chung chung |
| Critic | Hook mở rộng cho review/chấm chất lượng | `final_answer` | Feedback/score | Không bắt buộc trong luồng chính |

## Shared state

Shared state chính là `ResearchState`:

- `request`: query, audience, max_sources
- `iteration`: số vòng đã chạy
- `route_history`: lịch sử route của supervisor
- `sources`: danh sách nguồn đã thu thập
- `research_notes`: output của researcher
- `analysis_notes`: output của analyst
- `final_answer`: output cuối của writer
- `agent_results`: kết quả từng agent để benchmark/debug
- `trace`: trace events có cấu trúc
- `errors`: danh sách lỗi hoặc fallback reasons

Lý do:
- Các agent sau cần dữ liệu của agent trước.
- Benchmark cần source count, error count, trace events.
- Trace/log cần biết đã fallback ở đâu.

## Routing policy

Workflow dùng LangGraph `StateGraph`:

```text
START -> Supervisor -> Researcher -> Supervisor -> Analyst -> Supervisor -> Writer -> Supervisor -> END
```

Quy tắc route:
- nếu đã có `final_answer` thì `done`
- nếu chạm `max_iterations` thì `done`
- nếu chưa có `research_notes` thì `researcher`
- nếu chưa có `analysis_notes` thì `analyst`
- còn lại thì `writer`

Validation:
- `researcher` phải sinh `research_notes`
- `analyst` phải sinh `analysis_notes`
- `writer` phải sinh `final_answer`
- nếu fail thì workflow tạo fallback an toàn và ghi trace/error

## Guardrails

- Max iterations: 6
- Timeout: dùng timeout của provider/HTTP client
- Retry: `LLMClient` retry theo exponential backoff
- Fallback: deterministic fallback cho từng agent và workflow
- Validation: kiểm tra output sau mỗi stage

Query nhạy cảm được chặn sớm bởi guardrail trước khi vào workflow.
Nhóm nhạy cảm gồm:
- chính trị/persuasion
- bạo lực
- hoạt động bất hợp pháp
- dữ liệu cá nhân
- y tế/pháp lý/tài chính rủi ro cao

## Benchmark plan

Mục tiêu benchmark:
- so sánh latency
- so sánh cost
- so sánh quality signal
- so sánh trace completeness

Format mỗi case:
- `baseline`
- `multi-agent`
- `benchmark`

Ví dụ case:
- `graphrag_200_words`
- `rag_vs_graphrag`
- `orchestration`
- `failure_modes`
- `guardrail_politics`
- `trace_showcase`

Lệnh benchmark:

```bash
python -m multi_agent_research_lab.cli benchmark \
  --case-id graphrag_200_words \
  --query "Explain GraphRAG in 200 words" \
  --output benchmark_report.md
```

## Failure mode and fix

Failure mode chính:
- LLM provider không truy cập được
- search provider không có kết quả
- agent không sinh ra output tối thiểu
- query nhạy cảm cần bị chặn

Fix:
- dùng fallback deterministic cho từng agent
- validation sau từng stage
- guardrail trước workflow
- trace/log đầy đủ để biết stage nào fail

## Implementation notes

- `LLMClient` là abstraction cho provider LLM.
- `SearchClient` ưu tiên nguồn thật và re-rank kết quả.
- `workflow.py` dùng LangGraph để điều phối node.
- `observability/logging.py` ghi log ra console và file.
- `observability/tracing.py` ghi trace span có cấu trúc.
- `evaluation/report.py` render benchmark report theo `case_id`.
