# Checklist hoàn thành lab Multi-Agent Research System

Mục tiêu của checklist này là giúp bạn đi từ skeleton đến bài nộp hoàn chỉnh, có fallback rõ ràng, log gọn gàng, trace dễ đọc, và benchmark đủ thuyết phục.

## 1. Hiểu yêu cầu

- [ ] Đọc `README.md`, `docs/lab_guide.md`, `docs/peer_review_rubric.md`.
- [ ] Xác định rõ 4 vai trò chính: `Supervisor`, `Researcher`, `Analyst`, `Writer`.
- [ ] Ghi lại tiêu chí thành công: role rõ, state đủ, fallback có, trace có, benchmark có.

## 2. Chạy skeleton trước

- [ ] Cài môi trường theo README.
- [ ] Chạy `make test` để biết baseline test nào đang chờ.
- [ ] Chạy `python -m multi_agent_research_lab.cli --help`.
- [ ] Chạy `baseline` để xác nhận CLI hoạt động.
- [ ] Chạy `multi-agent` để xem phần `TODO(student)` đang nằm ở đâu.

## 3. Hoàn thiện state và schema

- [ ] Rà `src/multi_agent_research_lab/core/schemas.py` để hiểu dữ liệu vào/ra.
- [ ] Rà `src/multi_agent_research_lab/core/state.py` để hiểu shared state.
- [ ] Bổ sung field nếu workflow cần thêm context để handoff.
- [ ] Giữ state đủ nhỏ để debug, không nhét mọi thứ vào một blob.
- [ ] Đảm bảo mọi agent update state theo cùng một format.

## 4. Implement baseline trước

- [ ] Thay placeholder trong `src/multi_agent_research_lab/services/llm_client.py`.
- [ ] Cho baseline sinh ra câu trả lời thật, không hard-code.
- [ ] Ghi lại latency và chi phí nếu provider hỗ trợ.
- [ ] Đảm bảo baseline là mốc so sánh công bằng với multi-agent.

## 5. Xây Supervisor

- [ ] Implement routing policy trong `src/multi_agent_research_lab/agents/supervisor.py`.
- [ ] Xác định khi nào gọi `Researcher`, `Analyst`, `Writer`.
- [ ] Xác định điều kiện dừng.
- [ ] Xác định khi nào route lại thay vì đi tiếp.
- [ ] Không để Supervisor quyết định mơ hồ, phải có rule rõ.

## 6. Xây worker agents

- [ ] Implement `Researcher` để thu thập facts và nguồn.
- [ ] Implement `Analyst` để lọc, tổng hợp, và rút insight.
- [ ] Implement `Writer` để tạo final answer rõ ràng, có cấu trúc.
- [ ] Nếu có `Critic`, chỉ dùng khi thật sự làm tăng chất lượng.
- [ ] Mỗi agent chỉ làm đúng phần việc của mình, không overlap quá nhiều.

## 7. Thêm fallback logic

- [ ] Retry tối thiểu cho lỗi tạm thời.
- [ ] Có giới hạn retry rõ ràng để không loop vô hạn.
- [ ] Khi agent fail, Supervisor phải chọn đường fallback thay vì chết im.
- [ ] Fallback nên ưu tiên giảm độ phức tạp trước khi từ bỏ.
- [ ] Ghi lý do fallback vào `state.errors` và `state.trace`.
- [ ] Nếu dữ liệu không đủ, trả về output an toàn, ngắn hơn nhưng hợp lệ.

## 8. Làm log và trace gọn

- [ ] Dùng `src/multi_agent_research_lab/observability/logging.py` làm điểm cấu hình log.
- [ ] Mỗi run có `run_id` hoặc `trace_id` riêng.
- [ ] Mỗi log line nên có `agent`, `step`, `iteration`, `status`, `duration`.
- [ ] Khi fallback xảy ra, log thêm `fallback_reason`.
- [ ] Trace nên theo flow `Supervisor -> Researcher -> Analyst -> Writer`.
- [ ] Summary log ngắn, chi tiết để trong trace hoặc report.

## 9. Gắn workflow

- [ ] Implement `src/multi_agent_research_lab/graph/workflow.py`.
- [ ] Build nodes, edges, conditional routing, stop condition.
- [ ] Compile và chạy graph từ state đầu vào.
- [ ] Đảm bảo workflow trả về `ResearchState` cuối cùng.

## 10. Thêm validation và guardrail

- [ ] Dùng `max_iterations` từ config.
- [ ] Dùng `timeout_seconds` từ config.
- [ ] Validate output trước khi handoff giữa các agent.
- [ ] Báo lỗi rõ khi state hoặc output không hợp lệ.
- [ ] Không để agent im lặng trả về output rỗng mà không ghi cảnh báo.

## 11. Benchmark

- [ ] Tạo benchmark cho single-agent và multi-agent.
- [ ] Đo latency.
- [ ] Đo cost hoặc ước lượng token usage.
- [ ] Đo quality theo rubric.
- [ ] Ghi failure rate.
- [ ] So sánh kết quả trong `reports/benchmark_report.md`.

## 12. Trace và explain

- [ ] Chạy ít nhất một case có trace đầy đủ.
- [ ] Chứng minh được agent nào làm gì.
- [ ] Chỉ ra nơi có retry hoặc fallback nếu xảy ra.
- [ ] Lưu ảnh trace hoặc link trace để nộp.

## 13. Quality gate

- [ ] Chạy `ruff` để check style và import.
- [ ] Chạy `mypy` để check type.
- [ ] Chạy `pre-commit` nếu repo có cấu hình.
- [ ] Sửa hết lỗi lint/type trước khi chốt bài.

## 14. Dọn TODO

- [ ] Tìm lại toàn bộ `TODO(student)` trong `src`.
- [ ] Xác nhận TODO nào là intentional, TODO nào phải implement thật.
- [ ] Dọn sạch TODO trong code path bắt buộc để nộp bài.
- [ ] Chỉ giữ TODO trong tài liệu nếu đó là hướng dẫn cho học viên.

## 15. Test và dọn cuối

- [ ] Chạy toàn bộ test.
- [ ] Kiểm tra không còn `TODO(student)` ở phần bắt buộc.
- [ ] Kiểm tra CLI chạy được cả baseline và multi-agent.
- [ ] Đọc lại README xem hướng dẫn đã khớp với code chưa.
- [ ] Chuẩn bị phần giải thích failure mode và cách fix.
- [ ] Chạy benchmark một lần cuối và kiểm tra `reports/benchmark_report.md` có `run_id` khớp log.
- [ ] Xác nhận trace/log/report đủ để reviewer lần theo từng run.

## Definition of done

- [ ] Có baseline chạy thật.
- [ ] Có multi-agent workflow chạy thật.
- [ ] Có fallback logic rõ ràng.
- [ ] Có log và trace dễ đọc theo từng agent.
- [ ] Có benchmark report so sánh single-agent vs multi-agent.
- [ ] Có trace artifact hoặc link trace để nộp.
- [ ] Có giải thích ngắn gọn failure mode và khi nào không nên dùng multi-agent.
- [ ] Có deliverable cuối cùng đúng yêu cầu lab.
