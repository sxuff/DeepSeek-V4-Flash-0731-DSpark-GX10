# DeepSeek V4 Flash 0731 at 46.39 tok/s on one GX10

**Best measured result: 46.39 served-wall tok/s median versus a 21.32 tok/s plain baseline on the same normal, non-abliterated checkpoint. DSpark was 2.18x faster on the structured JSON fixture.**

The comparison used the same target, Entrpi `ds4` runtime, request payloads, sampler, context, continuous-bank configuration, and ASUS GX10. The DSpark arm added the pinned drafter and enabled DSpark trace/profile counters to prove treatment activity; the plain arm used `--no-spec`.

## Headline result

| Structured JSON | Plain baseline | DSpark |
|---|---:|---:|
| Median served-wall throughput | 21.32 tok/s | **46.39 tok/s** |
| Three measured runs | 21.32, 21.20, 21.47 | **45.90, 46.51, 46.39** |
| Exact validator | 3/3 passed | **3/3 passed** |
| Completion length | 611 tokens/run | 611 tokens/run |

- Hardware: one ASUS GX10 with NVIDIA GB10
- Model: normal, non-abliterated DeepSeek V4 Flash 0731
- Workload: structured JSON generation
- Concurrency: one request
- Repetitions: three measured runs per arm after one warm-up
- Sampling: temperature 0
- Server context: 32,768 tokens
- Metric: completion tokens divided by full non-streaming request wall time

The structured JSON output hashes matched in all 3/3 paired runs. The card-level claim is limited to this fixture.

## Full speed matrix

| Fixture | Plain | DSpark | Speedup |
|---|---:|---:|---:|
| Structured JSON | 21.32 | **46.39** | **2.18x** |
| Code | 21.26 | **38.01** | **1.79x** |
| Reasoning | 21.45 | **33.92** | **1.58x** |
| Prose | 21.53 | 21.33 | 0.99x |

- Geometric mean fixture speedup: **1.57x**
- Token-weighted served-wall rate: **21.41 to 29.93 tok/s**, **1.40x**
- Matched request payload hashes: **36/36**
- Runtime/transport errors: **0/72**
- Active DSpark telemetry: **5,855 hits from 6,510 drafts**, 89.94% sampled acceptance
- Continuous path: confirmed, zero fallback requests

## Quality boundary

This repository does **not** claim a quality-neutral deployment improvement across the full suite.

- Plain semantic canaries: **21/24**
- DSpark semantic canaries: **18/24**
- Exact cross-arm output matches: **18/36**
- Tool-call and sandboxed-code canaries did not regress
- DSpark introduced one repeated arithmetic regression:
  - Plain last integer: `16229`
  - DSpark last integer: `18713`
  - Repetitions: 3/3

The publishable finding is a measured structured-output speedup with a passing fixture-level validator, not universal losslessness.

## Safety

| Arm | Minimum MemAvailable | Maximum swap growth | Watchdog incident |
|---|---:|---:|---:|
| Plain | 19.09 GiB | 0 MiB | No |
| DSpark | 18.16 GiB | 151.19 MiB | No |

Both services ran with cgroup swap disabled. The runtime had to log `persistent batch ctx ready` before collection. The DSpark arm also had to show continuous execution with zero fallbacks.

## Exact stack

### Target

- Repository: `tekosML/DeepSeek-V4-Flash-0731-GGUF-GX10`
- Revision: `955036b188acfb10558be9977c44575d81e4bfe2`
- File: `DeepSeek-V4-Flash-0731-IQ2XXS-w2Q2K-AProjQ8-SExpQ8-OutQ8-imatrix.gguf`
- Size: 86,720,111,552 bytes, 80.76 GiB
- SHA-256: `73b86c93e7b0be37f68c4b3a5361c7e17f9b278647aa335ea304ac5dfd784867`

### DSpark drafter

- Repository: `bleysg/DeepSeek-V4-Flash-DSpark-drafter-GGUF`
- Revision: `81c6fdd38f9582da45ba27f0ed7b63bcd3ea3b62`
- File: `DSpark-drafter-Q2K-Q8-0731.gguf`
- Size: 6,971,241,504 bytes, 6.49 GiB
- SHA-256: `8fa269560dc76fd73e4233ad9b1938b5f65dd363381fd9b1a5c6183f7d12d686`

### Runtime

- Repository: `Entrpi/ds4`
- Revision: `d183482b413ecd2e3b540b290e6497437e9fbb73`
- Version: `v0.6.2`
- Build: `make cuda-spark`
- Backend: CUDA `sm_121`
- Context: 32,768
- Continuous banks: 2
- Runtime memory floor: 16 GiB

## Download and verify

```bash
hf download tekosML/DeepSeek-V4-Flash-0731-GGUF-GX10 \
  DeepSeek-V4-Flash-0731-IQ2XXS-w2Q2K-AProjQ8-SExpQ8-OutQ8-imatrix.gguf \
  --revision 955036b188acfb10558be9977c44575d81e4bfe2 \
  --local-dir ./models/target

hf download bleysg/DeepSeek-V4-Flash-DSpark-drafter-GGUF \
  DSpark-drafter-Q2K-Q8-0731.gguf \
  --revision 81c6fdd38f9582da45ba27f0ed7b63bcd3ea3b62 \
  --local-dir ./models/drafter

python3 scripts/verify_artifacts.py \
  --runtime-dir /path/to/ds4 \
  --model ./models/target/DeepSeek-V4-Flash-0731-IQ2XXS-w2Q2K-AProjQ8-SExpQ8-OutQ8-imatrix.gguf \
  --drafter ./models/drafter/DSpark-drafter-Q2K-Q8-0731.gguf
```

## Reproduce

Build the pinned runtime:

```bash
git clone https://github.com/Entrpi/ds4.git
cd ds4
git checkout --detach d183482b413ecd2e3b540b290e6497437e9fbb73
make cuda-spark
```

Set the pinned paths and start one arm:

```bash
export DS4_RUNTIME_DIR=/path/to/ds4
export DS4_MODEL_PATH=/path/to/DeepSeek-V4-Flash-0731-IQ2XXS-w2Q2K-AProjQ8-SExpQ8-OutQ8-imatrix.gguf
export DS4_DRAFTER_PATH=/path/to/DSpark-drafter-Q2K-Q8-0731.gguf
./scripts/serve.sh dspark
```

Run the frozen benchmark:

```bash
python3 scripts/bench.py \
  --arm dspark_v062 \
  --base-url http://127.0.0.1:8001 \
  --fixtures protocol/fixtures.json \
  --out run/dspark \
  --repeats 3
```

Use `./scripts/serve.sh plain` for the matched `--no-spec` arm. Run under the included watchdog on unified-memory systems.

## Evidence

- [`results/analysis.json`](results/analysis.json): complete public analysis
- [`results/structured-json-receipt.json`](results/structured-json-receipt.json): exact headline runs
- [`results/semantic-rescore-summary.json`](results/semantic-rescore-summary.json): corrected semantic quality totals
- [`protocol/PROTOCOL.json`](protocol/PROTOCOL.json): public matched protocol
- [`protocol/fixtures.json`](protocol/fixtures.json): exact prompts and validator manifest
- [`CARD_VALUES.md`](CARD_VALUES.md): result-card copy and exact values
- [`REPORT.md`](REPORT.md): technical interpretation and claim boundary

Model weights are not redistributed in this repository.

## Sources

- [Entrpi/ds4](https://github.com/Entrpi/ds4)
- [Entrpi/ds4-on-spark](https://github.com/Entrpi/ds4-on-spark)
- [Normal 0731 Q2-imatrix target](https://huggingface.co/tekosML/DeepSeek-V4-Flash-0731-GGUF-GX10)
- [0731 Q2K/Q8 DSpark drafter](https://huggingface.co/bleysg/DeepSeek-V4-Flash-DSpark-drafter-GGUF)
