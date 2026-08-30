# Result-card values

## Repository

- **Repository name:** `DeepSeek-V4-Flash-0731-DSpark-GX10`
- **Owner:** `sxuff`
- **Future URL:** `https://github.com/sxuff/DeepSeek-V4-Flash-0731-DSpark-GX10`

## Exact card copy

Use the previous 1600×900 DS4 card layout with these replacements:

| Position | Value |
|---|---|
| Title | `DEEPSEEK V4 FLASH 0731` |
| Subtitle | `CLEAN · Q2 IMATRIX` |
| Top-right hardware | `1× ASUS GX10 · GB10` |
| Hero value | `46.4` |
| Hero unit | `SERVED-WALL TOK/S` |
| Workload | `STRUCTURED JSON` |
| Left metric | `21.32` |
| Left label | `PLAIN BASELINE` |
| Center metric | `46.39` |
| Center label | `DSPARK MEDIAN` |
| Right metric | `2.18×` |
| Right label | `SPEEDUP` |
| Bottom-left | `MEDIAN · 3 RUNS / ARM · 1 CONCURRENT REQUEST` |
| Bottom-right | `JSON VALIDATOR 3/3 · BOTH ARMS` |

## Exact unrounded values

- Plain median: `21.322550405748803`
- DSpark median: `46.38977337700436`
- Speedup: `2.1756202937382736×`
- Plain runs: `21.322550`, `21.203202`, `21.473957`
- DSpark runs: `45.896303`, `46.506194`, `46.389773`
- Completion tokens: `611` in every measured run
- Exact structured JSON output matches: `3/3`

## Public disclosure outside the card

The card is valid for the structured JSON fixture. The README and report must retain the broader caveat: plain passed 21/24 semantic canaries, DSpark passed 18/24, with one repeated DSpark-only arithmetic regression.

Machine-readable values: [`card-values.json`](card-values.json).
