import os
import sys
import sqlite3
from pathlib import Path

# Ensure backend directory is in python path
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

project_root = current_dir.parent


def reset_demo_database(db_path: str = "data/cineguard.db", force: bool = False) -> bool:
    """
    Safely reset prototype demo data from SQLite database for repeated evaluation runs.
    Clears rows from 'alerts' and 'incidents' tables while preserving database schema.

    :param db_path: Path to SQLite database.
    :param force: If True, bypasses interactive confirmation prompt.
    :return: True if reset was executed.
    """
    target_db = project_root / db_path if not Path(db_path).is_absolute() else Path(db_path)

    if not target_db.exists():
        print(f"[RESET] Database file '{target_db}' does not exist. Nothing to reset.")
        return False

    print("==================================================")
    print("      CINEGUARD AI - DEMO DATA RESET UTILITY      ")
    print("==================================================")
    print(f"Target Database : {target_db}")
    print("WARNING: This action will clear prototype alerts and incidents")
    print("from the SQLite database while retaining the schema structure.")
    print("--------------------------------------------------")

    if not force:
        try:
            confirm = input("Type 'RESET' to confirm prototype data deletion: ").strip()
            if confirm != "RESET":
                print("Reset cancelled. No data modified.")
                return False
        except (EOFError, KeyboardInterrupt):
            print("\nReset cancelled.")
            return False

    try:
        conn = sqlite3.connect(str(target_db))
        cursor = conn.cursor()
        
        c_inc = cursor.execute("DELETE FROM incidents").rowcount
        c_alt = cursor.execute("DELETE FROM alerts").rowcount
        cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('alerts', 'incidents')")
        
        conn.commit()
        conn.close()

        print(f"[SUCCESS] Cleared {c_alt} prototype alert(s) and {c_inc} incident(s).")
        print(f"[SUCCESS] Database schema preserved. Database ready for new demo run.\n")
        return True
    except Exception as e:
        print(f"[ERROR] Reset failed: {e}")
        return False


if __name__ == "__main__":
    force_flag = "--force" in sys.argv or "-f" in sys.argv
    reset_demo_database(force=force_flag)
