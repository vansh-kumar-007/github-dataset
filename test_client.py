# test_client.py
# We will delete this file after testing - it's just for learning

from scripts.crawler.github_client import GitHubClient

# Create our GitHub client object
client = GitHubClient()

# Check our rate limit first
client.check_rate_limit()

# Fetch real information about a famous Python repository
print("\nFetching repository info...")
data = client.get("/repos/psf/requests")

if data:
    print(f"Repository name : {data['name']}")
    print(f"Owner           : {data['owner']['login']}")
    print(f"Description     : {data['description']}")
    print(f"Stars           : {data['stargazers_count']:,}")
    print(f"Language        : {data['language']}")
    print(f"License         : {data['license']['name'] if data['license'] else 'None'}")
else:
    print("Something went wrong - check the logs")