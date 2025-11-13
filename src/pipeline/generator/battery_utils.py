# src/pipeline/generator/battery_utils.py
from dataclasses import dataclass
from typing import List
import pandas as pd


@dataclass
class BatteryConfig:
    battery_type: str              # "main" ou "backup"
    capacity_kwh: float            # ex: 3000, 1000
    max_charge_kw: float           # ex: 600
    max_discharge_kw: float        # ex: 600


def simulate_battery_series(
    df: pd.DataFrame,
    cfg: BatteryConfig,
    energy_stored_kwh_start: float,
) -> pd.DataFrame:
    """
    Simule l'état de la batterie heure par heure.

    df DOIT contenir :
      - 'timestamp' (datetime)
      - 'consumption_kwh' (float) → énergie consommée par le site
      - 'solar_kwh' (float)       → énergie produite par le PV

    Retourne un DataFrame avec les colonnes prêtes pour battery_state_real :
      id, timestamp, battery_type, battery_capacity_kwh,
      solar_production_kwh, consumption_kwh, net_energy_kwh,
      soc_start_pct, soc_end_pct, energy_stored_kwh,
      battery_charge_kwh, battery_discharge_kwh,
      grid_import_kwh, grid_export_kwh
    """

    records: List[dict] = []

    # État initial
    energy_stored = float(energy_stored_kwh_start)

    # sécurité : clamp dans [0, capacity]
    energy_stored = max(0.0, min(energy_stored, cfg.capacity_kwh))

    # on ordonne par timestamp pour être sûr
    df_sorted = df.sort_values("timestamp").reset_index(drop=True)

    for row in df_sorted.itertuples(index=False):
        ts = row.timestamp
        consumption = float(row.consumption_kwh)
        solar = float(getattr(row, "solar_kwh", 0.0))

        # énergies nettes
        net = solar - consumption  # >0: surplus, <0: déficit

        soc_start_pct = 100.0 * energy_stored / cfg.capacity_kwh if cfg.capacity_kwh > 0 else 0.0

        # ---- CHARGE / DÉCHARGE BATTERIE ----
        if net >= 0:
            # Surplus → on essaie de charger
            available_for_charge = net
            possible_charge = min(
                available_for_charge,
                cfg.max_charge_kw,
                cfg.capacity_kwh - energy_stored,
            )
            battery_charge_kwh = max(possible_charge, 0.0)
            battery_discharge_kwh = 0.0

            energy_stored_new = energy_stored + battery_charge_kwh

            # le reste part vers le grid (export)
            grid_export_kwh = max(available_for_charge - battery_charge_kwh, 0.0)
            grid_import_kwh = 0.0

        else:
            # Déficit → on essaie de décharger
            need_from_battery = -net
            possible_discharge = min(
                need_from_battery,
                cfg.max_discharge_kw,
                energy_stored,
            )
            battery_discharge_kwh = max(possible_discharge, 0.0)
            battery_charge_kwh = 0.0

            energy_stored_new = energy_stored - battery_discharge_kwh

            # le reste du besoin vient du grid (import)
            grid_import_kwh = max(need_from_battery - battery_discharge_kwh, 0.0)
            grid_export_kwh = 0.0

        # clamp de sécurité
        energy_stored_new = max(0.0, min(energy_stored_new, cfg.capacity_kwh))

        soc_end_pct = 100.0 * energy_stored_new / cfg.capacity_kwh if cfg.capacity_kwh > 0 else 0.0

        record = {
            "id": f"{ts.strftime('%Y%m%d%H')}_{cfg.battery_type}",
            "timestamp": ts,
            "battery_type": cfg.battery_type,
            "battery_capacity_kwh": cfg.capacity_kwh,

            "solar_production_kwh": solar,
            "consumption_kwh": consumption,
            "net_energy_kwh": net,

            "soc_start_pct": soc_start_pct,
            "soc_end_pct": soc_end_pct,
            "energy_stored_kwh": energy_stored_new,

            "battery_charge_kwh": battery_charge_kwh,
            "battery_discharge_kwh": battery_discharge_kwh,

            "grid_import_kwh": grid_import_kwh,
            "grid_export_kwh": grid_export_kwh,
        }

        records.append(record)
        energy_stored = energy_stored_new

    return pd.DataFrame.from_records(records)
