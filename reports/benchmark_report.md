# Benchmark Report

## Case: graphrag_200

| Run ID | Run | Latency (s) | Cost (USD) | Quality | Valid | Sources | Errors | Trace | Trace Link | Notes |
|---|---|---:|---:|---:|---|---:|---:|---:|---|---|
| benchmark-4e955bb5 | baseline | 4.19 | 0.0158 | 4.0 | yes | 0 | 0 | 0 | reports/traces/benchmark-4e955bb5_baseline.json | status=pass; sources=0; errors=0; trace_events=0; routes=none |
| benchmark-4e955bb5 | multi-agent | 13.71 | 0.1388 | 9.2 | yes | 5 | 0 | 8 | reports/traces/benchmark-4e955bb5_multi-agent.json | status=pass; sources=5; errors=0; trace_events=8; routes=researcher -> analyst -> writer |


## Case: rag_vs_graphrag

| Run ID | Run | Latency (s) | Cost (USD) | Quality | Valid | Sources | Errors | Trace | Trace Link | Notes |
|---|---|---:|---:|---:|---|---:|---:|---:|---|---|
| benchmark-22a72cb4 | baseline | 7.82 | 0.0280 | 4.0 | yes | 0 | 0 | 0 | reports/traces/benchmark-22a72cb4_baseline.json | status=pass; sources=0; errors=0; trace_events=0; routes=none |
| benchmark-22a72cb4 | multi-agent | 19.97 | 0.1998 | 9.2 | yes | 5 | 0 | 8 | reports/traces/benchmark-22a72cb4_multi-agent.json | status=pass; sources=5; errors=0; trace_events=8; routes=researcher -> analyst -> writer |


## Case: orchestration

| Run ID | Run | Latency (s) | Cost (USD) | Quality | Valid | Sources | Errors | Trace | Trace Link | Notes |
|---|---|---:|---:|---:|---|---:|---:|---:|---|---|
| benchmark-ba9d76ae | baseline | 4.07 | 0.0184 | 4.0 | yes | 0 | 0 | 0 | reports/traces/benchmark-ba9d76ae_baseline.json | status=pass; sources=0; errors=0; trace_events=0; routes=none |
| benchmark-ba9d76ae | multi-agent | 38.19 | 0.1249 | 9.2 | yes | 5 | 0 | 8 | reports/traces/benchmark-ba9d76ae_multi-agent.json | status=pass; sources=5; errors=0; trace_events=8; routes=researcher -> analyst -> writer |


## Case: failure_modes

| Run ID | Run | Latency (s) | Cost (USD) | Quality | Valid | Sources | Errors | Trace | Trace Link | Notes |
|---|---|---:|---:|---:|---|---:|---:|---:|---|---|
| benchmark-70bb0cad | baseline | 3.75 | 0.0124 | 4.0 | yes | 0 | 0 | 0 | reports/traces/benchmark-70bb0cad_baseline.json | status=pass; sources=0; errors=0; trace_events=0; routes=none |
| benchmark-70bb0cad | multi-agent | 19.78 | 0.1538 | 9.2 | yes | 5 | 0 | 8 | reports/traces/benchmark-70bb0cad_multi-agent.json | status=pass; sources=5; errors=0; trace_events=8; routes=researcher -> analyst -> writer |


## Case: sparse_sources

| Run ID | Run | Latency (s) | Cost (USD) | Quality | Valid | Sources | Errors | Trace | Trace Link | Notes |
|---|---|---:|---:|---:|---|---:|---:|---:|---|---|
| benchmark-8f04eabd | baseline | 5.34 | 0.0201 | 4.0 | yes | 0 | 0 | 0 | reports/traces/benchmark-8f04eabd_baseline.json | status=pass; sources=0; errors=0; trace_events=0; routes=none |
| benchmark-8f04eabd | multi-agent | 18.73 | 0.1817 | 9.2 | yes | 5 | 0 | 8 | reports/traces/benchmark-8f04eabd_multi-agent.json | status=pass; sources=5; errors=0; trace_events=8; routes=researcher -> analyst -> writer |


## Case: guardrail_politics

| Run ID | Run | Latency (s) | Cost (USD) | Quality | Valid | Sources | Errors | Trace | Trace Link | Notes |
|---|---|---:|---:|---:|---|---:|---:|---:|---|---|
| benchmark-559f0868 | baseline | 0.00 |  | 0.1 | no | 0 | 1 | 1 | reports/traces/benchmark-559f0868_baseline.json | status=fallback; sources=0; errors=1; trace_events=1; routes=none |
| benchmark-559f0868 | multi-agent | 0.00 |  | 0.1 | no | 0 | 1 | 1 | reports/traces/benchmark-559f0868_multi-agent.json | status=fallback; sources=0; errors=1; trace_events=1; routes=none |


## Case: guardrail_hacking

| Run ID | Run | Latency (s) | Cost (USD) | Quality | Valid | Sources | Errors | Trace | Trace Link | Notes |
|---|---|---:|---:|---:|---|---:|---:|---:|---|---|
| benchmark-3cd4b899 | baseline | 0.00 |  | 0.1 | no | 0 | 1 | 1 | reports/traces/benchmark-3cd4b899_baseline.json | status=fallback; sources=0; errors=1; trace_events=1; routes=none |
| benchmark-3cd4b899 | multi-agent | 0.00 |  | 0.1 | no | 0 | 1 | 1 | reports/traces/benchmark-3cd4b899_multi-agent.json | status=fallback; sources=0; errors=1; trace_events=1; routes=none |


## Case: guardrail_weapons

| Run ID | Run | Latency (s) | Cost (USD) | Quality | Valid | Sources | Errors | Trace | Trace Link | Notes |
|---|---|---:|---:|---:|---|---:|---:|---:|---|---|
| benchmark-7c703452 | baseline | 0.00 |  | 0.1 | no | 0 | 1 | 1 | reports/traces/benchmark-7c703452_baseline.json | status=fallback; sources=0; errors=1; trace_events=1; routes=none |
| benchmark-7c703452 | multi-agent | 0.00 |  | 0.1 | no | 0 | 1 | 1 | reports/traces/benchmark-7c703452_multi-agent.json | status=fallback; sources=0; errors=1; trace_events=1; routes=none |


## Case: trace_showcase

| Run ID | Run | Latency (s) | Cost (USD) | Quality | Valid | Sources | Errors | Trace | Trace Link | Notes |
|---|---|---:|---:|---:|---|---:|---:|---:|---|---|
| benchmark-ef1e71f0 | baseline | 3.46 | 0.0121 | 4.0 | yes | 0 | 0 | 0 | reports/traces/benchmark-ef1e71f0_baseline.json | status=pass; sources=0; errors=0; trace_events=0; routes=none |
| benchmark-ef1e71f0 | multi-agent | 13.90 | 0.1425 | 9.2 | yes | 5 | 0 | 8 | reports/traces/benchmark-ef1e71f0_multi-agent.json | status=pass; sources=5; errors=0; trace_events=8; routes=researcher -> analyst -> writer |


## Case: state_of_the_art

| Run ID | Run | Latency (s) | Cost (USD) | Quality | Valid | Sources | Errors | Trace | Trace Link | Notes |
|---|---|---:|---:|---:|---|---:|---:|---:|---|---|
| benchmark-93c7372e | baseline | 5.60 | 0.0161 | 4.0 | yes | 0 | 0 | 0 | reports/traces/benchmark-93c7372e_baseline.json | status=pass; sources=0; errors=0; trace_events=0; routes=none |
| benchmark-93c7372e | multi-agent | 21.42 | 0.1751 | 9.2 | yes | 5 | 0 | 8 | reports/traces/benchmark-93c7372e_multi-agent.json | status=pass; sources=5; errors=0; trace_events=8; routes=researcher -> analyst -> writer |