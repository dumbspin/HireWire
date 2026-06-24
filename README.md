---
title: HireWire
emoji: 🎯
colorFrom: indigo
colorTo: green
sdk: docker
app_port: 7860
pinned: false
license: mit
---

# Redrob Intelligent Candidate Ranker (ICR)

Ranking system for the **India Runs Data & AI Challenge** — Intelligent Candidate Discovery & Ranking.

## Reproduce

```bash
pip install -r requirements.txt
python download_model.py          # one-time: saves model to models/
python rank.py \
  --candidates ./candidates.jsonl \
  --jd ./job_description.docx \
  --out ./submission.csv
```

End-to-end runtime: ~2–3 minutes on CPU (16 GB RAM). No GPU, no network required.

## Architecture

```
rank.py                 # Orchestration: stream, score, sort, write CSV
jd_parser.py            # Parses JD must-haves / nice-to-haves
disqualifiers.py        # 6 hard filters + honeypot suppression
feature_extractor.py    # Skill trust + semantic similarity (MiniLM)
scorer.py               # Weighted hybrid score + behavioral multiplier
models/all-MiniLM-L6-v2/  # Pre-downloaded embedding model (offline)
```

## Scoring Weights

| Component | Weight |
|---|---|
| Skills Match (semantic + trust) | 35% |
| Career Trajectory (title + prod keywords) | 25% |
| Experience Alignment (Gaussian, μ=7yrs) | 15% |
| Location / Notice Period | 10% |
| Education Tier | 5% |
| Behavioral Multiplier | ×(0.85–1.0) |

## Disqualifiers

| Rule | Score Cap |
|---|---|
| Honeypot (founding date / skill anomaly) | 0.10 |
| Consulting-only career | 0.15 |
| No production code > 18 months | 0.20 |
| LLM-wrapper only < 12 months | 0.20 |
| Academic/research-only | 0.20 |
| CV/speech/robotics, no NLP | 0.25 |
| Title chaser (avg tenure < 15 months) | 0.25 |

## Demo

```bash
streamlit run demo/app.py
```

## Tests

```bash
python -m pytest tests/ -v   # 12 tests, all pass
```
