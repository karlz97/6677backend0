from fastapi import APIRouter, HTTPException, Query
from app.models import AudioMetadata, UserInteraction
from app.database import get_db
from typing import List
from app.utils import (
    update_user_interactions,
    recommend_random,
    recommend_by_tags,
    fetch_audio_meta,
)

router = APIRouter()


@router.get("/recommend/{user_id}")
def get_recommend(
    user_id: str,
    tags: List[str] = Query(None),
    limit: int = 5,
    no_recommended: bool = False,
):
    conn = get_db()
    cur = conn.cursor()

    if tags:
        recommended = recommend_by_tags(cur, user_id, tags, limit, no_recommended)
    else:
        recommended = recommend_random(cur, user_id, limit, no_recommended)

    if not recommended:
        conn.close()
        raise HTTPException(
            status_code=404, detail="No applicable audio content available"
        )

    # Add UserInteraction entries for recommended audios
    update_user_interactions(cur, user_id, recommended)

    conn.commit()
    conn.close()
    return {"recommended": recommended}


@router.get("/recommend-full/{user_id}")
def get_recommend_full(
    user_id: str,
    tags: List[str] = Query(None),
    limit: int = 5,
    no_recommended: bool = False,
):
    conn = get_db()
    cur = conn.cursor()

    if tags:
        recommended_src_ids = recommend_by_tags(
            cur, user_id, tags, limit, no_recommended
        )
    else:
        recommended_src_ids = recommend_random(cur, user_id, limit, no_recommended)

    if not recommended_src_ids:
        conn.close()
        raise HTTPException(
            status_code=404, detail="No applicable audio content available"
        )

    recommended_full = []
    for src_id in recommended_src_ids:
        audio_meta = fetch_audio_meta(cur, src_id)
        if audio_meta:
            recommended_full.append(audio_meta)

    # Add UserInteraction entries for recommended audios
    update_user_interactions(cur, user_id, recommended_src_ids)

    conn.commit()
    conn.close()
    return recommended_full


@router.post("/user-interaction")
def update_user_interaction(interaction: UserInteraction):
    conn = get_db()
    cur = conn.cursor()

    # Update main user interaction
    cur.execute(
        """
        INSERT OR REPLACE INTO user_interactions 
        (user_id, src_id, is_fav, viewed, finished, listened_second, listened_percentage, recommended)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            interaction.user_id,
            interaction.src_id,
            interaction.is_fav,
            interaction.viewed,
            interaction.finished,
            interaction.listened_second,
            interaction.listened_percentage,
            interaction.recommended,
        ),
    )

    # Update bookmarks
    cur.execute(
        "DELETE FROM bookmarks WHERE user_id = ? AND src_id = ?",
        (interaction.user_id, interaction.src_id),
    )
    for bookmark in interaction.bookmarks:
        cur.execute(
            "INSERT INTO bookmarks (user_id, src_id, bookmark) VALUES (?, ?, ?)",
            (interaction.user_id, interaction.src_id, bookmark),
        )

    # Update comments
    cur.execute(
        "DELETE FROM comments WHERE user_id = ? AND src_id = ?",
        (interaction.user_id, interaction.src_id),
    )
    for comment in interaction.comments:
        cur.execute(
            "INSERT INTO comments (user_id, src_id, comment) VALUES (?, ?, ?)",
            (interaction.user_id, interaction.src_id, comment),
        )

    conn.commit()
    conn.close()
    return {"status": "success"}


@router.get("/audio-meta/{src_id}")
def get_audio_meta(src_id: str):
    conn = get_db()
    cur = conn.cursor()

    audio_meta = fetch_audio_meta(cur, src_id)
    conn.close()

    if audio_meta:
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
        LEFT JOIN bookmarks b ON ui.user_id = b.user_id AND ui.src_id = b.src_id
        LEFT JOIN comments c ON ui.user_id = c.user_id AND ui.src_id = c.src_id
        JOIN audio_metadata am ON ui.src_id = am.src_id
        WHERE am.src_id = ? AND ui.user_id = ?
        GROUP BY ui.user_id, ui.src_id
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
