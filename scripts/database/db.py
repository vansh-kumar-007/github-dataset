# scripts/database/db.py
#
# This file handles everything related to our database.
# It creates the tables, saves data, and retrieves data.
#
# Think of this as the "filing cabinet manager" for our project.
# Every piece of data we collect gets filed here in an organized way.

import os
import duckdb
from scripts.utils.logger import logger
from config.settings import DATA_DIR

# The database will be stored as a single file in our data folder
DB_PATH = os.path.join(DATA_DIR, "github_dataset.duckdb")


def get_connection():
    """
    Opens a connection to our database file.
    Creates the file automatically if it doesn't exist yet.
    """
    os.makedirs(DATA_DIR, exist_ok=True)
    return duckdb.connect(DB_PATH)


def initialize_database():
    """
    Creates all the tables we need if they don't already exist.

    A 'table' is like a spreadsheet with named columns.
    Each row in the table will represent one GitHub repository.

    We use 'IF NOT EXISTS' so running this function multiple times
    is safe — it won't wipe out data we already collected.
    """

    conn = get_connection()
    logger.info("Initializing database...")

    # Table 1: Repository metadata
    # Stores the core information about each repository
    conn.execute("""
        CREATE TABLE IF NOT EXISTS repositories (
            id              INTEGER PRIMARY KEY,
            name            VARCHAR,
            owner           VARCHAR,
            full_name       VARCHAR UNIQUE,
            description     VARCHAR,
            stars           INTEGER,
            forks           INTEGER,
            language        VARCHAR,
            license         VARCHAR,
            created_at      VARCHAR,
            updated_at      VARCHAR,
            topics          VARCHAR,
            archived        BOOLEAN,
            repo_url        VARCHAR,
            collected_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Table 2: Documentation files
    # Stores the actual content of README, LICENSE, etc.
    # We use SEQUENCE to auto-generate a unique id for each row
    conn.execute("CREATE SEQUENCE IF NOT EXISTS doc_id_seq START 1")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS documentation (
            id              INTEGER PRIMARY KEY DEFAULT nextval('doc_id_seq'),
            repo_full_name  VARCHAR,
            file_name       VARCHAR,
            content         VARCHAR,
            file_size       INTEGER,
            collected_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Table 3: Collection progress
    # Tracks which repositories we've already processed
    # This is what makes our pipeline resumable
    conn.execute("""
        CREATE TABLE IF NOT EXISTS progress (
            repo_full_name  VARCHAR PRIMARY KEY,
            status          VARCHAR,
            processed_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.close()
    logger.info(f"Database ready at: {DB_PATH}")


def is_already_collected(repo_full_name):
    """
    Checks whether we've already collected a specific repository.
    This prevents us from downloading the same repo twice
    if we stop and restart the pipeline.

    Returns True if already collected, False if not.
    """

    conn = get_connection()
    result = conn.execute(
        "SELECT COUNT(*) FROM progress WHERE repo_full_name = ? AND status = 'done'",
        [repo_full_name]
    ).fetchone()
    conn.close()

    return result[0] > 0


def save_repository(repo_data):
    """
    Saves one repository's metadata to the database.

    repo_data is a dictionary with all the fields we collected.
    We use INSERT OR REPLACE so re-running the pipeline updates
    existing records instead of causing an error.
    """

    conn = get_connection()

    try:
        conn.execute("""
            INSERT INTO repositories
            (id, name, owner, full_name, description, stars, forks,
             language, license, created_at, updated_at, topics, archived, repo_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (full_name) DO UPDATE SET
                stars      = EXCLUDED.stars,
                forks      = EXCLUDED.forks,
                updated_at = EXCLUDED.updated_at,
                topics     = EXCLUDED.topics,
                archived   = EXCLUDED.archived
        """, [
            repo_data["id"],
            repo_data["name"],
            repo_data["owner"],
            repo_data["full_name"],
            repo_data["description"],
            repo_data["stars"],
            repo_data["forks"],
            repo_data["language"],
            repo_data["license"],
            repo_data["created_at"],
            repo_data["updated_at"],
            repo_data["topics"],
            repo_data["archived"],
            repo_data["repo_url"],
        ])

        # Mark this repository as done in our progress tracker
        conn.execute("""
            INSERT OR REPLACE INTO progress (repo_full_name, status)
            VALUES (?, 'done')
        """, [repo_data["full_name"]])

        conn.close()
        return True

    except Exception as e:
        logger.error(f"Failed to save repository {repo_data.get('full_name')}: {e}")
        conn.close()
        return False


def save_documentation(repo_full_name, file_name, content):
    """
    Saves the content of one documentation file to the database.
    For example: the README.md content of a specific repository.
    """

    conn = get_connection()

    try:
        conn.execute("""
            INSERT INTO documentation (id, repo_full_name, file_name, content, file_size)
            VALUES (nextval('doc_id_seq'), ?, ?, ?, ?)
        """, [repo_full_name, file_name, content, len(content)])

        conn.close()
        return True

    except Exception as e:
        logger.error(f"Failed to save {file_name} for {repo_full_name}: {e}")
        conn.close()
        return False


def get_statistics():
    """
    Returns a quick summary of how much data we've collected so far.
    Useful for checking progress during a long collection run.
    """

    conn = get_connection()

    repos = conn.execute("SELECT COUNT(*) FROM repositories").fetchone()[0]
    docs  = conn.execute("SELECT COUNT(*) FROM documentation").fetchone()[0]
    done  = conn.execute("SELECT COUNT(*) FROM progress WHERE status = 'done'").fetchone()[0]

    conn.close()

    return {"repositories": repos, "documentation_files": docs, "completed": done}