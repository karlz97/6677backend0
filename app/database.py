import sqlite3
from sqlite3 import Connection

DATABASE_NAME = "audio_app.db"


def get_db() -> Connection:
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()

    # Audio metadata table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS audio_metadata (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            src_id TEXT UNIQUE NOT NULL,
            description TEXT,
            audio_src TEXT,
            location TEXT
        )
    """
    )

    # Creators table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS creators (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            creator_id TEXT UNIQUE NOT NULL
        )
    """
    )

    # Tags table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    """
    )

    # Images table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            audio_id INTEGER,
            image_url TEXT,
            FOREIGN KEY (audio_id) REFERENCES audio_metadata (id)
        )
    """
    )

    # Audio-Creator relationship table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS audio_creators (
            audio_id INTEGER,
            creator_id INTEGER,
            PRIMARY KEY (audio_id, creator_id),
            FOREIGN KEY (audio_id) REFERENCES audio_metadata (id),
            FOREIGN KEY (creator_id) REFERENCES creators (id)
        )
    """
    )

    # Audio-Tag relationship table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS audio_tags (
            audio_id INTEGER,
            tag_id INTEGER,
            PRIMARY KEY (audio_id, tag_id),
            FOREIGN KEY (audio_id) REFERENCES audio_metadata (id),
            FOREIGN KEY (tag_id) REFERENCES tags (id)
        )
    """
    )

    # Updated User interactions table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS user_interactions (
            user_id TEXT,
            audio_id INTEGER,
            is_fav BOOLEAN,
            viewed BOOLEAN,
            finished BOOLEAN,
            listened_second INTEGER,
            listened_percentage REAL,
            PRIMARY KEY (user_id, audio_id),
            FOREIGN KEY (audio_id) REFERENCES audio_metadata (id)
        )
    """
    )

    # New table for bookmarks
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS bookmarks (
            user_id TEXT,
            audio_id INTEGER,
            bookmark TEXT,
            PRIMARY KEY (user_id, audio_id, bookmark),
            FOREIGN KEY (user_id, audio_id) REFERENCES user_interactions (user_id, audio_id)
        )
    """
    )

    # New table for comments
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS comments (
            user_id TEXT,
            audio_id INTEGER,
            comment TEXT,
            PRIMARY KEY (user_id, audio_id, comment),
            FOREIGN KEY (user_id, audio_id) REFERENCES user_interactions (user_id, audio_id)
        )
    """
    )

    conn.commit()
    conn.close()
