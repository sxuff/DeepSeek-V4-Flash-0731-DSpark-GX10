# 46.39 tok/s result

Normal, non-abliterated DeepSeek V4 Flash 0731 reached a **46.39 tok/s served-wall median** on one ASUS GX10 with NVIDIA GB10.

The matched plain baseline was **21.32 tok/s**. Active DSpark delivered a **2.18x** speedup on the structured JSON fixture.

| Arm | Run 1 | Run 2 | Run 3 | Median | Validator |
|---|---:|---:|---:|---:|---:|
| Plain baseline | 21.32 | 21.20 | 21.47 | 21.32 | 3/3 |
| DSpark | 45.90 | 46.51 | 46.39 | **46.39** | 3/3 |

Each run generated exactly 611 completion tokens. All 3/3 paired structured JSON outputs matched exactly across arms.

## Comparison contract

- Same normal 0731 Q2-imatrix target and immutable revision
- Same Entrpi `ds4` runtime revision
- Same NVIDIA GB10 hardware
- Same structured JSON request payloads
- Same temperature-zero sampler
- One request at a time
- Three measured repetitions after warm-up
- Arm difference: `--no-spec` baseline versus the pinned DSpark drafter with DSpark trace/profile counters enabled
- Metric: completion tokens divided by full non-streaming request wall time

## Claim boundary

The structured JSON validator passed every measured run in both arms. This supports fixture-level output parity, not universal model-quality parity.

Across the broader frozen suite, plain passed 21/24 semantic canaries and DSpark passed 18/24. DSpark introduced one repeated arithmetic regression while tool calling and sandboxed code did not regress. The repository therefore does not claim a quality-neutral deployment improvement.
