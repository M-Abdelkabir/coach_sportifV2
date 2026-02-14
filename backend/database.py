"""
SQLite database management for Virtual Sports Coach.
Uses aiosqlite for async operations with FastAPI.
"""
import aiosqlite
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

# Database file path
DB_PATH = Path(__file__).parent / "coach.db"


async def init_db():
    """Initialize the database with required tables."""
    async with aiosqlite.connect(DB_PATH) as db:
        # Users table - stores profiles and calibration data
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                ratios_json TEXT,
                thresholds_json TEXT,
                body_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Sessions table - stores workout history
        await db.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                exercise TEXT NOT NULL,
                reps INTEGER DEFAULT 0,
                sets INTEGER DEFAULT 0,
                calories_est REAL DEFAULT 0.0,
                fatigue_score REAL DEFAULT 0.0,
                duration INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # Create index for faster user_id lookups
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_sessions_user_id 
            ON sessions(user_id)
        """)
        
        await db.commit()
        print(f"[DB] Initialized database at {DB_PATH}")


# ==================== User Operations ====================

async def create_user(name: str, user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Create a new user profile.
    
    Args:
        name: User's display name
        user_id: Optional specific ID (otherwise generated)
        
    Returns:
        Dictionary with user data including generated ID
    """
    if user_id is None:
        user_id = str(uuid.uuid4())[:8]  # Short UUID for simplicity
    created_at = datetime.now()
    
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO users (id, name, created_at)
            VALUES (?, ?, ?)
            """,
            (user_id, name, created_at)
        )
        await db.commit()
    
    print(f"[DB] Created user: {user_id} - {name}")
    return {
        "id": user_id,
        "name": name,
        "ratios": None,
        "thresholds": None,
        "body_type": None,
        "created_at": created_at
    }


async def get_user(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get user profile by ID.
    
    Args:
        user_id: User's unique identifier
        
    Returns:
        User data dictionary or None if not found
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM users WHERE id = ?",
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            
    if row is None:
        return None
    
    return {
        "id": row["id"],
        "name": row["name"],
        "ratios": json.loads(row["ratios_json"]) if row["ratios_json"] else None,
        "thresholds": json.loads(row["thresholds_json"]) if row["thresholds_json"] else None,
        "body_type": row["body_type"],
        "created_at": row["created_at"]
    }


async def update_user(
    user_id: str,
    name: Optional[str] = None,
    ratios: Optional[Dict] = None,
    thresholds: Optional[Dict] = None,
    body_type: Optional[str] = None
) -> bool:
    """
    Update user profile data.
    
    Args:
        user_id: User's unique identifier
        name: New name (optional)
        ratios: Body ratios from calibration (optional)
        thresholds: Exercise thresholds (optional)
        body_type: Body type classification (optional)
        
    Returns:
        True if update successful, False if user not found
    """
    # Build dynamic update query
    updates = []
    params = []
    
    if name is not None:
        updates.append("name = ?")
        params.append(name)
    if ratios is not None:
        updates.append("ratios_json = ?")
        params.append(json.dumps(ratios))
    if thresholds is not None:
        updates.append("thresholds_json = ?")
        params.append(json.dumps(thresholds))
    if body_type is not None:
        updates.append("body_type = ?")
        params.append(body_type)
    
    if not updates:
        return True  # Nothing to update
    
    params.append(user_id)
    query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
    
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(query, params)
        await db.commit()
        
        if cursor.rowcount == 0:
            return False
    
    print(f"[DB] Updated user: {user_id}")
    return True


async def get_all_users() -> List[Dict[str, Any]]:
    """Get all user profiles."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users ORDER BY created_at DESC") as cursor:
            rows = await cursor.fetchall()
    
    return [
        {
            "id": row["id"],
            "name": row["name"],
            "ratios": json.loads(row["ratios_json"]) if row["ratios_json"] else None,
            "thresholds": json.loads(row["thresholds_json"]) if row["thresholds_json"] else None,
            "body_type": row["body_type"],
            "created_at": row["created_at"]
        }
        for row in rows
    ]


async def create_session(
    user_id: str,
    exercise: str,
    reps: int = 0,
    sets: int = 0,
    calories_est: float = 0.0,
    fatigue_score: float = 0.0,
    duration: int = 0
) -> int:
    """
    Create a new workout session record.
    
    Returns:
        Session ID
    """
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            INSERT INTO sessions (user_id, exercise, reps, sets, calories_est, fatigue_score, duration)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, exercise, reps, sets, calories_est, fatigue_score, duration)
        )
        await db.commit()
        session_id = cursor.lastrowid
    
    print(f"[DB] Created session {session_id} for user {user_id}: {exercise}")
    return session_id


# ==================== Session Operations ====================

async def update_session(
    session_id: int,
    reps: Optional[int] = None,
    sets: Optional[int] = None,
    calories_est: Optional[float] = None,
    fatigue_score: Optional[float] = None,
    duration: Optional[int] = None
) -> bool:
    """
    Update an existing workout session record.
    
    Returns:
        True if successful, False if session not found
    """
    updates = []
    params = []
    
    if reps is not None:
        updates.append("reps = ?")
        params.append(reps)
    if sets is not None:
        updates.append("sets = ?")
        params.append(sets)
    if calories_est is not None:
        updates.append("calories_est = ?")
        params.append(calories_est)
    if fatigue_score is not None:
        updates.append("fatigue_score = ?")
        params.append(fatigue_score)
    if duration is not None:
        updates.append("duration = ?")
        params.append(duration)
        
    if not updates:
        return True
        
    params.append(session_id)
    query = f"UPDATE sessions SET {', '.join(updates)} WHERE id = ?"
    
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(query, params)
        await db.commit()
        return cursor.rowcount > 0


async def get_user_sessions(user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Get session history for a user.
    
    Args:
        user_id: User's unique identifier
        limit: Maximum number of sessions to return
        
    Returns:
        List of session dictionaries, newest first
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT * FROM sessions 
            WHERE user_id = ? 
            ORDER BY date DESC 
            LIMIT ?
            """,
            (user_id, limit)
        ) as cursor:
            rows = await cursor.fetchall()
    
    return [
        {
            "id": row["id"],
            "user_id": row["user_id"],
            "date": row["date"],
            "exercise": row["exercise"],
            "reps": row["reps"],
            "sets": row["sets"],
            "calories_est": row["calories_est"],
            "fatigue_score": row["fatigue_score"],
            "duration": row["duration"]
        }
        for row in rows
    ]


async def get_user_stats(user_id: str) -> Dict[str, Any]:
    """
    Get aggregated statistics for a user.
    
    Returns:
        Dictionary with total_sessions, total_reps, total_calories, avg_fatigue
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT 
                COUNT(*) as total_sessions,
                COALESCE(SUM(reps), 0) as total_reps,
                COALESCE(SUM(calories_est), 0) as total_calories,
                COALESCE(AVG(fatigue_score), 0) as avg_fatigue,
                COALESCE(SUM(duration), 0) as total_duration
            FROM sessions 
            WHERE user_id = ?
            """,
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
    
    return {
        "total_sessions": row["total_sessions"],
        "total_reps": row["total_reps"],
        "total_calories": row["total_calories"],
        "avg_fatigue": round(row["avg_fatigue"], 2),
        "total_duration": row["total_duration"]
    }


# ==================== Utility Functions ====================

async def delete_user(user_id: str) -> bool:
    """Delete a user and all their sessions."""
    async with aiosqlite.connect(DB_PATH) as db:
        # Delete sessions first (foreign key)
        await db.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
        cursor = await db.execute("DELETE FROM users WHERE id = ?", (user_id,))
        await db.commit()
        
        if cursor.rowcount == 0:
            return False
    
    print(f"[DB] Deleted user: {user_id}")
    return True


async def cleanup_old_sessions(days: int = 90) -> int:
    """
    Delete sessions older than specified days.
    
    Returns:
        Number of deleted sessions
    """
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            DELETE FROM sessions 
            WHERE date < datetime('now', ? || ' days')
            """,
            (f"-{days}",)
        )
        await db.commit()
        deleted = cursor.rowcount
    
    if deleted > 0:
        print(f"[DB] Cleaned up {deleted} old sessions")
    return deleted
