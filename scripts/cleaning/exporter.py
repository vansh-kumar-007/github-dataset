# scripts/cleaning/exporter.py
#
# This module exports our database tables to Parquet files
# ready for upload to Kaggle.
#
# It also does basic cleaning during export:
# - removes duplicate repositories
# - filters out repos with no useful content
# - adds a computed README quality score

import os
import duckdb
from scripts.utils.logger import logger
from config.settings import DATA_DIR, EXPORTS_DIR


DB_PATH = os.path.join(DATA_DIR, "github_dataset.duckdb")


def get_connection():
    return duckdb.connect(DB_PATH)


def compute_readme_quality_score(content):
    """
    Gives each README a simple quality score from 0 to 100.
    This is the "added value" feature that makes our dataset
    more useful than a plain file dump.

    We check for the presence of useful sections that indicate
    a well-documented project. Each feature adds points.
    """

    if not content:
        return 0

    content_lower = content.lower()
    score = 0

    # Length — longer READMEs tend to be more complete
    if len(content) > 500:   score += 10
    if len(content) > 1000:  score += 10
    if len(content) > 3000:  score += 10

    # Has a code example (backtick blocks)
    if "```" in content:
        score += 15

    # Has an installation section
    if any(w in content_lower for w in ["install", "installation", "getting started"]):
        score += 15

    # Has a usage section
    if any(w in content_lower for w in ["usage", "how to use", "example", "quickstart"]):
        score += 10

    # Has a contributing section
    if any(w in content_lower for w in ["contribut", "pull request", "open an issue"]):
        score += 10

    # Has a license mention
    if any(w in content_lower for w in ["license", "licence", "mit", "apache", "gpl"]):
        score += 10

    # Has badges (common in well-maintained repos)
    if "![" in content or "[![" in content:
        score += 10

    return min(score, 100)


def export_repositories():
    """
    Exports the repositories table to Parquet.
    Removes any duplicates and adds a has_readme column.
    """

    conn = get_connection()
    os.makedirs(EXPORTS_DIR, exist_ok=True)

    output_path = os.path.join(EXPORTS_DIR, "repositories.parquet")

    logger.info("Exporting repositories table...")

    # We join with documentation to add a has_readme flag
    # This lets researchers quickly filter repos with documentation
    conn.execute(f"""
        COPY (
            SELECT DISTINCT
                r.id,
                r.name,
                r.owner,
                r.full_name,
                r.description,
                r.stars,
                r.forks,
                r.language,
                r.license,
                r.created_at,
                r.updated_at,
                r.topics,
                r.archived,
                r.repo_url,
                r.collected_at,
                CASE WHEN d.repo_full_name IS NOT NULL THEN true ELSE false END AS has_readme
            FROM repositories r
            LEFT JOIN (
                SELECT DISTINCT repo_full_name
                FROM documentation
                WHERE file_name = 'README.md'
            ) d ON r.full_name = d.repo_full_name
            ORDER BY r.stars DESC
        ) TO '{output_path}' (FORMAT PARQUET, COMPRESSION ZSTD)
    """)

    count = conn.execute("SELECT COUNT(*) FROM repositories").fetchone()[0]
    conn.close()

    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    logger.info(f"Exported {count:,} repositories → {size_mb:.1f} MB")
    return count


def export_documentation():
    """
    Exports the documentation table to Parquet.
    Adds a readme_quality_score for README files.
    """

    conn = get_connection()
    os.makedirs(EXPORTS_DIR, exist_ok=True)

    output_path = os.path.join(EXPORTS_DIR, "documentation.parquet")

    logger.info("Exporting documentation table...")

    # Fetch all documentation rows
    rows = conn.execute("""
        SELECT id, repo_full_name, file_name, content, file_size, collected_at
        FROM documentation
        ORDER BY repo_full_name, file_name
    """).fetchall()

    # Add quality scores and prepare cleaned data
    cleaned_rows = []
    for row in rows:
        doc_id, repo_full_name, file_name, content, file_size, collected_at = row

        # Compute quality score only for README files
        quality_score = 0
        if file_name == "README.md":
            quality_score = compute_readme_quality_score(content)

        cleaned_rows.append({
            "id":                  doc_id,
            "repo_full_name":      repo_full_name,
            "file_name":           file_name,
            "content":             content,
            "file_size":           file_size,
            "readme_quality_score": quality_score,
            "collected_at":        str(collected_at),
        })

    # Write to a temporary in-memory table then export
    conn.execute("DROP TABLE IF EXISTS documentation_export")
    conn.execute("""
        CREATE TABLE documentation_export (
            id                    INTEGER,
            repo_full_name        VARCHAR,
            file_name             VARCHAR,
            content               VARCHAR,
            file_size             INTEGER,
            readme_quality_score  INTEGER,
            collected_at          VARCHAR
        )
    """)

    conn.executemany("""
        INSERT INTO documentation_export VALUES (?, ?, ?, ?, ?, ?, ?)
    """, [
        (r["id"], r["repo_full_name"], r["file_name"],
         r["content"], r["file_size"], r["readme_quality_score"],
         r["collected_at"])
        for r in cleaned_rows
    ])

    conn.execute(f"""
        COPY documentation_export
        TO '{output_path}' (FORMAT PARQUET, COMPRESSION ZSTD)
    """)

    conn.execute("DROP TABLE IF EXISTS documentation_export")
    conn.close()

    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    logger.info(f"Exported {len(cleaned_rows):,} documentation files → {size_mb:.1f} MB")
    return len(cleaned_rows)


def export_summary_stats():
    """
    Creates a small summary statistics file.
    This is useful for the Kaggle dataset description
    and for researchers who want a quick overview.
    """

    conn = get_connection()
    os.makedirs(EXPORTS_DIR, exist_ok=True)

    output_path = os.path.join(EXPORTS_DIR, "summary_stats.parquet")

    logger.info("Exporting summary statistics...")

    conn.execute(f"""
        COPY (
            SELECT
                language,
                COUNT(*)                    AS repo_count,
                AVG(stars)                  AS avg_stars,
                MAX(stars)                  AS max_stars,
                MIN(stars)                  AS min_stars,
                AVG(forks)                  AS avg_forks,
                SUM(CASE WHEN archived THEN 1 ELSE 0 END) AS archived_count
            FROM repositories
            WHERE language IS NOT NULL
            GROUP BY language
            ORDER BY repo_count DESC
        ) TO '{output_path}' (FORMAT PARQUET, COMPRESSION ZSTD)
    """)

    conn.close()
    logger.info("Exported summary statistics")


def run_export():
    """
    Runs the complete export pipeline.
    Exports all three Parquet files and prints a final summary.
    """

    logger.info("Starting Parquet export...")
    os.makedirs(EXPORTS_DIR, exist_ok=True)

    repo_count = export_repositories()
    doc_count  = export_documentation()
    export_summary_stats()

    # Print sizes of all exported files
    print()
    print("=" * 50)
    print("  Export complete")
    print("=" * 50)
    for fname in os.listdir(EXPORTS_DIR):
        if fname.endswith(".parquet"):
            fpath = os.path.join(EXPORTS_DIR, fname)
            size_mb = os.path.getsize(fpath) / (1024 * 1024)
            print(f"  {fname:<35} {size_mb:.1f} MB")
    print("=" * 50)
    print()