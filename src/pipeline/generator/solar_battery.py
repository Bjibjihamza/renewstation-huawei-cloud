
"""
=============================================================================
SOLAR PRODUCTION & BATTERY STATE CALCULATOR
=============================================================================
Calcule:
1. Production solaire prédite (7 jours) depuis weather_forecast_hourly
2. État batteries (Main: 2500 kWh, Backup: 700 kWh)
   - Predicted state (7 jours futurs)
   - Historical state (passé réel)

Usage:
    python solar_battery_calculator.py --mode predicted
    python solar_battery_calculator.py --mode historical
    python solar_battery_calculator.py --mode both
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
from typing import List, Tuple, Dict

# =============================================================================
# DATABASE CONNECTION
# =============================================================================

def get_db_connection():
    """Connexion à PostgreSQL via variables d'environnement"""
    return psycopg2.connect(
        host=os.getenv('GAUSSDB_HOST', 'localhost'),
        port=os.getenv('GAUSSDB_PORT', '5432'),
        database=os.getenv('GAUSSDB_DB_SILVER', 'silver'),
        user=os.getenv('GAUSSDB_USER', 'postgres'),
        password=os.getenv('GAUSSDB_PASSWORD', 'postgres'),
        sslmode=os.getenv('GAUSSDB_SSLMODE', 'disable')
    )


# =============================================================================
# GET AVAILABLE BUILDINGS FROM DATABASE
# =============================================================================

def get_buildings_from_db() -> List[str]:
    """Récupère la liste des buildings depuis la table energy_consumption_hourly"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT DISTINCT building 
            FROM energy_consumption_hourly 
            ORDER BY building
        """)
        
        buildings = [row[0] for row in cur.fetchall()]
        
        print(f"✅ Buildings trouvés dans la DB: {len(buildings)}")
        for b in buildings:
            print(f"   • {b}")
        
        return buildings
        
    except Exception as e:
        print(f"⚠️ Erreur récupération buildings: {e}")
        print("📋 Utilisation liste par défaut...")
        return [
            "Hospital",
            "House1", "House2", "House3", "House4", "House5",
            "House6", "House7", "House8", "House9", "House10",
            "House11", "House12", "House13", "House14", "House15",
            "Industry1", "Industry2", "Industry3",
            "Office1", "Office2", "Office3", "Office4",
            "School"
        ]
    finally:
        if conn:
            conn.close()


# =============================================================================
# SOLAR PRODUCTION CALCULATION
# =============================================================================

def get_weather_forecast_from_db(mode: str = 'predicted') -> pd.DataFrame:
    """
    Récupère données météo depuis weather_forecast_hourly
    
    Args:
        mode: 'predicted' (7 jours futurs) ou 'historical' (passé)
    """
    conn = None
    try:
        conn = get_db_connection()
        
        if mode == 'predicted':
            # Next 7 days
            query = """
                SELECT 
                    forecast_timestamp,
                    temperature_c,
                    humidity_pct,
                    cloud_cover_pct,
                    solar_radiation_w_m2,
                    wind_speed_kmh,
                    precipitation_mm
                FROM weather_forecast_hourly
                WHERE forecast_timestamp >= NOW()
                  AND forecast_timestamp <= NOW() + INTERVAL '7 days'
                ORDER BY forecast_timestamp
            """
        else:
            # Historical (last 30 days)
            query = """
                SELECT 
                    forecast_timestamp as production_timestamp,
                    temperature_c,
                    humidity_pct,
                    cloud_cover_pct,
                    solar_radiation_w_m2,
                    wind_speed_kmh,
                    precipitation_mm
                FROM weather_forecast_hourly
                WHERE forecast_timestamp >= NOW() - INTERVAL '30 days'
                  AND forecast_timestamp < NOW()
                ORDER BY forecast_timestamp
            """
        
        df = pd.read_sql_query(query, conn)
        
        if df.empty:
            print(f"⚠️ Aucune donnée météo trouvée (mode: {mode})")
            return pd.DataFrame()
        
        # Renommer colonnes pour pvlib
        timestamp_col = 'forecast_timestamp' if mode == 'predicted' else 'production_timestamp'
        df = df.rename(columns={
            timestamp_col: 'time',
            'temperature_c': 'temp_air',
            'wind_speed_kmh': 'wind_speed',
            'solar_radiation_w_m2': 'ghi',
            'cloud_cover_pct': 'cloud_cover',
            'humidity_pct': 'humidity'
        })
        
        df['time'] = pd.to_datetime(df['time'])
        df.set_index('time', inplace=True)
        
        # Convertir wind_speed de km/h vers m/s
        df['wind_speed'] = df['wind_speed'] / 3.6
        
        print(f"✅ Météo chargée: {len(df)} heures (mode: {mode})")
        return df
        
    except Exception as e:
        print(f"❌ Erreur récupération météo: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()


def calculate_solar_production_pvlib(weather_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcule production solaire avec pvlib
    Configuration: 1,364 panneaux × 550W = 750 kWc
    """
    
    if weather_df.empty:
        return pd.DataFrame()
    
    print("\n⚙️ Configuration système PV...")
    
    # Localisation Casablanca
    latitude = 33.5731
    longitude = -7.5898
    
    site = Location(
        latitude=latitude,
        longitude=longitude,
        tz='Africa/Casablanca',
        altitude=0,
        name='RenewStation Casablanca'
    )
    
    # Module: JinkoSolar Tiger Neo 550W (approximation)
    module_db = pvlib.pvsystem.retrieve_sam('CECMod')
    
    # Chercher module proche 550W
    high_power = [name for name in module_db.columns if '550' in name or '545' in name]
    
    if high_power:
        module_name = high_power[0]
    else:
        module_name = 'Canadian_Solar_Inc__CS1U_410MS'
    
    module_params = module_db[module_name]
    
    # Ajuster pour 550W
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
    
    # Configuration: 1,364 panneaux
    modules_per_string = 8
    strings_total = 171  # 171 × 8 = 1,368 ≈ 1,364
    
    system = PVSystem(
        surface_tilt=30,          # Inclinaison optimale Maroc
        surface_azimuth=180,      # Plein sud
        module_parameters=adjusted_module,
        inverter_parameters=inverter_params,
        temperature_model_parameters=temp_params,
        modules_per_string=modules_per_string,
        strings_per_inverter=strings_total
    )
    
    print(f"   📦 Panneaux: 1,364 × 550W = 750 kWc")
    print(f"   📐 Config: {strings_total} strings × {modules_per_string} modules")
    
    # ModelChain
    mc = ModelChain(
        system,
        site,
        aoi_model='physical',
        spectral_model='no_loss'
    )
    
    print("🔄 Calcul production solaire...")
    
    # Préparer données météo
    weather_pvlib = weather_df[['ghi', 'temp_air', 'wind_speed']].copy()
    weather_pvlib[weather_pvlib < 0] = 0
    
    # Estimer DNI et DHI depuis GHI (si manquants)
    weather_pvlib['dni'] = weather_pvlib['ghi'] * 0.8  # Approximation
    weather_pvlib['dhi'] = weather_pvlib['ghi'] * 0.2
    
    try:
        # Calculer production
        mc.run_model(weather_pvlib)
        
        # Extraire résultats
        def extract_values(data, length):
            if hasattr(data, 'values'):
                data = data.values
            if len(data.shape) > 1:
                data = data.flatten()[:length]
            return data
        
        cell_temp = extract_values(mc.results.cell_temperature, len(weather_df))
        dc_power = extract_values(mc.results.dc, len(weather_df))
        ac_power = extract_values(mc.results.ac, len(weather_df))
        
        # DataFrame résultats
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
            'production_kwh': ac_power / 1000  # Production cette heure (kW = kWh pour 1h)
        }, index=weather_df.index)
        
        # Nettoyer valeurs négatives
        results['production_kwh'] = results['production_kwh'].clip(lower=0)
        
        print(f"✅ Production calculée: {len(results)} heures")
        print(f"   ⚡ Production totale: {results['production_kwh'].sum():,.1f} kWh")
        print(f"   📈 Pic puissance: {results['ac_power_kw'].max():,.1f} kW")
        
        return results
        
    except Exception as e:
        print(f"❌ Erreur calcul pvlib: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()


# =============================================================================
# SAVE SOLAR PRODUCTION TO DATABASE
# =============================================================================

def save_predicted_solar_production(results_df: pd.DataFrame):
    """Sauvegarde production solaire prédite dans DB"""
    if results_df.empty:
        print("⚠️ Pas de données solaires à sauvegarder")
        return
    
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        print(f"\n💾 Sauvegarde production solaire prédite ({len(results_df)} lignes)...")
        
        # Truncate table pour éviter doublons
        cur.execute("TRUNCATE TABLE predicted_solar_production")
        
        inserted = 0
        for timestamp, row in results_df.iterrows():
            id_val = timestamp.strftime('%Y%m%d%H')
            
            cur.execute("""
                INSERT INTO predicted_solar_production (
                    id, forecast_timestamp,
                    temperature_c, humidity_pct, cloud_cover_pct, solar_radiation_w_m2,
                    wind_speed_kmh, ghi_w_m2, dni_w_m2, dhi_w_m2,
                    cell_temperature_c, dc_power_kw, ac_power_kw, predicted_production_kwh
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (id) DO UPDATE SET
                    temperature_c = EXCLUDED.temperature_c,
                    humidity_pct = EXCLUDED.humidity_pct,
                    cloud_cover_pct = EXCLUDED.cloud_cover_pct,
                    solar_radiation_w_m2 = EXCLUDED.solar_radiation_w_m2,
                    wind_speed_kmh = EXCLUDED.wind_speed_kmh,
                    ghi_w_m2 = EXCLUDED.ghi_w_m2,
                    dni_w_m2 = EXCLUDED.dni_w_m2,
                    dhi_w_m2 = EXCLUDED.dhi_w_m2,
                    cell_temperature_c = EXCLUDED.cell_temperature_c,
                    dc_power_kw = EXCLUDED.dc_power_kw,
                    ac_power_kw = EXCLUDED.ac_power_kw,
                    predicted_production_kwh = EXCLUDED.predicted_production_kwh,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                id_val, timestamp,
                float(row['temp_air']), float(row['humidity']), float(row['cloud_cover']),
                float(row['ghi_w_m2']), float(row['wind_speed_kmh']),
                float(row['ghi_w_m2']), float(row['dni_w_m2']), float(row['dhi_w_m2']),
                float(row['cell_temperature_c']), float(row['dc_power_kw']),
                float(row['ac_power_kw']), float(row['production_kwh'])
            ))
            inserted += 1
        
        conn.commit()
        print(f"✅ {inserted} lignes sauvegardées dans predicted_solar_production")
        
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"❌ Erreur sauvegarde: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if conn:
            conn.close()


def save_historical_solar_production(results_df: pd.DataFrame):
    """Sauvegarde production solaire historique dans DB"""
    if results_df.empty:
        print("⚠️ Pas de données solaires historiques à sauvegarder")
        return
    
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        print(f"\n💾 Sauvegarde production solaire historique ({len(results_df)} lignes)...")
        
        inserted = 0
        for timestamp, row in results_df.iterrows():
            id_val = timestamp.strftime('%Y%m%d%H')
            
            cur.execute("""
                INSERT INTO historical_solar_production (
                    id, production_timestamp,
                    temperature_c, humidity_pct, cloud_cover_pct, solar_radiation_w_m2,
                    ghi_w_m2, dni_w_m2, dhi_w_m2,
                    cell_temperature_c, dc_power_kw, ac_power_kw, actual_production_kwh
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (id) DO NOTHING
            """, (
                id_val, timestamp,
                float(row['temp_air']), float(row['humidity']), float(row['cloud_cover']),
                float(row['ghi_w_m2']),
                float(row['ghi_w_m2']), float(row['dni_w_m2']), float(row['dhi_w_m2']),
                float(row['cell_temperature_c']), float(row['dc_power_kw']),
                float(row['ac_power_kw']), float(row['production_kwh'])
            ))
            inserted += 1
        
        conn.commit()
        print(f"✅ {inserted} lignes sauvegardées dans historical_solar_production")
        
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"❌ Erreur sauvegarde historique: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if conn:
            conn.close()


# =============================================================================
# BATTERY STATE CALCULATION
# =============================================================================

def get_predicted_consumption() -> pd.DataFrame:
    """Récupère consommation prédite depuis predicted_energy_consumption"""
    conn = None
    try:
        conn = get_db_connection()
        
        query = """
            SELECT 
                time_ts,
                SUM(predicted_use_kw) as total_consumption_kwh
            FROM predicted_energy_consumption
            WHERE time_ts >= NOW()
              AND time_ts <= NOW() + INTERVAL '7 days'
            GROUP BY time_ts
            ORDER BY time_ts
        """
        
        df = pd.read_sql_query(query, conn)
        df['time_ts'] = pd.to_datetime(df['time_ts'])
        df.set_index('time_ts', inplace=True)
        
        print(f"✅ Consommation prédite chargée: {len(df)} heures")
        return df
        
    except Exception as e:
        print(f"❌ Erreur récupération consommation: {e}")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()


def get_historical_consumption() -> pd.DataFrame:
    """Récupère consommation historique depuis energy_consumption_hourly"""
    conn = None
    try:
        conn = get_db_connection()
        
        query = """
            SELECT 
                time_ts,
                SUM(use_kw) as total_consumption_kwh
            FROM energy_consumption_hourly
            WHERE time_ts >= NOW() - INTERVAL '30 days'
              AND time_ts < NOW()
            GROUP BY time_ts
            ORDER BY time_ts
        """
        
        df = pd.read_sql_query(query, conn)
        df['time_ts'] = pd.to_datetime(df['time_ts'])
        df.set_index('time_ts', inplace=True)
        
        print(f"✅ Consommation historique chargée: {len(df)} heures")
        return df
        
    except Exception as e:
        print(f"❌ Erreur récupération consommation historique: {e}")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()


def calculate_battery_state(
    solar_df: pd.DataFrame,
    consumption_df: pd.DataFrame,
    mode: str = 'predicted'
) -> Dict[str, pd.DataFrame]:
    """
    Calcule état batteries heure par heure
    
    Args:
        solar_df: Production solaire
        consumption_df: Consommation totale
        mode: 'predicted' ou 'historical'
    
    Returns:
        Dict avec 'main' et 'backup' DataFrames
    """
    
    if solar_df.empty or consumption_df.empty:
        print("⚠️ Données insuffisantes pour calcul batteries")
        return {'main': pd.DataFrame(), 'backup': pd.DataFrame()}
    
    print(f"\n🔋 Calcul état batteries (mode: {mode})...")
    
    # Capacités batteries
    MAIN_CAPACITY = 2500  # kWh
    BACKUP_CAPACITY = 700  # kWh
    
    # SOC initial: 100%
    main_soc = 100.0
    backup_soc = 100.0
    
    main_energy = MAIN_CAPACITY  # kWh
    backup_energy = BACKUP_CAPACITY  # kWh
    
    # Merge solar + consumption
    df = solar_df[['production_kwh']].copy()
    df = df.join(consumption_df, how='outer').fillna(0)
    df = df.rename(columns={'total_consumption_kwh': 'consumption_kwh'})
    
    # Calcul net energy
    df['net_energy_kwh'] = df['production_kwh'] - df['consumption_kwh']
    
    # Listes pour stocker résultats
    main_results = []
    backup_results = []
    
    for timestamp, row in df.iterrows():
        production = row['production_kwh']
        consumption = row['consumption_kwh']
        net = row['net_energy_kwh']
        
        # --- MAIN BATTERY (prioritaire) ---
        main_soc_start = main_soc
        main_charge = 0
        main_discharge = 0
        grid_import = 0
        grid_export = 0
        
        if net > 0:
            # Surplus: charger main battery
            available_space = MAIN_CAPACITY - main_energy
            main_charge = min(net, available_space)
            main_energy += main_charge
            
            # Si encore surplus: export réseau
            remaining = net - main_charge
            if remaining > 0:
                grid_export = remaining
        else:
            # Déficit: décharger main battery
            deficit = abs(net)
            main_discharge = min(deficit, main_energy)
            main_energy -= main_discharge
            
            # Si batterie insuffisante: import réseau
            remaining_deficit = deficit - main_discharge
            if remaining_deficit > 0:
                grid_import = remaining_deficit
        
        main_soc = (main_energy / MAIN_CAPACITY) * 100
        
        main_results.append({
            'timestamp': timestamp,
            'battery_type': 'main',
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
        
        # --- BACKUP BATTERY (réserve, pas utilisée pour l'instant) ---
        backup_results.append({
            'timestamp': timestamp,
            'battery_type': 'backup',
            'capacity_kwh': BACKUP_CAPACITY,
            'solar_production_kwh': 0,  # Backup ne participe pas
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
    
    main_df = pd.DataFrame(main_results)
    backup_df = pd.DataFrame(backup_results)
    
    main_df.set_index('timestamp', inplace=True)
    backup_df.set_index('timestamp', inplace=True)
    
    print(f"✅ État batteries calculé: {len(main_df)} heures")
    print(f"   🔋 Main Battery - SOC final: {main_df['soc_end_pct'].iloc[-1]:.1f}%")
    print(f"   🔋 Backup Battery - SOC final: {backup_df['soc_end_pct'].iloc[-1]:.1f}%")
    
    return {'main': main_df, 'backup': backup_df}


def save_predicted_battery_state(battery_states: Dict[str, pd.DataFrame]):
    """Sauvegarde état batteries prédit"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        print(f"\n💾 Sauvegarde état batteries prédit...")
        
        # Truncate
        cur.execute("TRUNCATE TABLE predicted_battery_state")
        
        inserted = 0
        for batt_type, df in battery_states.items():
            if df.empty:
                continue
            
            for timestamp, row in df.iterrows():
                id_val = timestamp.strftime('%Y%m%d%H') + f'_{batt_type}'
                
                cur.execute("""
                    INSERT INTO predicted_battery_state (
                        id, forecast_timestamp, battery_type, battery_capacity_kwh,
                        predicted_solar_production_kwh, predicted_consumption_kwh,
                        predicted_net_energy_kwh, predicted_soc_start_pct, predicted_soc_end_pct,
                        predicted_energy_stored_kwh, predicted_battery_charge_kwh,
                        predicted_battery_discharge_kwh, predicted_grid_import_kwh,
                        predicted_grid_export_kwh
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """, (
                    id_val, timestamp, batt_type, float(row['capacity_kwh']),
                    float(row['solar_production_kwh']), float(row['consumption_kwh']),
                    float(row['net_energy_kwh']), float(row['soc_start_pct']),
                    float(row['soc_end_pct']), float(row['energy_stored_kwh']),
                    float(row['battery_charge_kwh']), float(row['battery_discharge_kwh']),
                    float(row['grid_import_kwh']), float(row['grid_export_kwh'])
                ))
                inserted += 1
        
        conn.commit()
        print(f"✅ {inserted} lignes sauvegardées dans predicted_battery_state")
        
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"❌ Erreur sauvegarde batteries prédites: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if conn:
            conn.close()


def save_historical_battery_state(battery_states: Dict[str, pd.DataFrame]):
    """Sauvegarde état batteries historique"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        print(f"\n💾 Sauvegarde état batteries historique...")
        
        inserted = 0
        for batt_type, df in battery_states.items():
            if df.empty:
                continue
            
            for timestamp, row in df.iterrows():
                id_val = timestamp.strftime('%Y%m%d%H') + f'_{batt_type}'
                
                cur.execute("""
                    INSERT INTO historical_battery_state (
                        id, timestamp, battery_type, battery_capacity_kwh,
                        actual_solar_production_kwh, actual_consumption_kwh,
                        actual_net_energy_kwh, actual_soc_start_pct, actual_soc_end_pct,
                        actual_energy_stored_kwh, actual_battery_charge_kwh,
                        actual_battery_discharge_kwh, actual_grid_import_kwh,
                        actual_grid_export_kwh, battery_cycles_count
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 0
                    )
                    ON CONFLICT (id) DO NOTHING
                """, (
                    id_val, timestamp, batt_type, float(row['capacity_kwh']),
                    float(row['solar_production_kwh']), float(row['consumption_kwh']),
                    float(row['net_energy_kwh']), float(row['soc_start_pct']),
                    float(row['soc_end_pct']), float(row['energy_stored_kwh']),
                    float(row['battery_charge_kwh']), float(row['battery_discharge_kwh']),
                    float(row['grid_import_kwh']), float(row['grid_export_kwh'])
                ))
                inserted += 1
        
        conn.commit()
        print(f"✅ {inserted} lignes sauvegardées dans historical_battery_state")
        
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"❌ Erreur sauvegarde batteries historiques: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if conn:
            conn.close()


# =============================================================================
# MAIN WORKFLOW
# =============================================================================

def run_predicted_mode():
    """Mode: Calcul état prédit (7 jours futurs)"""
    print("=" * 80)
    print("⚡ MODE PREDICTED - 7 JOURS FUTURS")
    print("=" * 80)
    
    # 1. Récupérer buildings
    buildings = get_buildings_from_db()
    print(f"\n📋 Buildings actifs: {len(buildings)}")
    
    # 2. Météo forecast
    weather_df = get_weather_forecast_from_db(mode='predicted')
    if weather_df.empty:
        print("❌ Pas de données météo forecast disponibles")
        return
    
    # 3. Calculer production solaire
    solar_df = calculate_solar_production_pvlib(weather_df)
    if solar_df.empty:
        print("❌ Échec calcul production solaire")
        return
    
    # 4. Sauvegarder production solaire
    save_predicted_solar_production(solar_df)
    
    # 5. Récupérer consommation prédite
    consumption_df = get_predicted_consumption()
    if consumption_df.empty:
        print("❌ Pas de données consommation prédite")
        return
    
    # 6. Calculer état batteries
    battery_states = calculate_battery_state(solar_df, consumption_df, mode='predicted')
    
    # 7. Sauvegarder état batteries
    save_predicted_battery_state(battery_states)
    
    print("\n" + "=" * 80)
    print("✅ MODE PREDICTED TERMINÉ")
    print("=" * 80)


def run_historical_mode():
    """Mode: Calcul état historique (passé réel)"""
    print("=" * 80)
    print("⚡ MODE HISTORICAL - PASSÉ RÉEL")
    print("=" * 80)
    
    # 1. Récupérer buildings
    buildings = get_buildings_from_db()
    print(f"\n📋 Buildings actifs: {len(buildings)}")
    
    # 2. Météo historique
    weather_df = get_weather_forecast_from_db(mode='historical')
    if weather_df.empty:
        print("❌ Pas de données météo historiques disponibles")
        return
    
    # 3. Calculer production solaire historique
    solar_df = calculate_solar_production_pvlib(weather_df)
    if solar_df.empty:
        print("❌ Échec calcul production solaire historique")
        return
    
    # 4. Sauvegarder production historique
    save_historical_solar_production(solar_df)
    
    # 5. Récupérer consommation historique
    consumption_df = get_historical_consumption()
    if consumption_df.empty:
        print("❌ Pas de données consommation historique")
        return
    
    # 6. Calculer état batteries historique
    battery_states = calculate_battery_state(solar_df, consumption_df, mode='historical')
    
    # 7. Sauvegarder état batteries historique
    save_historical_battery_state(battery_states)
    
    print("\n" + "=" * 80)
    print("✅ MODE HISTORICAL TERMINÉ")
    print("=" * 80)


def main():
    """Point d'entrée principal"""
    parser = argparse.ArgumentParser(
        description='Calculateur Production Solaire & État Batteries'
    )
    parser.add_argument(
        '--mode',
        type=str,
        choices=['predicted', 'historical', 'both'],
        default='predicted',
        help='Mode de calcul: predicted (7j futurs), historical (passé), both (les 2)'
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("⚡ SOLAR PRODUCTION & BATTERY STATE CALCULATOR")
    print("🔆 RenewStation - 750 kWc PV System")
    print("🔋 Main Battery: 2,500 kWh | Backup Battery: 700 kWh")
    print("=" * 80)
    
    try:
        if args.mode == 'predicted':
            run_predicted_mode()
        elif args.mode == 'historical':
            run_historical_mode()
        elif args.mode == 'both':
            run_predicted_mode()
            print("\n")
            run_historical_mode()
        
        print("\n✅ CALCULS TERMINÉS AVEC SUCCÈS!")
        
    except Exception as e:
        print(f"\n❌ ERREUR GLOBALE: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()