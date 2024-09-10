from fastapi import APIRouter, HTTPException
from app.models import AudioMetadata, UserInteraction
from app.database import get_db
from typing import List
import json

router = APIRouter()


@router.get("/recommend/{user_id}")
def get_recommend(user_id: str, tags: List[str] = None, limit: int = 5):
    conn = get_db()
    cur = conn.cursor()

    if tags:
        recommended = recommend_by_tags(cur, user_id, tags, limit)
    else:
        recommended = recommend_random(cur, user_id, limit)

    conn.close()
    return {"recommended": recommended}


def recommend_random(cur, user_id: str, limit: int) -> List[str]:
    cur.execute(
        """
        SELECT am.src_id FROM audio_metadata am
        WHERE am.id NOT IN (
            SELECT ui.audio_id FROM user_interactions ui
            WHERE ui.user_id = ? AND ui.viewed = 1
        )
        ORDER BY RANDOM()
        LIMIT ?
    """,
        (user_id, limit),
    )
    return [row["src_id"] for row in cur.fetchall()]


def recommend_by_tags(cur, user_id: str, tags: List[str], limit: int) -> List[str]:
    placeholders = ",".join(["?" for _ in tags])
    cur.execute(
        f"""
        SELECT am.src_id, COUNT(DISTINCT t.id) as tag_count
        FROM audio_metadata am
        JOIN audio_tags at ON am.id = at.audio_id
        JOIN tags t ON at.tag_id = t.id
        WHERE t.name IN ({placeholders})
        AND am.id NOT IN (
            SELECT ui.audio_id FROM user_interactions ui
            WHERE ui.user_id = ? AND ui.viewed = 1
        )
        GROUP BY am.id
        ORDER BY tag_count DESC, RANDOM()
        LIMIT ?
    """,
        (*tags, user_id, limit),
    )

    recommended = [row["src_id"] for row in cur.fetchall()]

    if len(recommended) < limit:
        additional = limit - len(recommended)
        random_recs = recommend_random(cur, user_id, additional)
        recommended.extend(random_recs)

    return recommended[:limit]


@router.post("/user-interaction")
def update_user_interaction(interaction: UserInteraction):
    conn = get_db()
    cur = conn.cursor()

    # Update main user interaction
    cur.execute(
        """
        INSERT OR REPLACE INTO user_interactions 
        (user_id, audio_id, is_fav, viewed, finished, listened_second, listened_percentage)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
        (
            interaction.user_id,
            interaction.audio_id,
            interaction.is_fav,
            interaction.viewed,
            interaction.finished,
            interaction.listened_second,
            interaction.listened_percentage,
        ),
    )

    # Update bookmarks
    cur.execute(
        "DELETE FROM bookmarks WHERE user_id = ? AND audio_id = ?",
        (interaction.user_id, interaction.audio_id),
    )
    for bookmark in interaction.bookmarks:
        cur.execute(
            "INSERT INTO bookmarks (user_id, audio_id, bookmark) VALUES (?, ?, ?)",
            (interaction.user_id, interaction.audio_id, bookmark),
        )

    # Update comments
    cur.execute(
        "DELETE FROM comments WHERE user_id = ? AND audio_id = ?",
        (interaction.user_id, interaction.audio_id),
    )
    for comment in interaction.comments:
        cur.execute(
            "INSERT INTO comments (user_id, audio_id, comment) VALUES (?, ?, ?)",
            (interaction.user_id, interaction.audio_id, comment),
        )

    conn.commit()
    conn.close()
    return {"status": "success"}


@router.get("/audio-meta/{src_id}")
def get_audio_meta(src_id: str):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT am.*, GROUP_CONCAT(DISTINCT i.image_url) as images, 
               GROUP_CONCAT(DISTINCT c.creator_id) as creators,
               GROUP_CONCAT(DISTINCT t.name) as tags
        FROM audio_metadata am
        LEFT JOIN images i ON am.id = i.audio_id
        LEFT JOIN audio_creators ac ON am.id = ac.audio_id
        LEFT JOIN creators c ON ac.creator_id = c.id
        LEFT JOIN audio_tags at ON am.id = at.audio_id
        LEFT JOIN tags t ON at.tag_id = t.id
        WHERE am.src_id = ?
        GROUP BY am.id
    """,
        (src_id,),
    )

    result = cur.fetchone()
    conn.close()

    if result:
        audio_meta = dict(result)
        audio_meta["images"] = (
            audio_meta["images"].split(",") if audio_meta["images"] else []
        )
        audio_meta["creators"] = (
            audio_meta["creators"].split(",") if audio_meta["creators"] else []
        )
        audio_meta["tags"] = audio_meta["tags"].split(",") if audio_meta["tags"] else []
        return audio_meta
    raise HTTPException(status_code=404, detail="Audio metadata not found")


@router.get("/user-interaction/{src_id}/{user_id}")
def get_user_interaction(src_id: str, user_id: str):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT ui.*, GROUP_CONCAT(DISTINCT b.bookmark) as bookmarks, 
               GROUP_CONCAT(DISTINCT c.comment) as comments
        FROM user_interactions ui
        LEFT JOIN bookmarks b ON ui.user_id = b.user_id AND ui.audio_id = b.audio_id
        LEFT JOIN comments c ON ui.user_id = c.user_id AND ui.audio_id = c.audio_id
        JOIN audio_metadata am ON ui.audio_id = am.id
        WHERE am.src_id = ? AND ui.user_id = ?
        GROUP BY ui.user_id, ui.audio_id
    """,
        (src_id, user_id),
    )

    result = cur.fetchone()
    conn.close()

    if result:
        interaction = dict(result)
        interaction["bookmarks"] = (
            interaction["bookmarks"].split(",") if interaction["bookmarks"] else []
        )
        interaction["comments"] = (
            interaction["comments"].split(",") if interaction["comments"] else []
        )
        return interaction
    raise HTTPException(status_code=404, detail="User interaction not found")


@router.post("/add-audio-meta")
def add_audio_meta(audio: AudioMetadata):
    conn = get_db()
    cur = conn.cursor()

    # Insert audio metadata
    cur.execute(
        """
        INSERT OR REPLACE INTO audio_metadata (src_id, description, audio_src, location)
        VALUES (?, ?, ?, ?)
    """,
        (audio.src_id, audio.description, audio.audio_src, audio.location),
    )
    audio_id = cur.lastrowid

    # Insert images
    for image_url in audio.images:
        cur.execute(
            "INSERT INTO images (audio_id, image_url) VALUES (?, ?)",
            (audio_id, image_url),
        )

    # Insert creators
    for creator_id in audio.creators:
        cur.execute(
            "INSERT OR IGNORE INTO creators (creator_id) VALUES (?)", (creator_id,)
        )
        cur.execute("SELECT id FROM creators WHERE creator_id = ?", (creator_id,))
        creator_db_id = cur.fetchone()[0]
        cur.execute(
            "INSERT OR IGNORE INTO audio_creators (audio_id, creator_id) VALUES (?, ?)",
            (audio_id, creator_db_id),
        )

    # Insert tags
    for tag in audio.tags:
        cur.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (tag,))
        cur.execute("SELECT id FROM tags WHERE name = ?", (tag,))
        tag_id = cur.fetchone()[0]
        cur.execute(
            "INSERT OR IGNORE INTO audio_tags (audio_id, tag_id) VALUES (?, ?)",
            (audio_id, tag_id),
        )

    conn.commit()
    conn.close()
    return {"status": "success"}
