# verify.py — temporary verification script, delete after use

import duckdb

conn = duckdb.connect()

print("=== Top 5 repositories ===")
rows = conn.execute("""
    SELECT name, owner, stars, language, has_readme
    FROM read_parquet('exports/repositories.parquet')
    LIMIT 5
""").fetchall()
for row in rows:
    lang = str(row[3]) if row[3] else "None"
    print(f"  {row[0]:<35} {row[1]:<20} {row[2]:>7,} stars  {lang:<15} readme={row[4]}")

print()
print("=== README quality scores (top 10) ===")
rows = conn.execute("""
    SELECT repo_full_name, readme_quality_score, file_size
    FROM read_parquet('exports/documentation.parquet')
    WHERE file_name = 'README.md'
    ORDER BY readme_quality_score DESC
    LIMIT 10
""").fetchall()
for row in rows:
    score = row[1]
    size_kb = row[2] // 1024
    bar = "█" * (score // 10)
    print(f"  {row[0]:<45} score={score:>3}/100  size={size_kb:>5} KB  {bar}")

print()
print("=== Summary stats by language ===")
rows = conn.execute("""
    SELECT language, repo_count, ROUND(avg_stars) as avg_stars, max_stars
    FROM read_parquet('exports/summary_stats.parquet')
    ORDER BY repo_count DESC
""").fetchall()
for row in rows:
    lang = str(row[0]) if row[0] else "None"
    avg  = int(row[2]) if row[2] else 0
    print(f"  {lang:<15} {row[1]:>4} repos  avg_stars={avg:>6,}  max={row[3]:>7,}")

conn.close()