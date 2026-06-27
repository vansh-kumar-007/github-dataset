# scripts/crawler/github_client.py
#
# This file is responsible for all communication with the GitHub API.
# Think of it as our "translator" that knows how to talk to GitHub.
#
# Every other part of our project that needs GitHub data
# will use this file instead of talking to GitHub directly.
# This keeps things organized and easy to fix if GitHub ever
# changes how their API works.

import time
import requests
from scripts.utils.logger import logger
from config.settings import GITHUB_TOKEN, GITHUB_API_URL, REQUEST_DELAY


class GitHubClient:
    """
    A class that wraps the GitHub REST API.

    A 'class' is like a blueprint. We create one GitHubClient object
    and then use it throughout the project to make all our API calls.
    """

    def __init__(self):
        """
        This runs automatically when we create a GitHubClient object.
        It sets up the headers that get sent with every request.
        """

        # Headers are extra information we attach to every request
        # They tell GitHub who we are and what format we want data in
        self.headers = {
            # This is how we prove our identity to GitHub
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            # This tells GitHub we want the latest version of their API
            "Accept": "application/vnd.github+json",
            # GitHub wants to know what software is making requests
            "User-Agent": "github-dataset-pipeline/1.0",
        }

        # Store the base URL so we don't have to repeat it everywhere
        self.base_url = GITHUB_API_URL

        # Log that we initialized successfully
        logger.info("GitHub client initialized")

    def get(self, endpoint, params=None):
        """
        Makes a single GET request to the GitHub API.

        A GET request means: "please give me this data" (read only).
        We never modify anything on GitHub — we only read.

        Arguments:
            endpoint: the specific API path, e.g. "/repos/python/cpython"
            params:   optional filters, e.g. {"per_page": 100, "page": 2}

        Returns:
            The response data as a Python dictionary, or None if it failed.
        """

        # Build the full URL by combining base URL and the endpoint
        url = f"{self.base_url}{endpoint}"

        try:
            # Make the actual request to GitHub
            response = requests.get(url, headers=self.headers, params=params, timeout=30)

            # Pause after every request so we don't overwhelm GitHub
            # This is called "rate limit courtesy" — good API citizenship
            time.sleep(REQUEST_DELAY)

            # Check if GitHub returned an error
            if response.status_code == 200:
                # 200 means "success" — return the data
                return response.json()

            elif response.status_code == 403:
                # 403 means we've hit the rate limit — we're asking too fast
                logger.warning(f"Rate limit hit on {endpoint}. Waiting 60 seconds...")
                time.sleep(60)
                return None

            elif response.status_code == 404:
                # 404 means "not found" — the repository or file doesn't exist
                logger.debug(f"Not found: {endpoint}")
                return None

            else:
                # Something else went wrong
                logger.error(f"Unexpected status {response.status_code} for {endpoint}")
                return None

        except requests.exceptions.Timeout:
            # The request took too long and gave up
            logger.error(f"Request timed out: {endpoint}")
            return None

        except requests.exceptions.ConnectionError:
            # No internet connection or GitHub is unreachable
            logger.error(f"Connection error: {endpoint}")
            return None

    def check_rate_limit(self):
        """
        Asks GitHub how many API requests we have remaining.

        GitHub allows 5,000 requests per hour with a token.
        This lets us check how many we've used and how many remain.
        """

        data = self.get("/rate_limit")

        if data:
            core = data["resources"]["core"]
            remaining = core["remaining"]
            limit = core["limit"]
            logger.info(f"API rate limit: {remaining}/{limit} requests remaining")
            return remaining

        return None