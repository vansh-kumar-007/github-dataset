# scripts/crawler/doc_fetcher.py
#
# This file is responsible for fetching documentation files
# from each repository we've already collected.
#
# For each repository in our database, it tries to download
# each of our target files (README.md, LICENSE, etc.)
# and saves the content to the documentation table.

import base64
import duckdb
import os
from tqdm import tqdm
from scripts.crawler.github_client import GitHubClient
from scripts.database.db import save_documentation, get_connection
from scripts.utils.logger import logger
from config.settings import TARGET_FILES, DEPENDENCY_FILES


def fetch_file_content(client, repo_full_name, file_name):
    """
    Tries to fetch a single file from a repository.

    Arguments:
        client:         our GitHubClient object
        repo_full_name: e.g. "freeCodeCamp/freeCodeCamp"
        file_name:      e.g. "README.md"

    Returns:
        The decoded text content of the file,
        or None if the file doesn't exist or fetch failed.
    """

    endpoint = f"/repos/{repo_full_name}/contents/{file_name}"
    data = client.get(endpoint)

    if not data:
        # File doesn't exist in this repository — that's normal
        return None

    # GitHub sends file content encoded in base64
    # We need to decode it back to readable text
    if isinstance(data, dict) and data.get("encoding") == "base64":
        try:
            # base64.b64decode converts from base64 back to bytes
            # .decode("utf-8") converts bytes to a normal Python string
            content = base64.b64decode(data["content"]).decode("utf-8")
            return content
        except Exception as e:
            logger.warning(f"Could not decode {file_name} for {repo_full_name}: {e}")
            return None

    return None


def is_doc_already_fetched(repo_full_name, file_name):
    """
    Checks if we already fetched a specific file for a specific repo.
    Prevents downloading the same file twice if we restart the pipeline.
    """

    conn = get_connection()
    result = conn.execute(
        """SELECT COUNT(*) FROM documentation
           WHERE repo_full_name = ? AND file_name = ?""",
        [repo_full_name, file_name]
    ).fetchone()
    conn.close()
    return result[0] > 0


def get_all_repo_names():
    """
    Retrieves the full_name of every repository in our database.
    These are the repositories we'll fetch documentation for.
    """

    conn = get_connection()
    rows = conn.execute(
        "SELECT full_name FROM repositories ORDER BY stars DESC"
    ).fetchall()
    conn.close()

    # fetchall() returns a list of tuples like [("owner/repo",), ...]
    # We extract just the string from each tuple
    return [row[0] for row in rows]


def run_doc_fetcher():
    """
    Main function that fetches documentation files for all
    repositories currently in our database.

    For each repository:
      - Try to download each target documentation file
      - Try to download each dependency file
      - Save any found files to the documentation table
      - Skip files we've already downloaded
    """

    client = GitHubClient()
    client.check_rate_limit()

    # Get list of all repositories we need to process
    repo_names = get_all_repo_names()
    logger.info(f"Fetching documentation for {len(repo_names)} repositories")

    # Combine documentation and dependency files into one list
    all_target_files = TARGET_FILES + DEPENDENCY_FILES

    # Track overall statistics
    total_found  = 0
    total_missed = 0

    # Loop through every repository with a progress bar
    for repo_full_name in tqdm(repo_names, desc="Fetching docs", unit="repo"):

        logger.debug(f"Processing: {repo_full_name}")
        repo_found = 0

        # Try to fetch each target file for this repository
        for file_name in all_target_files:

            # Skip if we already have this file
            if is_doc_already_fetched(repo_full_name, file_name):
                logger.debug(f"Already have {file_name} for {repo_full_name}")
                continue

            # Try to fetch the file from GitHub
            content = fetch_file_content(client, repo_full_name, file_name)

            if content:
                # File exists — save it to the database
                save_documentation(repo_full_name, file_name, content)
                repo_found += 1
                total_found += 1
                logger.debug(f"Saved {file_name} ({len(content):,} chars) for {repo_full_name}")
            else:
                # File doesn't exist in this repo — perfectly normal
                total_missed += 1

        logger.debug(f"Found {repo_found}/{len(all_target_files)} files for {repo_full_name}")

    logger.info(f"Documentation fetch complete")
    logger.info(f"Files saved: {total_found} | Not found: {total_missed}")