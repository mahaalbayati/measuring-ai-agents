# Data and code for "Measuring AI Agents: Validity, Reliability, and What Leaderboards Hide"

This repository accompanies the book chapter *Measuring AI Agents: Validity, Reliability, and What Leaderboards Hide*
([Author names], in *Advances in Artificial Intelligence and Computer Science: Methods, Systems, and Applications*,
Karabük University Press, 2026). It contains the frozen data snapshot and the analysis script that reproduce every
table and figure in Section 5 of the chapter.

## Nature of the analysis

This is a **secondary statistical analysis of publicly released data**. The authors did **not** run any AI agent,
re-execute any patch or re-run the SWE-bench evaluation harness. Every task outcome was produced by the original
leaderboard submitters, who ran their own agents and the SWE-bench evaluation harness and published the results in the
official SWE-bench experiments repository. The authors' contribution is the assembly of these outcomes into one
submission × task matrix at a fixed commit, the statistical analyses (E1–E5 below) and this reproducibility package.
The findings apply to SWE-bench Verified at the commit analysed and are not claimed to hold for other benchmarks.

## Data source

| Item | Value |
|---|---|
| Source repository | https://github.com/SWE-bench/experiments |
| Commit | `40f164d5b8f1d249bf95a6df8b74b577fd8e519d` (committed 2026-09-03T01:24:30Z) |
| Retrieved | 2026-10-27T10:10Z |
| Files used per submission | `evaluation/verified/<submission>/results/results.json` (field `resolved`); `evaluation/verified/<submission>/metadata.yaml` (fields `tags.model`, `tags.system.attempts`, `info.resolved`) |
| Task ID list | keys of `evaluation/verified/<submission>/per_instance_details.json` (500 SWE-bench Verified instance IDs) |
| Submissions listed at this commit | 182 |
| Included | 135 (those providing `results/results.json`) |
| Excluded | 40 with per-task data only in `per_instance_details.json` (different format, not parsed); 7 with no per-task data |
| Tasks | 500 (29 resolved by no included submission) |
| Model-name harmonisation | `claude-4-sonnet-20250514` → `claude-sonnet-4-20250514` |

All task outcomes, model names and attempt counts are **as reported by the submitters**; they were not verified
independently. The benchmark itself is described in: C. E. Jimenez et al., "SWE-bench: Can Language Models Resolve
Real-World GitHub Issues?", arXiv:2310.06770.

## Contents

```
measuring-ai-agents/
├── README.md
├── LICENSE                                   MIT licence (code)
├── requirements.txt
├── swebench_reliability_analysis.py          analysis script (E1–E5)
├── data/
│   ├── swebench_verified_outcomes_40f164d.csv   135 × 500 binary outcome matrix (1 = resolved)
│   ├── submission_log_40f164d.csv               all 182 submissions: inclusion status, exclusion reason, score, attempts, models
│   ├── raw_files_40f164d.zip                    results.json and metadata.yaml files as retrieved
│   └── MANIFEST_40f164d.json                    commit, source paths, counts and SHA-256 checksums
└── figures/                                  figures as published in the chapter (300 dpi)
```

### SHA-256 checksums

| File | SHA-256 |
|---|---|
| `swebench_verified_outcomes_40f164d.csv` | `433e345cf40b88e26e1f16d686ef18cdc645ee52157b468f6f800ea59c2ad847` |
| `submission_log_40f164d.csv` | `96c3fce5c88a296a60527f1e38cc0b8d7599f593bc51452321d7b491ee797123` |
| `raw_files_40f164d.zip` | `22f6a6453128a2a24a0c3a7c8226e9bbc33931162cc4e45a2f46aa6ca55cd45b` |

## How to run

Requirements: Python ≥ 3.10.

```bash
pip install -r requirements.txt

# 1) Reproduce all results from the frozen snapshot in ./data (no internet needed)
python swebench_reliability_analysis.py

# 2) Optional: rebuild the snapshot from the pinned commit, then analyse it
python swebench_reliability_analysis.py --rebuild
```

The script first prints the SHA-256 of the outcome matrix and whether it matches the chapter's snapshot. Run time is
under one minute on a standard laptop; no GPU or model inference is needed. Random seeds are fixed
(bootstrap seed 0, simulation seed 1).

### Expected output

```
outcome matrix sha256: 433e345cf40b88e26e1f16d686ef18cdc645ee52157b468f6f800ea59c2ad847 (matches chapter snapshot)
135 submissions x 500 tasks; tasks resolved by no included submission: 29
E1 adjacent pairs not significant: 130/134; top-20 pairs not significant: 140/190; median gap 0.4 pp; median CI half-width 4.2 pp
E2 P(rank 1) for observed ranks 1-3: [0.336 0.352 0.262]
E3 runs/task=1: Kendall tau=0.685, adjacent inverted=0.419
E3 runs/task=3: Kendall tau=0.807, adjacent inverted=0.364
E3 runs/task=5: Kendall tau=0.846, adjacent inverted=0.332
E3 runs/task=10: Kendall tau=0.888, adjacent inverted=0.286
E4 attempts reported: {'2+': 82, '1': 45, 'unreported': 8}
E4 Qwen 2.5: n=3, 30.2-40.2% (range 10.0 pp)
E4 claude-3-5-sonnet-20241022: n=12, 33.6-63.4% (range 29.8 pp)
E4 claude-sonnet-4-20250514: n=9, 57.0-76.8% (range 19.8 pp)
E4 gpt-4o-2024-05-13: n=4, 23.2-38.8% (range 15.6 pp)
E4 gpt-4o-2024-08-06: n=3, 24.0-32.6% (range 8.6 pp)
E5 top-20: solved by all 250, by none 41, discriminating 209; tasks with 30-70% pass rate: 174
```

Minor differences in the last decimal of the Monte Carlo values (E2, E3) are possible with other library versions.
The chapter's values were produced with Python 3.11.17, NumPy 2.4.6, pandas 2.3.3, SciPy 1.17.1 and statsmodels 0.15.0.

## Analyses

| ID | Analysis | Method |
|---|---|---|
| E1 | Statistical resolution of the leaderboard | Wilson 95% intervals; exact McNemar test for paired comparisons (α = 0.05, uncorrected) |
| E2 | Rank uncertainty | 2,000 bootstrap resamples of tasks, top 15 submissions |
| E3 | Repeated-run stability (**simulation**) | Rasch model fitted by penalised joint maximum likelihood (λ = 0.05); 2,000 simulated leaderboards for 1, 3, 5, 10 runs per task. Model-based, not observed reruns |
| E4 | Attribution | Score range of the same declared model across submissions; declared attempts per task |
| E5 | Task informativeness | Tasks solved by all, none or some of the top 20; tasks with 30–70% pass rate |

## Licence

- **Code** (`swebench_reliability_analysis.py`): MIT licence, see `LICENSE`.
- **Derived data** (`swebench_verified_outcomes_40f164d.csv`, `submission_log_40f164d.csv`, `MANIFEST_40f164d.json`) and
  **figures**: CC BY 4.0, to the extent the authors hold rights in them.
- **Raw files** (`raw_files_40f164d.zip`): copies of files from the SWE-bench experiments repository, which declares no
  licence at the commit used. They are included only so that the snapshot can be verified, and remain under the terms of
  their original authors. They can be regenerated with `--rebuild`.

## Citation

If you use this package, please cite the chapter:

> [Author names], "Measuring AI Agents: Validity, Reliability, and What Leaderboards Hide," in *Advances in Artificial
> Intelligence and Computer Science: Methods, Systems, and Applications*, O. Fındık and O. Menemencioğlu, Eds.
> Karabük, Türkiye: Karabük University Press, 2026.

and the SWE-bench benchmark (Jimenez et al., arXiv:2310.06770).

## Contact

[Corresponding author name, e-mail]
