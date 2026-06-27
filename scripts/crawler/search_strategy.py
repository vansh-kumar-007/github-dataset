# scripts/crawler/search_strategy.py
#
# This module builds and manages our search strategy.
# Instead of one big search that returns biased results,
# we generate many small targeted searches that together
# produce a diverse, balanced dataset.

from config.settings import SEARCH_LANGUAGES, STAR_RANGES
from scripts.utils.logger import logger


def build_search_queries():
    """
    Generates a list of targeted search queries by combining
    every language with every star range.

    For example, combining "Python" with (100, 500) produces:
    "language:Python stars:100..500 is:public archived:false"

    Returns a list of (query_string, label) tuples.
    """

    queries = []

    for language in SEARCH_LANGUAGES:
        for (min_stars, max_stars, tier) in STAR_RANGES:

            # GitHub's star range syntax uses ".." between two numbers
            query = (
                f"language:{language} "
                f"stars:{min_stars}..{max_stars} "
                f"is:public "
                f"archived:false"
            )

            # A human-readable label for logging
            label = f"{language}_{tier}"

            queries.append((query, label))

    logger.info(f"Built {len(queries)} search queries across "
                f"{len(SEARCH_LANGUAGES)} languages and "
                f"{len(STAR_RANGES)} star tiers")

    return queries


def calculate_target_per_query(total_target, queries):
    """
    Divides our total repository target evenly across all queries.

    For example, if we want 10,000 repos total and have 60 queries,
    each query should collect about 166 repositories.

    We cap at 900 per query because GitHub's search API
    only returns 1,000 results maximum per query, and
    we want to stay safely below that limit.

    Returns the number of repos to collect per query.
    """

    per_query = total_target // len(queries)

    # Never ask for more than 900 per query (safe margin under 1,000 limit)
    per_query = min(per_query, 900)

    # Always collect at least 10 per query
    per_query = max(per_query, 10)

    logger.info(f"Target: {total_target} repos total — "
                f"{per_query} per query across {len(queries)} queries")

    return per_query