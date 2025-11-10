import os
import re
from pathlib import Path

import psycopg2
from dotenv import load_dotenv


# =============================================================================
# Load environment (.env.local then .env)
# =============================================================================
if os.path.exists(".env.local"):
    load_dotenv(".env.local")
else:
    load_dotenv()

DB_HOST = os.getenv("GAUSSDB_HOST", "localhost")
DB_PORT = int(os.getenv("GAUSSDB_PORT", "5432"))
DB_USER = os.getenv("GAUSSDB_USER", "postgres")
DB_PASSWORD = os.getenv("GAUSSDB_PASSWORD", "postgres")
DB_SSLMODE = os.getenv("GAUSSDB_SSLMODE", "disable")

# DB "admin" sur laquelle on a le droit de faire CREATE DATABASE
DB_ADMIN = os.getenv("GAUSSDB_DB_ADMIN", "postgres")


def get_connection(dbname: str):
    """Open a connection to a given database."""
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=dbname,
        user=DB_USER,
        password=DB_PASSWORD,
        sslmode=DB_SSLMODE,
    )
    conn.autocommit = True
    return conn


def split_sql_statements(sql_text: str):
    """
    Naive split on ';' for multiple statements.
    Ignore empty statements and psql meta-commands starting with '\'.
    """
    statements = []
    buffer = []

    for line in sql_text.splitlines():
        stripped = line.strip()

        # Skip psql meta-commands like "\c silver"
        if stripped.startswith("\\"):
            continue

        buffer.append(line)

        # If ';' in line → end of statement (very simple heuristic)
        if ";" in line:
            stmt = "\n".join(buffer).strip()
            buffer = []
            if stmt:
                # Remove trailing ';'
                if stmt.endswith(";"):
                    stmt = stmt[:-1]
                if stmt.strip():
                    statements.append(stmt)

    # Remaining buffer (no trailing ';')
    tail = "\n".join(buffer).strip()
    if tail:
        statements.append(tail)

    return statements


def run_sql_file(sql_path: Path):
    """
    Run a .sql file:
      - If it contains 'CREATE DATABASE xxx', create that DB on admin DB.
      - Ignore '\c xxx' and other meta-commands.
      - Execute remaining statements in the target DB (or silver if none).
    """
    print(f"\n📄 Processing {sql_path.name} ...")

    content = sql_path.read_text(encoding="utf-8")

    # 1) Detect CREATE DATABASE <name>
    db_match = re.search(r"CREATE\s+DATABASE\s+([a-zA-Z0-9_]+)", content, re.IGNORECASE)
    if db_match:
        db_name = db_match.group(1)
        print(f"   ➤ Detected database definition: {db_name}")

        # Create database on admin DB
        try:
            with get_connection(DB_ADMIN) as conn:
                with conn.cursor() as cur:
                    cur.execute(f"CREATE DATABASE {db_name};")
            print(f"   ✅ Database '{db_name}' created.")
        except psycopg2.errors.DuplicateDatabase:
            print(f"   ℹ️ Database '{db_name}' already exists, skipping creation.")
        except Exception as e:
            print(f"   ❌ Error creating database '{db_name}': {e}")

        # Remove CREATE DATABASE and \c lines from the content
        filtered_lines = []
        for line in content.splitlines():
            if re.search(r"CREATE\s+DATABASE\s+[a-zA-Z0-9_]+", line, re.IGNORECASE):
                continue
            if line.strip().startswith("\\c"):
                continue
            filtered_lines.append(line)

        remaining_sql = "\n".join(filtered_lines).strip()
        target_db = db_name
    else:
        # No CREATE DATABASE → default to silver DB
        remaining_sql = content
        target_db = os.getenv("GAUSSDB_DB_SILVER", "silver")
        print(f"   ➤ No CREATE DATABASE found, using DB '{target_db}'.")

    if not remaining_sql.strip():
        print("   ℹ️ No SQL statements to run (only DB declaration / comments).")
        return

    # 2) Execute remaining statements on the target DB
    statements = split_sql_statements(remaining_sql)
    if not statements:
        print("   ℹ️ No executable SQL statements found after parsing.")
        return

    print(f"   ➤ Executing {len(statements)} statement(s) on DB '{target_db}' ...")

    try:
        with get_connection(target_db) as conn:
            with conn.cursor() as cur:
                for stmt in statements:
                    # Ignore pure comments
                    if stmt.strip().startswith("--"):
                        continue
                    cur.execute(stmt)
        print(f"   ✅ Finished executing {sql_path.name} on '{target_db}'.")
    except Exception as e:
        print(f"   ❌ Error executing {sql_path.name} on '{target_db}': {e}")


def main():
    base_dir = Path(__file__).resolve().parent

    sql_files = [
        base_dir / "bronze.sql",
        base_dir / "silver.sql",
        base_dir / "gold.sql",
    ]

    print("===============================================")
    print("🛠  Building databases from SQL scripts")
    print("===============================================")
    print(f"Host={DB_HOST}, Port={DB_PORT}, User={DB_USER}")
    print(f"Admin DB={DB_ADMIN}")
    print("SQL files:", ", ".join(f.name for f in sql_files))

    for sql_file in sql_files:
        if sql_file.exists():
            run_sql_file(sql_file)
        else:
            print(f"\n⚠️ SQL file not found: {sql_file}")

    print("\n✅ Done.")


if __name__ == "__main__":
    main()
