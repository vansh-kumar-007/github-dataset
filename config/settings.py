# config/settings.py
#
# This file loads all our settings from the .env file
# and makes them available to every other part of the project.
#
# Think of this as the "control panel" for the entire pipeline.

import os
from dotenv import load_dotenv

# This line reads the .env file and loads everything in it
# into Python's environment so we can access it below
load_dotenv()

# --- GitHub API Settings ---

# Your secret GitHub token (loaded from .env, never typed directly here)
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# Base URL for the GitHub API - all our requests start with this
GITHUB_API_URL = "https://api.github.com"

# How many results to request per API call (max GitHub allows is 100)
PER_PAGE = 100

# How long to pause between requests so we don't upset GitHub (in seconds)
REQUEST_DELAY = float(os.getenv("REQUEST_DELAY", "1"))

# --- Collection Settings ---

# Maximum number of repositories to collect
MAX_REPOS = int(os.getenv("MAX_REPOS", "100"))

# Which documentation files to look for in each repository
TARGET_FILES = [
    "README.md",
    "LICENSE",
    "CONTRIBUTING.md",
    "CHANGELOG.md",
    "SECURITY.md",
    "CODE_OF_CONDUCT.md",
]

# Which dependency files to look for
DEPENDENCY_FILES = [
    "requirements.txt",
    "pyproject.toml",
    "package.json",
    "Cargo.toml",
    "pom.xml",
    "build.gradle",
    "go.mod",
    "Gemfile",
]

# --- Folder Paths ---
# These tell every part of our project where to save things

# The root folder of the project
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Where collected data gets saved
DATA_DIR = os.path.join(ROOT_DIR, "data")

# Where log files get saved
LOGS_DIR = os.path.join(ROOT_DIR, "logs")

# Where final Parquet exports go
EXPORTS_DIR = os.path.join(ROOT_DIR, "exports")