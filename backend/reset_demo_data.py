import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

project_root = backend_dir.parent
from database import DatabaseManager


def reset_demo_database(db_path: str = None, force: bool = True):
    """
    Clear alerts and incidents tables and re-seed clean demonstration state.
    """
    if db_path is None:
        db_path = str(project_root / "data" / "agentshield.db")

    db = DatabaseManager(db_path=db_path)
    db.clear_all_data()

    print("==================================================")
    print("    AGENTSHIELD AI - DEMO DATA RESET UTILITY      ")
    print("==================================================")
    print(f"Target Database : {db_path}")
    print("[SUCCESS] Cleared alerts and incidents.")
    print("[SUCCESS] Database ready for AgentShield AI demonstration.")


if __name__ == "__main__":
    reset_demo_database(force=True)
