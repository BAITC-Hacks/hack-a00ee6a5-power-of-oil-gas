import sqlite3
from contextlib import contextmanager
from pathlib import Path
from .config import DATABASE_PATH

DB_PATH = Path(DATABASE_PATH)
if not DB_PATH.is_absolute():
    DB_PATH = (Path(__file__).resolve().parent.parent / DB_PATH).resolve()
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def _connect():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def db_session():
    conn = _connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with db_session() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS challenges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                raw_description TEXT NOT NULL,
                industry TEXT NOT NULL DEFAULT 'Other',
                title TEXT,
                context TEXT,
                need TEXT,
                users TEXT,
                data_materials TEXT,
                constraints_text TEXT,
                expected_result TEXT,
                success_criteria TEXT,
                contact TEXT,
                interaction_format TEXT,
                ai_questions TEXT NOT NULL DEFAULT '[]',
                answers TEXT NOT NULL DEFAULT '[]',
                score INTEGER NOT NULL DEFAULT 0,
                readiness_level TEXT NOT NULL DEFAULT 'Черновик',
                status TEXT NOT NULL DEFAULT 'draft',
                is_confirmed INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS teams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                interests TEXT NOT NULL DEFAULT '[]',
                skills TEXT NOT NULL DEFAULT '[]',
                technologies TEXT NOT NULL DEFAULT '[]'
            );

            CREATE TABLE IF NOT EXISTS proposals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                challenge_id INTEGER NOT NULL,
                team_id INTEGER,
                team_name TEXT NOT NULL,
                solution_idea TEXT NOT NULL,
                plan TEXT NOT NULL,
                deadline TEXT NOT NULL,
                prototype_url TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (challenge_id) REFERENCES challenges(id) ON DELETE CASCADE,
                FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE SET NULL
            );
            CREATE TABLE IF NOT EXISTS milestones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                proposal_id INTEGER NOT NULL REFERENCES proposals(id) ON DELETE CASCADE,
                stage TEXT NOT NULL,
                evidence TEXT NOT NULL,
                points INTEGER NOT NULL,
                confirmed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(proposal_id, stage)
            );
            """
        )
        columns = {row[1] for row in conn.execute('PRAGMA table_info(challenges)')}
        if 'ai_mode' not in columns:
            conn.execute("ALTER TABLE challenges ADD COLUMN ai_mode TEXT NOT NULL DEFAULT 'fallback'")
        for name, definition in [('owner_id','INTEGER REFERENCES users(id)'), ('rating_json',"TEXT NOT NULL DEFAULT '{}'")]:
            if name not in columns:
                conn.execute(f'ALTER TABLE challenges ADD COLUMN {name} {definition}')
        conn.executescript('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                display_name TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('business','performer')),
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS sessions (
                token_hash TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                expires_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                challenge_id INTEGER NOT NULL REFERENCES challenges(id) ON DELETE CASCADE,
                card_hash TEXT NOT NULL,
                rating_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(challenge_id, card_hash)
            );
        ''')
        proposal_columns = {row[1] for row in conn.execute('PRAGMA table_info(proposals)')}
        if 'owner_id' not in proposal_columns:
            conn.execute('ALTER TABLE proposals ADD COLUMN owner_id INTEGER REFERENCES users(id)')
