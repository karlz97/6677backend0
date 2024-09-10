from typing import List
from app.models import AudioMetadata


def update_user_interactions(cur, user_id: str, src_ids: List[str]):
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


def recommend_random(cur, user_id: str, limit: int) -> List[str]:
    cur.execute(
        """
        SELECT am.src_id FROM audio_metadata am
        WHERE am.src_id NOT IN (
            SELECT ui.src_id FROM user_interactions ui
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
        AND am.src_id NOT IN (
            SELECT ui.src_id FROM user_interactions ui
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


def fetch_audio_meta(cur, src_id: str):
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
    return None
