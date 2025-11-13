import os
import psycopg2
import pandas as pd
import matplotlib.pyplot as plt

from src.pipeline.load.battery_loader import get_db_connection

plt.rcParams["figure.figsize"] = (14, 4)


def fetch_battery_states(table: str) -> pd.DataFrame:
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            f"""
            SELECT
                timestamp,
                battery_type,
                soc_start_pct,
                soc_end_pct,
                energy_stored_kwh,
                battery_charge_kwh,
                battery_discharge_kwh,
                grid_import_kwh,
                grid_export_kwh
            FROM {table}
            ORDER BY timestamp
            """
        )
        rows = cur.fetchall()
        cols = [
            "timestamp",
            "battery_type",
            "soc_start_pct",
            "soc_end_pct",
            "energy_stored_kwh",
            "battery_charge_kwh",
            "battery_discharge_kwh",
            "grid_import_kwh",
            "grid_export_kwh",
        ]
        df = pd.DataFrame(rows, columns=cols)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df
    finally:
        cur.close()
        conn.close()


real_df = fetch_battery_states("battery_state_real")
pred_df = fetch_battery_states("battery_state_predicted")

# ---------- 1) SOC EVOLUTION ----------
def plot_soc(df, title):
    pivot = df.pivot_table(
        index="timestamp",
        columns="battery_type",
        values="soc_end_pct",
        aggfunc="last"
    )

    plt.figure()
    for col in pivot.columns:
        plt.plot(pivot.index, pivot[col], label=f"SOC {col}")
    plt.title(title)
    plt.ylabel("SOC (%)")
    plt.legend()
    plt.grid(True)
    plt.show()


plot_soc(real_df, "🔋 REAL – SOC Evolution")
plot_soc(pred_df, "🔮 PREDICTED – SOC Evolution (7 days)")


# ---------- 2) CHARGE / DISCHARGE ----------
def plot_charge_discharge(df, title):
    charge_pivot = df.pivot_table(
        index="timestamp", columns="battery_type", values="battery_charge_kwh", aggfunc="sum"
    )
    discharge_pivot = df.pivot_table(
        index="timestamp", columns="battery_type", values="battery_discharge_kwh", aggfunc="sum"
    )

    plt.figure()
    for col in charge_pivot.columns:
        plt.plot(charge_pivot.index, charge_pivot[col], label=f"charge {col}")
    for col in discharge_pivot.columns:
        plt.plot(discharge_pivot.index, discharge_pivot[col], linestyle="--", label=f"discharge {col}")
    plt.title(title)
    plt.ylabel("kWh")
    plt.legend()
    plt.grid(True)
    plt.show()


plot_charge_discharge(real_df, "🔋 REAL – Charge/Discharge")
plot_charge_discharge(pred_df, "🔮 PREDICTED – Charge/Discharge")


# ---------- 3) GRID IMPORT / EXPORT ----------
def plot_grid_flux(df, title):
    imp_pivot = df.pivot_table(
        index="timestamp", columns="battery_type", values="grid_import_kwh", aggfunc="sum"
    )
    exp_pivot = df.pivot_table(
        index="timestamp", columns="battery_type", values="grid_export_kwh", aggfunc="sum"
    )

    plt.figure()
    for col in imp_pivot.columns:
        plt.plot(imp_pivot.index, imp_pivot[col], label=f"import {col}")
    for col in exp_pivot.columns:
        plt.plot(exp_pivot.index, exp_pivot[col], linestyle="--", label=f"export {col}")
    plt.title(title)
    plt.ylabel("kWh")
    plt.legend()
    plt.grid(True)
    plt.show()


plot_grid_flux(real_df, "🔌 REAL – Grid Import/Export")
plot_grid_flux(pred_df, "🔮 PREDICTED – Grid Import/Export")
