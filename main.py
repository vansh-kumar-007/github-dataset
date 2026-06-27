# main.py
#
# This is the single entry point for the entire pipeline.
# Instead of running individual scripts separately, you run this
# one file and it handles everything in the correct order.
#
# Usage:
#   python main.py                        (uses defaults from .env)
#   python main.py --repos 500           (collect 500 repositories)
#   python main.py --repos 100 --no-docs (skip documentation fetching)

import argparse
from scripts.utils.logger import logger
from scripts.database.db import initialize_database, get_statistics
from scripts.crawler.repo_crawler import run_crawler
from scripts.crawler.doc_fetcher import run_doc_fetcher


def parse_arguments():
    """
    Reads optional command-line arguments so we can customize
    the pipeline without editing any code.

    For example:
        python main.py --repos 200
    This sets max_repos to 200 for this run only.
    """

    parser = argparse.ArgumentParser(
        description="GitHub Documentation Dataset Pipeline"
    )

    parser.add_argument(
        "--repos",
        type=int,
        default=None,
        help="Number of repositories to collect (default: from .env file)"
    )

    parser.add_argument(
        "--query",
        type=str,
        default=None,
        help="GitHub search query (default: stars:>50 is:public archived:false)"
    )

    parser.add_argument(
        "--no-docs",
        action="store_true",
        help="Skip fetching documentation files (only collect metadata)"
    )

    parser.add_argument(
        "--docs-only",
        action="store_true",
        help="Skip crawling and only fetch docs for repos already in database"
    )

    return parser.parse_args()


def print_banner():
    """Prints a simple banner when the pipeline starts."""
    print()
    print("=" * 60)
    print("   GitHub Documentation Dataset Pipeline")
    print("=" * 60)
    print()


def main():
    """
    The main function that runs the entire pipeline in order:
    1. Initialize the database
    2. Crawl GitHub for repository metadata
    3. Fetch documentation files for each repository
    4. Print final statistics
    """

    print_banner()
    args = parse_arguments()

    # Step 1: Make sure the database is ready
    logger.info("Step 1/3 — Initializing database")
    initialize_database()

    # Step 2: Crawl repositories (unless --docs-only was specified)
    if not args.docs_only:
        logger.info("Step 2/3 — Crawling GitHub for repositories")
        run_crawler(
            query=args.query,
            max_repos=args.repos,
        )
    else:
        logger.info("Step 2/3 — Skipping crawl (--docs-only mode)")

    # Step 3: Fetch documentation files (unless --no-docs was specified)
    if not args.no_docs:
        logger.info("Step 3/3 — Fetching documentation files")
        run_doc_fetcher()
    else:
        logger.info("Step 3/3 — Skipping documentation fetch (--no-docs mode)")

    # Final summary
    stats = get_statistics()
    print()
    print("=" * 60)
    print("   Pipeline Complete")
    print("=" * 60)
    print(f"   Repositories collected : {stats['repositories']:,}")
    print(f"   Documentation files    : {stats['documentation_files']:,}")
    print(f"   Completed entries      : {stats['completed']:,}")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()