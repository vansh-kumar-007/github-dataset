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
    print(f"  {row[0]:<35} {row[1]:<20} {row[2]:>7,} stars  {row[3]:<15} readme={row[4]}")

print()
print("=== README quality scores (sample) ===")
rows = conn.execute("""
    SELECT repo_full_name, file_name, file_size, readme_quality_score
    FROM read_parquet('exports/documentation.parquet')
    WHERE file_name = 'README.md'
    ORDER BY readme_quality_score DESC
    LIMIT 10
""").fetchall()
for row in rows:
    bar = "█" * (row[3] // 10)
    print(f"  {row[0]:<45} score={row[2]:>3}  {bar}")

print()
print("=== Summary stats by language ===")
rows = conn.execute("""
    SELECT language, repo_count, ROUND(avg_stars) as avg_stars, max_stars
    FROM read_parquet('exports/summary_stats.parquet')
    ORDER BY repo_count DESC
""").fetchall()
for row in rows:
    print(f"  {str(row[0]):<15} {row[1]:>4} repos  avg_stars={int(row[2]):>6,}  max={row[3]:>7,}")

conn.close()