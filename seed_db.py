import csv
import os
import sqlite3
from app.database import get_db, init_db
from app.models import AudioMetadata, Creator, Tag, UserInteraction

DATA_INPUT_DIR = "data.input"
ADDED_FILES_LOG = DATA_INPUT_DIR + "/added_files.log"


def load_added_files():
    if os.path.exists(ADDED_FILES_LOG):
        with open(ADDED_FILES_LOG, "r") as f:
            return set(f.read().splitlines())
    return set()


def log_added_file(filename):
    with open(ADDED_FILES_LOG, "a") as f:
        f.write(f"{filename}\n")


def process_csv_files():
    added_files = load_added_files()

    for filename in os.listdir(DATA_INPUT_DIR):
        if filename.endswith(".csv") and filename not in added_files:
            process_csv_file(os.path.join(DATA_INPUT_DIR, filename))
            log_added_file(filename)
            print(f"Processed and added: {filename}")


def process_csv_file(file_path):
    with open(file_path, "r", encoding="utf-8-sig") as csvfile:
        reader = csv.DictReader(csvfile)
        conn = get_db()
        cur = conn.cursor()

        for row in reader:
            # Insert audio metadata
            cur.execute(
                "INSERT OR REPLACE INTO audio_metadata (src_id, description, audio_src, location) VALUES (?, ?, ?, ?)",
                (row["Video_id"], row["Title"], row["Audio_url"], row["Location"]),
            )
            audio_id = cur.lastrowid

            # Insert images
            for image_url in row["Image_url"].split(","):
                cur.execute(
                    "INSERT INTO images (audio_id, image_url) VALUES (?, ?)",
                    (audio_id, image_url.strip()),
                )

            # Insert creators
            creator_ids = row["Creator_id"].split(",")
            for creator_id in creator_ids:
                cur.execute(
                    "INSERT OR IGNORE INTO creators (creator_id) VALUES (?)",
                    (creator_id.strip(),),
                )
                cur.execute(
                    "SELECT id FROM creators WHERE creator_id = ?",
                    (creator_id.strip(),),
                )
                creator_db_id = cur.fetchone()[0]
                cur.execute(
                    "INSERT OR IGNORE INTO audio_creators (audio_id, creator_id) VALUES (?, ?)",
                    (audio_id, creator_db_id),
                )

            # Insert tags
            tags = row["Tag"].split(",")
            for tag in tags:
                cur.execute(
                    "INSERT OR IGNORE INTO tags (name) VALUES (?)", (tag.strip(),)
                )
                cur.execute("SELECT id FROM tags WHERE name = ?", (tag.strip(),))
                tag_id = cur.fetchone()[0]
                cur.execute(
                    "INSERT OR IGNORE INTO audio_tags (audio_id, tag_id) VALUES (?, ?)",
                    (audio_id, tag_id),
                )

        conn.commit()
        conn.close()


# def seed_user_interactions():
#     db = get_db()
#     user_interactions = [
#         UserInteraction(
#             user_id="user1",
#             src_id="audio1",  # Changed from audio_id to src_id
#             is_fav=True,
#             viewed=True,
#             finished=False,
#             listened_second=300,
#             listened_percentage=0.5,
#             bookmarks=["1:30", "5:45"],
#             comments=["Great audio!"],
#             recommended=True,
#         ),
#         # ... more user interactions ...
#     ]
#     db.add_all(user_interactions)
#     db.commit()


if __name__ == "__main__":
    init_db()
    process_csv_files()
