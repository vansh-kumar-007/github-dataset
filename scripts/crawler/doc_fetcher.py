# scripts/crawler/doc_fetcher.py
#
# Fetches documentation files for each repository.
# Now tracks all attempts so we never retry files we already checked.

import base64
from tqdm import tqdm
from scripts.crawler.github_client import GitHubClient
from scripts.database.db import (
    save_documentation,
    get_connection,
    record_fetch_attempt,
    was_fetch_attempted,
)
from scripts.utils.logger import logger
from config.settings import TARGET_FILES, DEPENDENCY_FILES


def fetch_file_content(client, repo_full_name, file_name):
    """
    Tries to fetch a single file from a repository.
    Returns the decoded text content, or None if not found.
    """
    endpoint = f"/repos/{repo_full_name}/contents/{file_name}"
    data = client.get(endpoint)

    if not data:
        return None

    if isinstance(data, dict) and data.get("encoding") == "base64":
        try:
            content = base64.b64decode(data["content"]).decode("utf-8")
            return content
        except Exception as e:
            logger.warning(f"Could not decode {file_name} for {repo_full_name}: {e}")
            return None

    return None


def get_all_repo_names():
    """Gets all repository names from the database."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT full_name FROM repositories ORDER BY stars DESC"
    ).fetchall()
    conn.close()
    return [row[0] for row in rows]


def run_doc_fetcher():
    """
    Fetches documentation files for all repositories.
    Skips any file we've already attempted, saving hours of API calls.
    """

    client = GitHubClient()
    client.check_rate_limit()

    repo_names = get_all_repo_names()
    logger.info(f"Fetching documentation for {len(repo_names)} repositories")

    all_target_files = TARGET_FILES + DEPENDENCY_FILES

    total_found    = 0
    total_missed   = 0
    total_skipped  = 0

    for repo_full_name in tqdm(repo_names, desc="Fetching docs", unit="repo"):

        for file_name in all_target_files:

            # Skip if we already attempted this file for this repo
            # This is the key improvement — saves hours on re-runs
            if was_fetch_attempted(repo_full_name, file_name):
                total_skipped += 1
                continue

            # Try to fetch the file
            content = fetch_file_content(client, repo_full_name, file_name)

            if content:
                save_documentation(repo_full_name, file_name, content)
                record_fetch_attempt(repo_full_name, file_name, found=True)
                total_found += 1
                logger.debug(f"Saved {file_name} for {repo_full_name}")
            else:
                # File not found — record this so we never try again
                record_fetch_attempt(repo_full_name, file_name, found=False)
                total_missed += 1

    logger.info(f"Documentation fetch complete")
    logger.info(f"Found: {total_found} | Not found: {total_missed} | Skipped (already tried): {total_skipped}")