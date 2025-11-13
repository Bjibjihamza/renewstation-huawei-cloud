# init_silver_data.py
import os
import pandas as pd
import psycopg2
from datetime import datetime
from psycopg2.extras import execute_values

# === Connexion DB ===
def get_conn():
    return psycopg2.connect(
        host=os.getenv('GAUSSDB_HOST', 'localhost'),
        port=os.getenv('GAUSSDB_PORT', '5432'),
        dbname='silver',
        user=os.getenv('GAUSSDB_USER', 'postgres'),
        password=os.getenv('GAUSSDB_PASSWORD', 'postgres')
    )

conn = get_conn()
cur = conn.cursor()

print("Démarrage de l'initialisation SILVER...")

# === 1. Copier tout de l'ancienne table → archive ===
print("1. Copie de energy_consumption_hourly → energy_consumption_hourly_archive")
cur.execute("""
    INSERT INTO energy_consumption_hourly_archive
    SELECT * FROM energy_consumption_hourly
    ON CONFLICT (time_ts, building) DO NOTHING;
""")
archive_count = cur.rowcount
print(f"   {archive_count} lignes copiées dans l'archive")

# === 2. Garder seulement l'heure actuelle dans live ===
now = datetime.now().replace(minute=0, second=0, microsecond=0)
print(f"2. Filtrage de l'heure actuelle : {now}")

cur.execute("""
    INSERT INTO energy_consumption_hourly_live
    SELECT * FROM energy_consumption_hourly
    WHERE time_ts = %s
    ON CONFLICT (time_ts, building) DO NOTHING;
""", (now,))
live_count = cur.rowcount
print(f"   {live_count} lignes insérées dans live (heure actuelle)")

# === 3. Initialiser les batteries à 100% SOC pour l'heure actuelle ===
print("3. Initialisation battery_state_real (main=3000 kWh, backup=1000 kWh)")

batteries = [
    {
        'id': f"{now.strftime('%Y%m%d%H')}_main",
        'timestamp': now,
        'battery_type': 'main',
        'capacity_kwh': 3000.0,
        'soc_start_pct': 100.0,
        'soc_end_pct': 100.0,
        'energy_stored_kwh': 3000.0
    },
    {
        'id': f"{now.strftime('%Y%m%d%H')}_backup",
        'timestamp': now,
        'battery_type': 'backup',
        'capacity_kwh': 1000.0,
        'soc_start_pct': 100.0,
        'soc_end_pct': 100.0,
        'energy_stored_kwh': 1000.0
    }
]

insert_query = """
    INSERT INTO battery_state_real (
        id, timestamp, battery_type, battery_capacity_kwh,
        solar_production_kwh, consumption_kwh, net_energy_kwh,
        soc_start_pct, soc_end_pct, energy_stored_kwh,
        battery_charge_kwh, battery_discharge_kwh,
        grid_import_kwh, grid_export_kwh
    ) VALUES (
        %(id)s, %(timestamp)s, %(battery_type)s, %(capacity_kwh)s,
        0.0, 0.0, 0.0,
        %(soc_start_pct)s, %(soc_end_pct)s, %(energy_stored_kwh)s,
        0.0, 0.0, 0.0, 0.0
    )
    ON CONFLICT (id) DO UPDATE SET
        soc_end_pct = EXCLUDED.soc_end_pct,
        energy_stored_kwh = EXCLUDED.energy_stored_kwh;
"""

for batt in batteries:
    cur.execute(insert_query, batt)

print("   Main battery : 3000 kWh (100%)")
print("   Backup battery: 1000 kWh (100%)")

# === Commit & fin ===
conn.commit()
cur.close()
conn.close()

print("\nINITIALISATION TERMINÉE !")
print(f"Archive  : {archive_count} lignes")
print(f"Live     : {live_count} lignes (heure actuelle)")
print(f"Batteries: main=3000 kWh, backup=1000 kWh → {now}")
print("\nTu peux maintenant lancer ton pipeline quotidien sans problème !")