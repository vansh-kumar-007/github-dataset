# GitHub Documentation Dataset

A curated dataset of **1,200+ open-source GitHub repositories** spanning
15 programming languages, collected and structured for AI research,
NLP tasks, and software engineering studies.

Unlike raw code mirrors, this dataset focuses on **human-readable
documentation** — the files developers write to explain their work.

---

## What makes this dataset unique

Most GitHub datasets collect source code. This one collects something
rarer and more useful for language models: the *documentation layer* of
open source software.

- Structured repository metadata with stars, forks, license, and topics
- Raw content of README, LICENSE, CONTRIBUTING, CHANGELOG, SECURITY, and
  CODE_OF_CONDUCT files where available
- Dependency manifests (requirements.txt, package.json, Cargo.toml, etc.)
- A computed **README quality score** (0–100) based on structure, depth,
  and completeness — not just length
- Balanced across languages and repository sizes using a multi-tier
  search strategy

---

## Dataset contents

| File | Description | Size |
|---|---|---|
| `repositories.parquet` | Repository metadata for 1,200+ repos | ~0.2 MB |
| `documentation.parquet` | 2,900+ documentation files with content | ~8.4 MB |
| `summary_stats.parquet` | Per-language aggregated statistics | <0.1 MB |

### Repository metadata fields

| Field | Type | Description |
|---|---|---|
| `id` | integer | GitHub repository ID |
| `name` | string | Repository name |
| `owner` | string | Owner username or organization |
| `full_name` | string | `owner/name` format |
| `description` | string | Repository description |
| `stars` | integer | Star count at collection time |
| `forks` | integer | Fork count |
| `language` | string | Primary programming language |
| `license` | string | License name |
| `created_at` | string | Repository creation date |
| `updated_at` | string | Last update date |
| `topics` | string | Comma-separated topic tags |
| `archived` | boolean | Whether the repository is archived |
| `repo_url` | string | Full GitHub URL |
| `has_readme` | boolean | Whether a README was found |

### Documentation fields

| Field | Type | Description |
|---|---|---|
| `repo_full_name` | string | Links to repositories table |
| `file_name` | string | e.g. `README.md`, `LICENSE` |
| `content` | string | Full decoded file content |
| `file_size` | integer | Content length in bytes |
| `readme_quality_score` | integer | 0–100 quality score (README only) |

---

## Quick start

```python
import duckdb

conn = duckdb.connect()

# Load repository metadata
repos = conn.execute("""
    SELECT name, owner, stars, language, license
    FROM read_parquet('repositories.parquet')
    WHERE language = 'Python'
    ORDER BY stars DESC
    LIMIT 10
""").df()

print(repos)
```

```python
# Find the highest quality READMEs
top_docs = conn.execute("""
    SELECT r.full_name, r.stars, r.language, d.readme_quality_score
    FROM read_parquet('repositories.parquet') r
    JOIN read_parquet('documentation.parquet') d
        ON r.full_name = d.repo_full_name
    WHERE d.file_name = 'README.md'
    ORDER BY d.readme_quality_score DESC
    LIMIT 20
""").df()

print(top_docs)
```

```python
# License distribution
licenses = conn.execute("""
    SELECT license, COUNT(*) as count
    FROM read_parquet('repositories.parquet')
    WHERE license IS NOT NULL
    GROUP BY license
    ORDER BY count DESC
""").df()

print(licenses)
```

---

## Language coverage

The dataset uses a deliberate multi-tier search strategy to ensure
balanced representation across languages and repository sizes.

| Tier | Star range | Intent |
|---|---|---|
| Emerging | 50–200 | Small but active projects |
| Established | 200–1,000 | Solid mid-size projects |
| Popular | 1,000–5,000 | Well-known projects |
| Very popular | 5,000–50,000 | Major ecosystem projects |

Languages covered: Python, JavaScript, TypeScript, Java, Go, Rust,
C++, C, Ruby, PHP, Swift, Kotlin, Shell, HTML, CSS

---

## README quality score

Each README receives a score from 0 to 100 based on:

- **Length** (up to 20 points) — gradual scale, not a cliff
- **Structure** (up to 15 points) — number of markdown headers
- **Code examples** (up to 20 points) — number of fenced code blocks
- **Key sections** (up to 25 points) — installation, usage, examples,
  contributing, license
- **Links and references** (up to 10 points) — markdown links
- **Badges** (up to 5 points) — CI, coverage, version badges
- **Penalties** — very short content, suspiciously repetitive text

This score is an imperfect heuristic, not ground truth. It is intended
as a starting point for documentation quality research.

---

## Reproducing this dataset

Requirements: Python 3.10+, a GitHub Personal Access Token

```bash
git clone https://github.com/vansh-kumar-007/github-dataset.git
cd github-dataset
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and add your GitHub token:

GITHUB_TOKEN=your_token_here

MAX_REPOS=1000

REQUEST_DELAY=1.5

Run the full pipeline:

```bash
# Collect repositories and documentation
python main.py --diverse --repos 1000

# Export to Parquet
python main.py --export
```

---

## Limitations and ethics

- Data collected via the GitHub REST API in compliance with
  [GitHub's Terms of Service](https://docs.github.com/en/site-policy/github-terms/github-terms-of-service)
- Only public repositories are included
- File contents are reproduced under their original licenses —
  users are responsible for checking individual repository licenses
  before using content for training or commercial purposes
- Star counts and metadata reflect the collection date and may be stale
- The README quality score is a heuristic and should not be treated
  as ground truth for documentation quality research

---

## License

The pipeline code in this repository is released under the
**MIT License** — see [LICENSE](LICENSE) for details.

The dataset itself contains content from third-party repositories.
Each file's license is recorded in the `license` field of
`repositories.parquet`. Users must comply with individual
repository licenses when using file contents.

---

## Citation

If you use this dataset in research, please cite it as:

@dataset{github_documentation_dataset_2026,

author    = {Kumar, Vansh},

title     = {GitHub Documentation Dataset},

year      = {2026},

publisher = {Kaggle},

url       = {https://kaggle.com/datasets/vansh-kumar-007/github-documentation-dataset}

}

---

## Changelog

### v1.0.0 — June 2026
- Initial release
- 1,200+ repositories across 15 languages
- 2,900+ documentation files
- README quality scoring (v2 calibrated scorer)
- Parquet export with ZSTD compression