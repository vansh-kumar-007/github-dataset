<div align="center">

# GitHub Documentation Dataset

**A structured collection of 1,200+ open-source repositories across 15 languages,\
built for AI research, LLM fine-tuning, and software engineering studies.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Format](https://img.shields.io/badge/Format-Parquet%20%2B%20ZSTD-00B4D8?style=flat-square)](https://parquet.apache.org)
[![Database](https://img.shields.io/badge/Database-DuckDB-FFC300?style=flat-square)](https://duckdb.org)
[![API](https://img.shields.io/badge/Source-GitHub%20REST%20API-181717?style=flat-square&logo=github)](https://docs.github.com/en/rest)
[![License](https://img.shields.io/badge/Pipeline%20License-MIT-22C55E?style=flat-square)](LICENSE)

[Overview](#overview) · [Dataset Contents](#dataset-contents) · [Quick Start](#quick-start) · [Schema](#schema) · [Reproduce](#reproducing-this-dataset) · [Citation](#citation)

</div>

---

## Overview

Most GitHub datasets collect **source code**. This one collects something rarer and more useful for language models: the *documentation layer* — the files developers write to explain, teach, and contextualize their work.

This dataset was built with a deliberate **multi-tier search strategy** that samples repositories across 15 languages and 4 star-count tiers, avoiding the popularity bias that plagues most scraped GitHub datasets.

### What you get

- Structured **repository metadata** (stars, forks, license, topics, language, dates)
- Raw decoded content of **README, LICENSE, CONTRIBUTING, CHANGELOG, SECURITY, CODE\_OF\_CONDUCT**
- **Dependency manifests** (requirements.txt, package.json, Cargo.toml, go.mod, Gemfile, and more)
- A calibrated **README quality score** (0–100) based on structure, depth, and completeness
- All data in **Parquet format** with ZSTD compression, ready for DuckDB, pandas, or Polars

### Research applications

| Use case | How this dataset helps |
|---|---|
| LLM fine-tuning | High-quality human-written technical prose with metadata context |
| RAG systems | Chunked documentation with repo-level metadata for filtering |
| Documentation quality research | Quality scores + raw text enable supervised and unsupervised studies |
| License compliance tooling | License field + raw LICENSE content for 1,200+ repos |
| Dependency trend analysis | Structured dependency files across languages and time |
| Software engineering research | Balanced cross-language sample with star-tier stratification |

---

## Dataset contents

| File | Rows | Size | Description |
|---|---|---|---|
| `repositories.parquet` | 1,210 | ~0.2 MB | Repository metadata |
| `documentation.parquet` | 2,900+ | ~8.4 MB | File contents + quality scores |
| `summary_stats.parquet` | 22 | <0.1 MB | Per-language aggregated statistics |

### Language distribution

```
Python          151 repos  ████████████████████  12.5%
TypeScript       99 repos  █████████████         8.2%
JavaScript       86 repos  ███████████           7.1%
Rust             76 repos  ██████████            6.3%
Go               76 repos  ██████████            6.3%
C++              75 repos  ██████████            6.2%
Java             73 repos  █████████             6.0%
Shell            71 repos  █████████             5.9%
C                69 repos  █████████             5.7%
HTML             68 repos  █████████             5.6%
Swift            65 repos  ████████              5.4%
PHP              64 repos  ████████              5.3%
Kotlin           64 repos  ████████              5.3%
Ruby             64 repos  ████████              5.3%
CSS              64 repos  ████████              5.3%
```

### Documentation file coverage

| File | Found in | Coverage |
|---|---|---|
| README.md | 944 repos | 93% |
| LICENSE | 646 repos | 64% |
| CONTRIBUTING.md | 262 repos | 26% |
| package.json | 213 repos | 21% |
| CHANGELOG.md | 197 repos | 20% |
| CODE\_OF\_CONDUCT.md | 130 repos | 13% |
| SECURITY.md | 122 repos | 12% |
| pyproject.toml | 72 repos | 7% |
| Gemfile | 70 repos | 7% |
| Cargo.toml | 63 repos | 6% |

---

## Quick start

```python
import duckdb

conn = duckdb.connect()

# Top Python repositories by stars
conn.execute("""
    SELECT name, owner, stars, license
    FROM read_parquet('repositories.parquet')
    WHERE language = 'Python'
    ORDER BY stars DESC
    LIMIT 10
""").df()
```

```python
# Highest quality READMEs in the dataset
conn.execute("""
    SELECT r.full_name, r.language, r.stars, d.readme_quality_score
    FROM read_parquet('repositories.parquet') r
    JOIN read_parquet('documentation.parquet') d
        ON r.full_name = d.repo_full_name
    WHERE d.file_name = 'README.md'
    ORDER BY d.readme_quality_score DESC
    LIMIT 20
""").df()
```

```python
# License distribution across the dataset
conn.execute("""
    SELECT license, COUNT(*) as count,
           ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) as pct
    FROM read_parquet('repositories.parquet')
    WHERE license IS NOT NULL
    GROUP BY license
    ORDER BY count DESC
""").df()
```

```python
# README length vs quality score correlation
conn.execute("""
    SELECT
        r.language,
        ROUND(AVG(d.file_size) / 1024.0, 1)      AS avg_readme_kb,
        ROUND(AVG(d.readme_quality_score), 1)     AS avg_quality_score,
        COUNT(*)                                   AS repo_count
    FROM read_parquet('repositories.parquet') r
    JOIN read_parquet('documentation.parquet') d
        ON r.full_name = d.repo_full_name
    WHERE d.file_name = 'README.md'
      AND r.language IS NOT NULL
    GROUP BY r.language
    ORDER BY avg_quality_score DESC
""").df()
```

---

## Schema

### `repositories.parquet`

| Field | Type | Description |
|---|---|---|
| `id` | integer | GitHub repository ID |
| `name` | string | Repository name |
| `owner` | string | Owner username or organization |
| `full_name` | string | `owner/name` — primary key |
| `description` | string | Repository description text |
| `stars` | integer | Star count at collection time |
| `forks` | integer | Fork count at collection time |
| `language` | string | Primary programming language |
| `license` | string | License name (e.g. MIT, Apache 2.0) |
| `created_at` | string | Repository creation timestamp |
| `updated_at` | string | Last push timestamp |
| `topics` | string | Comma-separated topic tags |
| `archived` | boolean | Whether the repository is archived |
| `repo_url` | string | Full GitHub HTML URL |
| `has_readme` | boolean | Whether README.md was found |
| `collected_at` | timestamp | When this record was collected |

### `documentation.parquet`

| Field | Type | Description |
|---|---|---|
| `id` | integer | Auto-generated row ID |
| `repo_full_name` | string | Foreign key → repositories.full\_name |
| `file_name` | string | e.g. `README.md`, `LICENSE`, `Cargo.toml` |
| `content` | string | Full decoded UTF-8 file content |
| `file_size` | integer | Content length in bytes |
| `readme_quality_score` | integer | 0–100 quality score (README only, else 0) |
| `collected_at` | timestamp | When this file was collected |

### `summary_stats.parquet`

| Field | Type | Description |
|---|---|---|
| `language` | string | Programming language |
| `repo_count` | integer | Number of repositories |
| `avg_stars` | float | Mean star count |
| `max_stars` | integer | Highest star count |
| `min_stars` | integer | Lowest star count |
| `avg_forks` | float | Mean fork count |
| `archived_count` | integer | Number of archived repositories |

---

## README quality score

Each README receives a score from **0 to 100** based on six dimensions:

| Dimension | Max points | What is measured |
|---|---|---|
| Length | 20 | Gradual scale across 5 thresholds — no artificial cliffs |
| Structure | 15 | Number of markdown headers (H1–H6) |
| Code examples | 20 | Count of fenced code blocks |
| Key sections | 25 | Presence of installation, usage, examples, contributing, license |
| Links | 10 | Number of markdown hyperlinks |
| Badges | 5 | CI, coverage, and version badge count |

> **Note:** This score is a structural heuristic, not ground truth. It measures *form*, not *quality of explanation*. Use it as a feature for downstream models, not as a definitive ranking.

---

## Pipeline architecture

```
GitHub REST API
      │
      ▼
┌─────────────────┐     ┌──────────────────┐
│   Crawler       │────▶│  Doc Fetcher     │
│  (15 languages  │     │  (14 file types  │
│   × 4 tiers)   │     │   per repo)      │
└─────────────────┘     └──────────────────┘
      │                         │
      ▼                         ▼
┌─────────────────────────────────────────┐
│         DuckDB  (github_dataset.duckdb) │
│   repositories │ documentation │ progress│
└─────────────────────────────────────────┘
                      │
                      ▼
         ┌────────────────────────┐
         │  Parquet Exporter      │
         │  + README quality score│
         └────────────────────────┘
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
  repositories  documentation  summary
   .parquet      .parquet      _stats
                               .parquet
```

---

## Reproducing this dataset

**Requirements:** Python 3.10+, a GitHub Personal Access Token with `public_repo` scope

```bash
git clone https://github.com/vansh-kumar-007/github-dataset.git
cd github-dataset

# Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux

pip install -r requirements.txt
```

Copy `.env.example` to `.env` and add your token:

```bash
GITHUB_TOKEN=your_token_here
MAX_REPOS=1000
REQUEST_DELAY=1.5
```

Run the full pipeline:

```bash
# Collect 1,000 repositories across all languages and star tiers
python main.py --diverse --repos 1000

# Export to Parquet files
python main.py --export
```

**Available flags:**

| Flag | Description |
|---|---|
| `--diverse` | Use multi-language, multi-tier search strategy |
| `--repos N` | Target number of repositories to collect |
| `--no-docs` | Skip documentation fetching (metadata only) |
| `--docs-only` | Skip crawling, fetch docs for existing repos |
| `--export` | Export database to Parquet files |

The pipeline is **fully resumable** — if it stops for any reason, run the same command again and it picks up exactly where it left off.

---

## Limitations and ethics

- Collected via the GitHub REST API in compliance with [GitHub's Terms of Service](https://docs.github.com/en/site-policy/github-terms/github-terms-of-service)
- Only **public repositories** are included — no private or internal repositories
- File contents are reproduced under their **original licenses** — users are responsible for verifying individual repository licenses before using content for training or commercial purposes
- Star counts and metadata reflect the **collection date** and will drift over time
- The README quality score is a **heuristic** and should not be treated as ground truth for documentation quality research
- The multi-tier sampling strategy reduces but does **not eliminate** popularity bias

---

## License

The pipeline code in this repository is released under the **MIT License** — see [LICENSE](LICENSE) for details.

The collected dataset contains content from third-party repositories. Each file's original license is recorded in the `license` field of `repositories.parquet`. Users must comply with individual repository licenses when using file content.

---

## Citation

If you use this dataset in research, please cite:

```bibtex
@dataset{github_documentation_dataset_2026,
  author    = {Kumar, Vansh},
  title     = {GitHub Documentation Dataset},
  year      = {2026},
  publisher = {Kaggle},
  url       = {https://kaggle.com/datasets/vansh-kumar-007/github-documentation-dataset}
}
```

---

## Changelog

### v1.0.0 — June 2026

- Initial release with 1,210 repositories across 15 languages
- 2,900+ documentation files decoded and stored
- Calibrated v2 README quality scorer (0–100 scale)
- Parquet export with ZSTD compression (~8.6 MB total)
- Resumable pipeline with per-file fetch tracking

---

<div align="center">

Built with Python · DuckDB · GitHub REST API · Parquet

</div>
