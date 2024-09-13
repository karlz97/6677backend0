from typing import List
from app.models import AudioMetadata
from fastapi import HTTPException


def post_recommend_state_update(cur, user_id: str, src_ids: List[str]):
    for src_id in src_ids:
        cur.execute(
            """
            SELECT 1 FROM user_interactions WHERE user_id = ? AND src_id = ?
            """,
            (user_id, src_id),
        )
        exists = cur.fetchone()

        if exists:
            cur.execute(
                """
                UPDATE user_interactions
                SET recommended = ?
                WHERE user_id = ? AND src_id = ?
                """,
                (True, user_id, src_id),
            )
        else:
            cur.execute(
                """
                INSERT INTO user_interactions 
                (user_id, src_id, is_fav, viewed, finished, listened_second, listened_percentage, recommended)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (user_id, src_id, False, False, False, 0, 0.0, True),
            )


def no_recommended_state_update(
    cur,
    user_id: str,
):
    raise HTTPException(
        status_code=204,
        detail="Sorry, we have no applicable audio content available for you",
    )


def recommend_random(
    cur, user_id: str, limit: int, no_recommended: bool = False
) -> List[str]:
    query = """
        SELECT am.src_id FROM audio_metadata am
        LEFT JOIN user_interactions ui ON am.src_id = ui.src_id AND ui.user_id = ?
        WHERE ui.viewed IS NULL OR ui.viewed = 0
    """

    if no_recommended:
        query += " AND (ui.recommended IS NULL OR ui.recommended = 0)"

    query += """
        ORDER BY RANDOM()
        LIMIT ?
    """

    cur.execute(query, (user_id, limit))
    return [row["src_id"] for row in cur.fetchall()]


def recommend_by_tags(
    cur, user_id: str, tags: List[str], limit: int, no_recommended: bool = False
) -> List[str]:
    placeholders = ",".join(["?" for _ in tags])
    query = f"""
        SELECT am.src_id, COUNT(DISTINCT t.id) as tag_count
        FROM audio_metadata am
        JOIN audio_tags at ON am.src_id = at.src_id
        JOIN tags t ON at.tag_id = t.id
        LEFT JOIN user_interactions ui ON am.src_id = ui.src_id AND ui.user_id = ?
        WHERE t.name IN ({placeholders})
        AND (ui.viewed IS NULL OR ui.viewed = 0)
    """

    if no_recommended:
        query += " AND (ui.recommended IS NULL OR ui.recommended = 0)"

    query += """
        GROUP BY am.src_id
        ORDER BY tag_count DESC, RANDOM() 
        LIMIT ?
    """

    cur.execute(query, (user_id, *tags, limit))
    recommended = [row["src_id"] for row in cur.fetchall()]

    if len(recommended) < limit:
        additional = limit - len(recommended)
        random_recs = recommend_random(cur, user_id, additional, no_recommended)
        recommended.extend(random_recs)

    return recommended[:limit]


def fetch_audio_meta(cur, src_id: str):
    cur.execute(
        """
        SELECT am.*, GROUP_CONCAT(DISTINCT i.image_url) as images, 
               GROUP_CONCAT(DISTINCT t.name) as tags
        FROM audio_metadata am
        LEFT JOIN images i ON am.src_id = i.src_id
        LEFT JOIN audio_tags at ON am.src_id = at.src_id
        LEFT JOIN tags t ON at.tag_id = t.id
        WHERE am.src_id = ?
        GROUP BY am.src_id
    """,
        (src_id,),
    )
    result = cur.fetchone()
    if result:
        audio_meta = dict(result)
        audio_meta["images"] = (
            audio_meta["images"].split(",") if audio_meta["images"] else []
        )
        audio_meta["tags"] = audio_meta["tags"].split(",") if audio_meta["tags"] else []
        return audio_meta
    return None
