"""
=============================================================================
SOLAR PRODUCTION & BATTERY STATE CALCULATOR (SIMPLIFIED)
=============================================================================
Architecture simplifiée:
1. Production solaire prédite (7 jours futurs uniquement)
2. État batteries UNIFIÉ:
   - Réel: Dernières 6h (is_predicted=FALSE)
   - Prédit: 7 jours futurs (is_predicted=TRUE)

Usage:
    python solar_battery_simplified.py --mode predicted
    python solar_battery_simplified.py --mode recent
=============================================================================
"""

import os
import sys
import argparse
import psycopg2
import pandas as pd
import numpy as np
import pvlib
from pvlib.location import Location
from pvlib.pvsystem import PVSystem
from pvlib.modelchain import ModelChain
from datetime import datetime, timedelta
from typing import Dict

# =============================================================================
# DATABASE CONNECTION
# =============================================================================

def get_db_connection():
    """Connexion PostgreSQL"""
    return psycopg2.connect(
        host=os.getenv('GAUSSDB_HOST', 'localhost'),
        port=os.getenv('GAUSSDB_PORT', '5432'),
        database=os.getenv('GAUSSDB_DB_SILVER', 'silver'),
        user=os.getenv('GAUSSDB_USER', 'postgres'),
        password=os.getenv('GAUSSDB_PASSWORD', 'postgres'),
        sslmode=os.getenv('GAUSSDB_SSLMODE', 'disable')
    )


# =============================================================================
# SOLAR PRODUCTION CALCULATION
# =============================================================================

def get_weather_forecast(mode: str = 'predicted') -> pd.DataFrame:
    """
    Récupère météo depuis weather_forecast_hourly
    
    Args:
        mode: 'predicted' (7j futurs) ou 'recent' (6h passées)
    """
    conn = None
    try:
        conn = get_db_connection()
        
        if mode == 'predicted':
            query = """
                SELECT 
                    forecast_timestamp,
                    temperature_c,
                    humidity_pct,
                    cloud_cover_pct,
                    solar_radiation_w_m2,
                    wind_speed_kmh
                FROM weather_forecast_hourly
                WHERE forecast_timestamp >= NOW()
                  AND forecast_timestamp <= NOW() + INTERVAL '7 days'
                ORDER BY forecast_timestamp
            """
        else:  # recent
            query = """
                SELECT 
                    forecast_timestamp,
                    temperature_c,
                    humidity_pct,
                    cloud_cover_pct,
                    solar_radiation_w_m2,
                    wind_speed_kmh
                FROM weather_forecast_hourly
                WHERE forecast_timestamp >= NOW() - INTERVAL '6 hours'
                  AND forecast_timestamp < NOW()
                ORDER BY forecast_timestamp
            """
        
        df = pd.read_sql_query(query, conn)
        
        if df.empty:
            print(f"⚠️ Aucune donnée météo ({mode})")
            return pd.DataFrame()
        
        # Préparer pour pvlib
        df = df.rename(columns={
            'forecast_timestamp': 'time',
            'temperature_c': 'temp_air',
            'wind_speed_kmh': 'wind_speed',
            'solar_radiation_w_m2': 'ghi',
            'cloud_cover_pct': 'cloud_cover',
            'humidity_pct': 'humidity'
        })
        
        df['time'] = pd.to_datetime(df['time'])
        df.set_index('time', inplace=True)
        df['wind_speed'] = df['wind_speed'] / 3.6  # km/h → m/s
        
        print(f"✅ Météo chargée: {len(df)} heures (mode: {mode})")
        return df
        
    except Exception as e:
        print(f"❌ Erreur météo: {e}")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()


def calculate_solar_production(weather_df: pd.DataFrame) -> pd.DataFrame:
    """Calcule production solaire avec pvlib (1,364 × 550W = 750 kWc)"""
    
    if weather_df.empty:
        return pd.DataFrame()
    
    print("⚙️ Calcul production solaire...")
    
    # Localisation Casablanca
    site = Location(
        latitude=33.5731,
        longitude=-7.5898,
        tz='Africa/Casablanca',
        altitude=0,
        name='RenewStation'
    )
    
    # Module 550W
    module_db = pvlib.pvsystem.retrieve_sam('CECMod')
    high_power = [n for n in module_db.columns if '550' in n or '545' in n]
    module_name = high_power[0] if high_power else 'Canadian_Solar_Inc__CS1U_410MS'
    module_params = module_db[module_name]
    
    # Ajuster à 550W
    scaling = 550 / module_params['STC']
    adjusted_module = module_params.copy()
    adjusted_module['STC'] = 550
    adjusted_module['I_mp_ref'] = module_params['I_mp_ref'] * np.sqrt(scaling)
    adjusted_module['V_mp_ref'] = module_params['V_mp_ref'] * np.sqrt(scaling)
    
    # Onduleur
    inverter_db = pvlib.pvsystem.retrieve_sam('CECInverter')
    large_inv = [n for n in inverter_db.columns if '100' in n]
    inverter_name = large_inv[0] if large_inv else inverter_db.columns[0]
    inverter_params = inverter_db[inverter_name]
    
    # Température
    temp_params = pvlib.temperature.TEMPERATURE_MODEL_PARAMETERS['sapm']['open_rack_glass_polymer']
    
    # 1,364 panneaux = 171 strings × 8 modules
    system = PVSystem(
        surface_tilt=30,
        surface_azimuth=180,
        module_parameters=adjusted_module,
        inverter_parameters=inverter_params,
        temperature_model_parameters=temp_params,
        modules_per_string=8,
        strings_per_inverter=171
    )
    
    mc = ModelChain(system, site, aoi_model='physical', spectral_model='no_loss')
    
    # Préparer météo
    weather_pvlib = weather_df[['ghi', 'temp_air', 'wind_speed']].copy()
    weather_pvlib[weather_pvlib < 0] = 0
    weather_pvlib['dni'] = weather_pvlib['ghi'] * 0.8
    weather_pvlib['dhi'] = weather_pvlib['ghi'] * 0.2
    
    try:
        mc.run_model(weather_pvlib)
        
        def extract_values(data, length):
            if hasattr(data, 'values'):
                data = data.values
            if len(data.shape) > 1:
                data = data.flatten()[:length]
            return data
        
        cell_temp = extract_values(mc.results.cell_temperature, len(weather_df))
        dc_power = extract_values(mc.results.dc, len(weather_df))
        ac_power = extract_values(mc.results.ac, len(weather_df))
        
        results = pd.DataFrame({
            'ghi_w_m2': weather_pvlib['ghi'].values,
            'dni_w_m2': weather_pvlib['dni'].values,
            'dhi_w_m2': weather_pvlib['dhi'].values,
            'temp_air': weather_df['temp_air'].values,
            'cloud_cover': weather_df.get('cloud_cover', 0).values,
            'humidity': weather_df.get('humidity', 0).values,
            'wind_speed_kmh': weather_df['wind_speed'].values * 3.6,
            'cell_temperature_c': cell_temp,
            'dc_power_kw': dc_power / 1000,
            'ac_power_kw': ac_power / 1000,
            'production_kwh': (ac_power / 1000).clip(lower=0)
        }, index=weather_df.index)
        
        print(f"✅ Production: {results['production_kwh'].sum():,.1f} kWh total")
        return results
        
    except Exception as e:
        print(f"❌ Erreur calcul: {e}")
        return pd.DataFrame()


# =============================================================================
# SAVE SOLAR PRODUCTION
# =============================================================================

def save_predicted_solar(results_df: pd.DataFrame):
    """Sauvegarde production solaire prédite"""
    if results_df.empty:
        return
    
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        print(f"\n💾 Sauvegarde production solaire ({len(results_df)} lignes)...")
        
        # Truncate pour éviter doublons
        cur.execute("TRUNCATE TABLE predicted_solar_production")
        
        for timestamp, row in results_df.iterrows():
            id_val = timestamp.strftime('%Y%m%d%H')
            
            cur.execute("""
                INSERT INTO predicted_solar_production (
                    id, forecast_timestamp,
                    temperature_c, humidity_pct, cloud_cover_pct,
                    solar_radiation_w_m2, wind_speed_kmh,
                    ghi_w_m2, dni_w_m2, dhi_w_m2,
                    cell_temperature_c, dc_power_kw, ac_power_kw,
                    predicted_production_kwh
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                id_val, timestamp,
                float(row['temp_air']), float(row['humidity']),
                float(row['cloud_cover']), float(row['ghi_w_m2']),
                float(row['wind_speed_kmh']), float(row['ghi_w_m2']),
                float(row['dni_w_m2']), float(row['dhi_w_m2']),
                float(row['cell_temperature_c']), float(row['dc_power_kw']),
                float(row['ac_power_kw']), float(row['production_kwh'])
            ))
        
        conn.commit()
        print(f"✅ Sauvegardé dans predicted_solar_production")
        
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"❌ Erreur sauvegarde: {e}")
    finally:
        if conn:
            conn.close()


# =============================================================================
# BATTERY STATE CALCULATION
# =============================================================================

def get_consumption(mode: str = 'predicted') -> pd.DataFrame:
    """Récupère consommation (prédite ou réelle)"""
    conn = None
    try:
        conn = get_db_connection()
        
        if mode == 'predicted':
            query = """
                SELECT time_ts, SUM(predicted_use_kw) as consumption_kwh
                FROM predicted_energy_consumption
                WHERE time_ts >= NOW()
                  AND time_ts <= NOW() + INTERVAL '7 days'
                GROUP BY time_ts
                ORDER BY time_ts
            """
        else:  # recent
            query = """
                SELECT time_ts, SUM(use_kw) as consumption_kwh
                FROM energy_consumption_hourly
                WHERE time_ts >= NOW() - INTERVAL '6 hours'
                  AND time_ts < NOW()
                GROUP BY time_ts
                ORDER BY time_ts
            """
        
        df = pd.read_sql_query(query, conn)
        df['time_ts'] = pd.to_datetime(df['time_ts'])
        df.set_index('time_ts', inplace=True)
        
        print(f"✅ Consommation chargée: {len(df)} heures (mode: {mode})")
        return df
        
    except Exception as e:
        print(f"❌ Erreur consommation: {e}")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()


def calculate_battery_state(
    solar_df: pd.DataFrame,
    consumption_df: pd.DataFrame,
    is_predicted: bool = True
) -> Dict[str, pd.DataFrame]:
    """Calcule état batteries (Main 2500 + Backup 700)"""
    
    if solar_df.empty or consumption_df.empty:
        print("⚠️ Données insuffisantes")
        return {'main': pd.DataFrame(), 'backup': pd.DataFrame()}
    
    print(f"\n🔋 Calcul batteries (predicted={is_predicted})...")
    
    MAIN_CAPACITY = 2500
    BACKUP_CAPACITY = 700
    
    # SOC initial: 100%
    main_soc = 100.0
    backup_soc = 100.0
    main_energy = MAIN_CAPACITY
    backup_energy = BACKUP_CAPACITY
    
    # Merge données
    df = solar_df[['production_kwh']].copy()
    df = df.join(consumption_df, how='outer').fillna(0)
    df['net_energy_kwh'] = df['production_kwh'] - df['consumption_kwh']
    
    main_results = []
    backup_results = []
    
    for timestamp, row in df.iterrows():
        production = row['production_kwh']
        consumption = row['consumption_kwh']
        net = row['net_energy_kwh']
        
        # MAIN BATTERY
        main_soc_start = main_soc
        main_charge = 0
        main_discharge = 0
        grid_import = 0
        grid_export = 0
        
        if net > 0:
            # Surplus: charger
            available = MAIN_CAPACITY - main_energy
            main_charge = min(net, available)
            main_energy += main_charge
            remaining = net - main_charge
            if remaining > 0:
                grid_export = remaining
        else:
            # Déficit: décharger
            deficit = abs(net)
            main_discharge = min(deficit, main_energy)
            main_energy -= main_discharge
            remaining_deficit = deficit - main_discharge
            if remaining_deficit > 0:
                grid_import = remaining_deficit
        
        main_soc = (main_energy / MAIN_CAPACITY) * 100
        
        main_results.append({
            'timestamp': timestamp,
            'battery_type': 'main',
            'is_predicted': is_predicted,
            'capacity_kwh': MAIN_CAPACITY,
            'solar_production_kwh': production,
            'consumption_kwh': consumption,
            'net_energy_kwh': net,
            'soc_start_pct': main_soc_start,
            'soc_end_pct': main_soc,
            'energy_stored_kwh': main_energy,
            'battery_charge_kwh': main_charge,
            'battery_discharge_kwh': main_discharge,
            'grid_import_kwh': grid_import,
            'grid_export_kwh': grid_export
        })
        
        # BACKUP BATTERY (réserve)
        backup_results.append({
            'timestamp': timestamp,
            'battery_type': 'backup',
            'is_predicted': is_predicted,
            'capacity_kwh': BACKUP_CAPACITY,
            'solar_production_kwh': 0,
            'consumption_kwh': 0,
            'net_energy_kwh': 0,
            'soc_start_pct': backup_soc,
            'soc_end_pct': backup_soc,
            'energy_stored_kwh': backup_energy,
            'battery_charge_kwh': 0,
            'battery_discharge_kwh': 0,
            'grid_import_kwh': 0,
            'grid_export_kwh': 0
        })
    
    main_df = pd.DataFrame(main_results).set_index('timestamp')
    backup_df = pd.DataFrame(backup_results).set_index('timestamp')
    
    print(f"✅ Main SOC final: {main_df['soc_end_pct'].iloc[-1]:.1f}%")
    
    return {'main': main_df, 'backup': backup_df}


def save_battery_state(battery_states: Dict[str, pd.DataFrame], is_predicted: bool):
    """Sauvegarde état batteries dans table unifiée"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        print(f"\n💾 Sauvegarde batteries (predicted={is_predicted})...")
        
        if is_predicted:
            # Supprimer anciennes prédictions
            cur.execute("DELETE FROM battery_state WHERE is_predicted = TRUE")
        
        inserted = 0
        for batt_type, df in battery_states.items():
            if df.empty:
                continue
            
            for timestamp, row in df.iterrows():
                id_val = timestamp.strftime('%Y%m%d%H') + f'_{batt_type}'
                
                cur.execute("""
                    INSERT INTO battery_state (
                        id, timestamp, battery_type, is_predicted,
                        battery_capacity_kwh, solar_production_kwh,
                        consumption_kwh, net_energy_kwh,
                        soc_start_pct, soc_end_pct, energy_stored_kwh,
                        battery_charge_kwh, battery_discharge_kwh,
                        grid_import_kwh, grid_export_kwh
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (id) DO UPDATE SET
                        solar_production_kwh = EXCLUDED.solar_production_kwh,
                        consumption_kwh = EXCLUDED.consumption_kwh,
                        net_energy_kwh = EXCLUDED.net_energy_kwh,
                        soc_start_pct = EXCLUDED.soc_start_pct,
                        soc_end_pct = EXCLUDED.soc_end_pct,
                        energy_stored_kwh = EXCLUDED.energy_stored_kwh,
                        battery_charge_kwh = EXCLUDED.battery_charge_kwh,
                        battery_discharge_kwh = EXCLUDED.battery_discharge_kwh,
                        grid_import_kwh = EXCLUDED.grid_import_kwh,
                        grid_export_kwh = EXCLUDED.grid_export_kwh,
                        updated_at = CURRENT_TIMESTAMP
                """, (
                    id_val, timestamp, batt_type, is_predicted,
                    float(row['capacity_kwh']), float(row['solar_production_kwh']),
                    float(row['consumption_kwh']), float(row['net_energy_kwh']),
                    float(row['soc_start_pct']), float(row['soc_end_pct']),
                    float(row['energy_stored_kwh']), float(row['battery_charge_kwh']),
                    float(row['battery_discharge_kwh']), float(row['grid_import_kwh']),
                    float(row['grid_export_kwh'])
                ))
                inserted += 1
        
        conn.commit()
        print(f"✅ {inserted} lignes sauvegardées dans battery_state")
        
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"❌ Erreur sauvegarde: {e}")
    finally:
        if conn:
            conn.close()


# =============================================================================
# MAIN WORKFLOWS
# =============================================================================

def run_predicted_mode():
    """Mode: Prédictions 7 jours futurs"""
    print("=" * 80)
    print("⚡ MODE PREDICTED - 7 JOURS FUTURS")
    print("=" * 80)
    
    # 1. Météo forecast
    weather_df = get_weather_forecast(mode='predicted')
    if weather_df.empty:
        print("❌ Pas de météo forecast")
        return
    
    # 2. Production solaire
    solar_df = calculate_solar_production(weather_df)
    if solar_df.empty:
        print("❌ Échec calcul solaire")
        return
    
    # 3. Sauvegarder production solaire
    save_predicted_solar(solar_df)
    
    # 4. Consommation prédite
    consumption_df = get_consumption(mode='predicted')
    if consumption_df.empty:
        print("❌ Pas de consommation prédite")
        return
    
    # 5. État batteries
    battery_states = calculate_battery_state(solar_df, consumption_df, is_predicted=True)
    
    # 6. Sauvegarder batteries
    save_battery_state(battery_states, is_predicted=True)
    
    print("\n✅ MODE PREDICTED TERMINÉ")


def run_recent_mode():
    """Mode: Dernières 6h réelles"""
    print("=" * 80)
    print("⚡ MODE RECENT - DERNIÈRES 6H")
    print("=" * 80)
    
    # 1. Météo récente
    weather_df = get_weather_forecast(mode='recent')
    if weather_df.empty:
        print("❌ Pas de météo récente")
        return
    
    # 2. Production solaire
    solar_df = calculate_solar_production(weather_df)
    if solar_df.empty:
        print("❌ Échec calcul solaire")
        return
    
    # 3. Consommation réelle
    consumption_df = get_consumption(mode='recent')
    if consumption_df.empty:
        print("❌ Pas de consommation réelle")
        return
    
    # 4. État batteries
    battery_states = calculate_battery_state(solar_df, consumption_df, is_predicted=False)
    
    # 5. Sauvegarder batteries
    save_battery_state(battery_states, is_predicted=False)
    
    print("\n✅ MODE RECENT TERMINÉ")


def main():
    parser = argparse.ArgumentParser(description='Solar & Battery Calculator')
    parser.add_argument(
        '--mode',
        choices=['predicted', 'recent', 'both'],
        default='predicted',
        help='Mode: predicted (7j), recent (6h), both'
    )
    
    args = parser.parse_args()
    
    print("⚡ SOLAR & BATTERY CALCULATOR - SIMPLIFIED")
    print("🔆 750 kWc | 🔋 Main: 2500 kWh | Backup: 700 kWh")
    print("=" * 80)
    
    try:
        if args.mode == 'predicted':
            run_predicted_mode()
        elif args.mode == 'recent':
            run_recent_mode()
        elif args.mode == 'both':
            run_predicted_mode()
            print("\n")
            run_recent_mode()
        
        print("\n✅ SUCCÈS!")
        
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()