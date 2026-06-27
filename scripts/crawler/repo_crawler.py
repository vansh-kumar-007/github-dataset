# scripts/crawler/repo_crawler.py
#
# This is the main crawler — the engine that searches GitHub
# for repositories and saves their metadata to our database.
#
# It works like a systematic librarian:
# 1. Ask GitHub for a page of matching repositories
# 2. Save each one to the database
# 3. Ask for the next page
# 4. Repeat until we have enough

from tqdm import tqdm
from scripts.crawler.github_client import GitHubClient
from scripts.database.db import (
    initialize_database,
    is_already_collected,
    save_repository,
    get_statistics,
)
from scripts.utils.logger import logger
from config.settings import MAX_REPOS, PER_PAGE


def parse_repo(raw):
    """
    Takes the raw JSON data GitHub sends us for one repository
    and extracts only the fields we care about.

    GitHub sends back 80+ fields per repository — most of which
    we don't need. This function picks out just the useful ones
    and organizes them cleanly.
    """

    # Extract the license name safely
    # Some repositories have no license, so we check first
    license_name = None
    if raw.get("license") and raw["license"].get("name"):
        license_name = raw["license"]["name"]

    # Topics are returned as a list — we join them into a
    # comma-separated string so they fit neatly in one database cell
    # Example: ["python", "api", "web"] becomes "python,api,web"
    topics = ",".join(raw.get("topics", []))

    return {
        "id":           raw["id"],
        "name":         raw["name"],
        "owner":        raw["owner"]["login"],
        "full_name":    raw["full_name"],
        "description":  raw.get("description"),
        "stars":        raw["stargazers_count"],
        "forks":        raw["forks_count"],
        "language":     raw.get("language"),
        "license":      license_name,
        "created_at":   raw["created_at"],
        "updated_at":   raw["updated_at"],
        "topics":       topics,
        "archived":     raw["archived"],
        "repo_url":     raw["html_url"],
    }


def search_repositories(client, query, page):
    """
    Asks GitHub for one page of search results.

    Arguments:
        client: our GitHubClient object
        query:  the search string, e.g. "stars:>100 language:python"
        page:   which page of results to fetch (starts at 1)

    Returns:
        A list of raw repository dictionaries from GitHub,
        or an empty list if something went wrong.
    """

    logger.info(f"Fetching page {page} of search results...")

    data = client.get("/search/repositories", params={
        "q":        query,
        "sort":     "stars",
        "order":    "desc",
        "per_page": PER_PAGE,
        "page":     page,
    })

    if not data:
        logger.warning(f"No data returned for page {page}")
        return []

    items = data.get("items", [])
    logger.info(f"Got {len(items)} repositories from page {page}")
    return items


def run_crawler(query=None, max_repos=None):
    """
    The main function that runs the entire crawling process.

    Arguments:
        query:     what to search for on GitHub
                   defaults to popular, non-archived repositories
        max_repos: how many repositories to collect
                   defaults to the value in our .env file
    """

    # Use defaults from settings if not specified
    if max_repos is None:
        max_repos = MAX_REPOS

    # Default search query if none provided:
    # - stars:>50 means at least 50 stars (filters out empty/toy repos)
    # - is:public means only public repositories
    # - archived:false means skip archived repositories
    if query is None:
        query = "stars:>50 is:public archived:false"

    # Make sure the database tables exist before we start writing
    initialize_database()

    # Create our GitHub API client
    client = GitHubClient()

    # Check how many API requests we have left before starting
    client.check_rate_limit()

    logger.info(f"Starting crawler — target: {max_repos} repositories")
    logger.info(f"Search query: {query}")

    # Counters to track our progress
    collected = 0
    skipped   = 0
    page      = 1

    # tqdm creates the progress bar you'll see in the terminal
    # It shows how many repos we've collected out of our target
    progress_bar = tqdm(total=max_repos, desc="Collecting repos", unit="repo")

    # Keep fetching pages until we have enough repositories
    while collected < max_repos:

        # Fetch one page of results from GitHub
        items = search_repositories(client, query, page)

        # If GitHub returned nothing, we've run out of results
        if not items:
            logger.info("No more results from GitHub — stopping")
            break

        # Process each repository on this page
        for raw_repo in items:

            # Stop if we've reached our target
            if collected >= max_repos:
                break

            full_name = raw_repo["full_name"]

            # Skip if we already collected this repository
            # This is what makes the pipeline resumable
            if is_already_collected(full_name):
                logger.debug(f"Already collected: {full_name} — skipping")
                skipped += 1
                continue

            # Extract just the fields we need
            repo = parse_repo(raw_repo)

            # Save to the database
            if save_repository(repo):
                collected += 1
                progress_bar.update(1)
                logger.debug(f"Saved: {full_name} ({repo['stars']:,} stars)")
            else:
                logger.warning(f"Failed to save: {full_name}")

        # Move to the next page
        page += 1

        # GitHub Search API hard limit — never go past page 10
        # (10 pages × 100 results = 1,000 maximum)
        if page > 10:
            logger.info("Reached GitHub search limit of 1,000 results")
            break

    progress_bar.close()

    # Print a final summary
    stats = get_statistics()
    logger.info(f"Crawl complete — collected: {collected}, skipped: {skipped}")
    logger.info(f"Database totals: {stats}")