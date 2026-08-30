# Technical report

## Finding

On one ASUS GX10, Entrpi `ds4` v0.6.2 with the pinned 0731 Q2K/Q8 DSpark drafter increased the normal DeepSeek V4 Flash 0731 target from **21.32 to 46.39 served-wall tok/s** on a 611-token structured JSON generation. The median ratio was **2.18x** across three measured repetitions per arm.

The complete four-fixture comparison produced a **1.57x geometric-mean speedup** and increased token-weighted served-wall throughput from **21.41 to 29.93 tok/s**, or **1.40x**.

## Full matrix

| Fixture | Plain median | DSpark median | Ratio | Semantic validator |
|---|---:|---:|---:|---:|
| Structured JSON | 21.32 | 46.39 | 2.18x | 3/3 both arms |
| Code | 21.26 | 38.01 | 1.79x | Plain 0/3, DSpark 1/3 |
| Reasoning | 21.45 | 33.92 | 1.58x | 3/3 both arms |
| Prose | 21.53 | 21.33 | 0.99x | 3/3 both arms |

The prose control confirms that DSpark is workload-dependent. The result is not a universal 2.18x model speedup.

## Metric

Every reported rate is:

```text
server-reported completion tokens / full non-streaming request wall seconds
```

It includes prefill and first-token latency. It is served-wall throughput, not isolated decode-kernel throughput.

## DSpark activation

Collection was allowed only after startup logged a persistent two-bank continuous context. The DSpark service then logged continuous execution with zero fallback requests.

Across harness warm-ups and measured requests, runtime metrics recorded:

- Drafted tokens: 6,510
- Accepted draft tokens: 5,855
- Sampled acceptance: 89.94%
- Quenches: 7

Acceptance is an efficiency diagnostic, not a quality score.

## Quality

The headline structured JSON fixture passed 3/3 in both arms and produced identical output hashes in all three paired requests.

The broader quality result was weaker:

- Plain: 21/24 semantic canaries
- DSpark: 18/24 semantic canaries
- Exact cross-arm outputs: 18/36
- Repeated DSpark-only regression: arithmetic answer `16229` became `18713` in 3/3 repetitions
- Tool-call regression: none
- Sandboxed-code regression: none

This makes the completed protocol a **no-go for a quality-neutral deployment claim**. It does not invalidate the measured structured JSON speed result.

## Safety

Both arms ran under whole-host memory and swap-growth supervision with cgroup swap disabled.

| Arm | Minimum MemAvailable | Maximum swap growth |
|---|---:|---:|
| Plain | 19.09 GiB | 0 MiB |
| DSpark | 18.16 GiB | 151.19 MiB |

No watchdog incident occurred. The DSpark arm remained below the frozen 512 MiB swap-growth ceiling and above the 6 GiB reserve.

## Reproducibility boundary

The repository pins target, drafter, runtime revision, fixture bytes, sampler, context, continuous banks, memory floor, and hashes. Rebuilt runtime binaries can differ byte-for-byte across compiler and toolkit versions, so the measured binary hash is retained as evidence rather than required from every source rebuild.

A different checkpoint, drafter, runtime commit, context allocation, concurrency level, cache state, or timing denominator is a different experiment.
