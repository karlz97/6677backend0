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
            src_id TEXT,
            image_url TEXT,
            FOREIGN KEY (src_id) REFERENCES audio_metadata (src_id)
        )
    """
    )

    # Audio-Creator relationship table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS audio_creators (
            src_id TEXT,
            creator_id INTEGER,
            PRIMARY KEY (src_id, creator_id),
            FOREIGN KEY (src_id) REFERENCES audio_metadata (src_id),
            FOREIGN KEY (creator_id) REFERENCES creators (id)
        )
    """
    )

    # Audio-Tag relationship table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS audio_tags (
            src_id TEXT,
            tag_id INTEGER,
            PRIMARY KEY (src_id, tag_id),
            FOREIGN KEY (src_id) REFERENCES audio_metadata (src_id),
            FOREIGN KEY (tag_id) REFERENCES tags (id)
        )
    """
    )

    # Updated User interactions table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS user_interactions (
            user_id TEXT,
            src_id TEXT,
            is_fav BOOLEAN,
            viewed BOOLEAN,
            finished BOOLEAN,
            listened_second INTEGER,
            listened_percentage REAL,
            recommended BOOLEAN,  
            PRIMARY KEY (user_id, src_id),
            FOREIGN KEY (src_id) REFERENCES audio_metadata (src_id)
        )
    """
    )

    # New table for bookmarks
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS bookmarks (
            user_id TEXT,
            src_id TEXT,
            bookmark TEXT,
            PRIMARY KEY (user_id, src_id, bookmark),
            FOREIGN KEY (user_id, src_id) REFERENCES user_interactions (user_id, src_id)
        )
    """
    )

    # New table for comments
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS comments (
            user_id TEXT,
            src_id TEXT,
            comment TEXT,
            PRIMARY KEY (user_id, src_id, comment),
            FOREIGN KEY (user_id, src_id) REFERENCES user_interactions (user_id, src_id)
        )
    """
    )

    conn.commit()
    conn.close()
