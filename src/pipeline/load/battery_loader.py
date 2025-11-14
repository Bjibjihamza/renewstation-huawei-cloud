# src/pipeline/load/battery_loader.py
import os
from io import StringIO
from typing import Literal

import pandas as pd
import psycopg2
from dotenv import load_dotenv

# -------------------------------------------------------------------------
# ENV / DB CONNECTION
# -------------------------------------------------------------------------
if os.path.exists(".env.local"):
    load_dotenv(".env.local")
else:
    load_dotenv()


DB_HOST = os.getenv("GAUSSDB_HOST", "postgres")
DB_PORT = int(os.getenv("GAUSSDB_PORT", "5432"))
DB_NAME = os.getenv("GAUSSDB_DB_SILVER", "silver")
DB_USER = os.getenv("GAUSSDB_USER", "postgres")
DB_PASSWORD = os.getenv("GAUSSDB_PASSWORD", "postgres")
DB_SSLMODE = os.getenv("GAUSSDB_SSLMODE", "disable")


def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        sslmode=DB_SSLMODE,
    )


# -------------------------------------------------------------------------
# HELPERS
# -------------------------------------------------------------------------

def _normalize_timestamp(df: pd.DataFrame, col: str = "timestamp") -> pd.DataFrame:
    """
    Force timestamps to be timezone-naive (TIMESTAMP WITHOUT TIME ZONE).
    """
    if col not in df.columns:
        raise ValueError(f"Column '{col}' not found in DataFrame")

    df[col] = pd.to_datetime(df[col])


    try:
        if df[col].dt.tz is not None:
            df[col] = df[col].dt.tz_convert("UTC").dt.tz_localize(None)
    except AttributeError:
        pass

    return df


# -------------------------------------------------------------------------
# MAIN LOADER
# -------------------------------------------------------------------------
def load_battery_states(
    df: pd.DataFrame,
    target_table: Literal["battery_state_real", "battery_state_predicted"] = "battery_state_real",
):
    """
    Charge / upsert des états de batterie.

    Hypothèse : la table cible possède une contrainte UNIQUE/PK sur (timestamp, battery_type).
    On fait un ON CONFLICT sur ces deux colonnes.

    expected_cols DOIT correspondre au schéma logique commun
    à battery_state_real et battery_state_predicted.
    """
    if df.empty:
        print(f"[{target_table}] Rien à insérer (DataFrame vide).")
        return

    df = df.copy()

    # Normaliser timestamps
    df = _normalize_timestamp(df, col="timestamp")

    # Colonnes attendues
    expected_cols = [
        "timestamp",
        "battery_type",
        "is_predicted",
        "battery_capacity_kwh",
        "solar_production_kwh",
        "consumption_kwh",
        "net_energy_kwh",
        "soc_start_pct",
        "soc_end_pct",
        "energy_stored_kwh",
        "battery_charge_kwh",
        "battery_discharge_kwh",
        "grid_import_kwh",
        "grid_export_kwh",
    ]

    missing = [c for c in expected_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns for {target_table}: {missing}")

    df = df[expected_cols]
    df["is_predicted"] = df["is_predicted"].astype(bool)

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # -----------------------------------------------------------------
        # TEMP TABLE SANS COLONNE id / created_at / updated_at
        # (on ne copie QUE les colonnes de expected_cols)
        # -----------------------------------------------------------------
        cur.execute(
            """
            CREATE TEMP TABLE tmp_battery_states (
                timestamp              TIMESTAMP NOT NULL,
                battery_type           VARCHAR(20) NOT NULL,
                is_predicted           BOOLEAN NOT NULL,
                battery_capacity_kwh   NUMERIC(10,2) NOT NULL,
                solar_production_kwh   NUMERIC(10,4),
                consumption_kwh        NUMERIC(10,4),
                net_energy_kwh         NUMERIC(10,4),
                soc_start_pct          NUMERIC(5,2),
                soc_end_pct           NUMERIC(5,2),
                energy_stored_kwh      NUMERIC(10,2),
                battery_charge_kwh     NUMERIC(10,4),
                battery_discharge_kwh  NUMERIC(10,4),
                grid_import_kwh        NUMERIC(10,4),
                grid_export_kwh        NUMERIC(10,4)
            );
            """
        )

        # Copy depuis DataFrame → temp table
        buffer = StringIO()
        df.to_csv(buffer, index=False, header=False)
        buffer.seek(0)

        cur.copy_expert(
            f"COPY tmp_battery_states ({', '.join(expected_cols)}) FROM STDIN WITH (FORMAT csv)",
            buffer,
        )

        # -----------------------------------------------------------------
        # UPSERT vers la table cible
        # -----------------------------------------------------------------
        upsert_sql = f"""
        INSERT INTO {target_table} (
            timestamp,
            battery_type,
            is_predicted,
            battery_capacity_kwh,
            solar_production_kwh,
            consumption_kwh,
            net_energy_kwh,
            soc_start_pct,
            soc_end_pct,
            energy_stored_kwh,
            battery_charge_kwh,
            battery_discharge_kwh,
            grid_import_kwh,
            grid_export_kwh
        )
        SELECT
            timestamp,
            battery_type,
            is_predicted,
            battery_capacity_kwh,
            solar_production_kwh,
            consumption_kwh,
            net_energy_kwh,
            soc_start_pct,
            soc_end_pct,
            energy_stored_kwh,
            battery_charge_kwh,
            battery_discharge_kwh,
            grid_import_kwh,
            grid_export_kwh
        FROM tmp_battery_states
        ON CONFLICT (timestamp, battery_type) DO UPDATE SET
            is_predicted          = EXCLUDED.is_predicted,
            battery_capacity_kwh  = EXCLUDED.battery_capacity_kwh,
            solar_production_kwh  = EXCLUDED.solar_production_kwh,
            consumption_kwh       = EXCLUDED.consumption_kwh,
            net_energy_kwh        = EXCLUDED.net_energy_kwh,
            soc_start_pct         = EXCLUDED.soc_start_pct,
            soc_end_pct           = EXCLUDED.soc_end_pct,
            energy_stored_kwh     = EXCLUDED.energy_stored_kwh,
            battery_charge_kwh    = EXCLUDED.battery_charge_kwh,
            battery_discharge_kwh = EXCLUDED.battery_discharge_kwh,
            grid_import_kwh       = EXCLUDED.grid_import_kwh,
            grid_export_kwh       = EXCLUDED.grid_export_kwh,
            updated_at            = NOW();
        """

        cur.execute(upsert_sql)
        conn.commit()
        print(f"[{target_table}] {len(df)} rows upserted.")

    except Exception as e:
        conn.rollback()
        print(f"❌ Error while loading {target_table}: {e}")
        raise
    finally:
        cur.close()
        conn.close()
