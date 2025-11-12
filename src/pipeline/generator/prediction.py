"""
📊 PREPARE PREDICTION DATA - 7 DAYS AHEAD

Ce script:
1. Récupère les prévisions météo des 7 prochains jours
2. Génère les features (temporal, season flags, etc.)
3. Insère/Update dans predicted_energy_consumption (SANS les prédictions ML)
4. Les colonnes predicted_use_kw* restent NULL (à remplir par le modèle ML)

Usage:
    python prepare_prediction_data_7days.py
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from io import StringIO

import pandas as pd
import psycopg2

# Add project root to Python path
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline.load.energy_loader import generate_energy_id, get_db_connection

# ============================================================================
#   CONFIGURATION
# ============================================================================

# Liste de tous les bâtiments
BUILDINGS = [
    "Hospital",
    "House1", "House2", "House3", "House4", "House5",
    "House6", "House7", "House8", "House9", "House10",
    "House11", "House12", "House13", "House14", "House15",
    "Industry1", "Industry2", "Industry3",
    "Office1", "Office2", "Office3", "Office4",
    "School"
]


# ============================================================================
#   RÉCUPÉRATION DES PRÉVISIONS MÉTÉO (7 JOURS)
# ============================================================================

def fetch_weather_forecast_7days():
    """
    Récupère les prévisions météo des 7 prochains jours
    
    Returns:
        DataFrame avec les données météo futures
    """
    print("\n" + "=" * 80)
    print("📡 RÉCUPÉRATION DES PRÉVISIONS MÉTÉO (7 JOURS)")
    print("=" * 80)
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        now = datetime.now()
        
        query = """
        SELECT 
            forecast_timestamp as time,
            temperature_c,
            humidity_pct,
            cloud_cover_pct,
            solar_radiation_w_m2
        FROM weather_forecast_hourly
        WHERE forecast_timestamp > %s
        ORDER BY forecast_timestamp
        """
        
        print(f"🔍 Récupération depuis: {now}")
        cur.execute(query, (now,))
        rows = cur.fetchall()
        
        if not rows:
            print("❌ Aucune prévision météo disponible!")
            return None
        
        # Créer le DataFrame
        df = pd.DataFrame(rows, columns=[
            'Time',
            'Outdoor Temp (°C)',
            'Humidity (%)',
            'Cloud Cover (%)',
            'Solar Radiation (W/m²)'
        ])
        
        # Convertir les Decimal en float
        df['Outdoor Temp (°C)'] = df['Outdoor Temp (°C)'].astype(float)
        df['Humidity (%)'] = df['Humidity (%)'].astype(float)
        df['Cloud Cover (%)'] = df['Cloud Cover (%)'].astype(float)
        df['Solar Radiation (W/m²)'] = df['Solar Radiation (W/m²)'].astype(float)

        print(f"✅ {len(df)} heures de prévisions récupérées")
        print(f"📅 Période: {df['Time'].min()} → {df['Time'].max()}")
        print(f"🌡️  Température: min={df['Outdoor Temp (°C)'].min():.1f}°C, max={df['Outdoor Temp (°C)'].max():.1f}°C")
        
        return df
        
    except Exception as e:
        print(f"❌ Erreur lors de la récupération: {e}")
        raise
    finally:
        cur.close()
        conn.close()


# ============================================================================
#   AJOUT DES FEATURES TEMPORELLES
# ============================================================================

def add_temporal_features(df: pd.DataFrame) -> pd.DataFrame:
    """Ajoute toutes les features temporelles nécessaires"""
    df["Hour"] = df["Time"].dt.hour
    df["DayOfWeek"] = df["Time"].dt.dayofweek
    df["Month"] = df["Time"].dt.month
    df["DayOfYear"] = df["Time"].dt.dayofyear
    df["IsWeekend"] = df["DayOfWeek"].isin([5, 6]).astype(int)

    df["IsHoliday"] = (
        ((df["Time"].dt.month == 12) & (df["Time"].dt.day.between(24, 31)))
        | ((df["Time"].dt.month == 1) & (df["Time"].dt.day == 1))
        | ((df["Time"].dt.month == 7) & (df["Time"].dt.day == 4))
        | ((df["Time"].dt.month == 11) & (df["Time"].dt.day.between(22, 28)))
        | ((df["Time"].dt.month == 3) & (df["Time"].dt.day.between(15, 22)))
    ).astype(int)

    df["IsPeakHour"] = df["Hour"].isin([7, 8, 9, 17, 18, 19, 20]).astype(int)

    # Add season columns
    df["Winter"] = df["Month"].isin([12, 1, 2]).astype(int)
    df["Spring"] = df["Month"].isin([3, 4, 5]).astype(int)
    df["Summer"] = df["Month"].isin([6, 7, 8]).astype(int)
    df["Fall"] = df["Month"].isin([9, 10, 11]).astype(int)

    return df


# ============================================================================
#   PRÉPARATION DES DONNÉES POUR TOUS LES BÂTIMENTS
# ============================================================================

def prepare_prediction_features(weather_df: pd.DataFrame) -> pd.DataFrame:
    """
    Prépare un DataFrame avec toutes les features pour chaque bâtiment
    
    Returns:
        DataFrame prêt pour insertion dans predicted_energy_consumption
    """
    print("\n🔧 PRÉPARATION DES FEATURES POUR PRÉDICTION...")
    
    # Ajouter les features temporelles
    weather_with_features = add_temporal_features(weather_df.copy())
    
    # Créer une ligne par bâtiment et par timestamp
    all_data = []
    
    for building in BUILDINGS:
        building_df = weather_with_features.copy()
        building_df['Building'] = building
        all_data.append(building_df)
    
    combined = pd.concat(all_data, ignore_index=True)
    
    # Générer les IDs
    combined['id'] = combined.apply(
        lambda row: generate_energy_id(row['Time'], row['Building']),
        axis=1
    )
    
    print(f"✅ {len(combined)} lignes préparées ({len(BUILDINGS)} buildings × {len(weather_df)} hours)")
    print(f"📋 Exemples d'IDs: {combined['id'].head(3).tolist()}")
    
    return combined


# ============================================================================
#   UPSERT DANS LA TABLE PREDICTED_ENERGY_CONSUMPTION
# ============================================================================

def upsert_prediction_data_to_db(df: pd.DataFrame):
    """
    UPSERT (UPDATE + INSERT) du DataFrame dans predicted_energy_consumption
    
    NOTE: Les colonnes predicted_use_kw* restent NULL (à remplir par le modèle ML)
    
    Args:
        df: DataFrame avec toutes les features
    """
    print("\n💾 UPSERT DANS predicted_energy_consumption...")
    
    # 1) Renommer les colonnes pour matcher la table SQL
    df_db = df.rename(columns={
        'Time': 'time_ts',
        'Building': 'building',
        'Winter': 'winter_flag',
        'Spring': 'spring_flag',
        'Summer': 'summer_flag',
        'Fall': 'fall_flag',
        'Outdoor Temp (°C)': 'outdoor_temp_c',
        'Humidity (%)': 'humidity_pct',
        'Cloud Cover (%)': 'cloud_cover_pct',
        'Solar Radiation (W/m²)': 'solar_radiation_w_m2',
        'Hour': 'hour_of_day',
        'DayOfWeek': 'day_of_week',
        'Month': 'month_num',
        'DayOfYear': 'day_of_year',
        'IsWeekend': 'is_weekend',
        'IsHoliday': 'is_holiday',
        'IsPeakHour': 'is_peak_hour',
    })

    # 2) Colonnes dans l'ordre de la table SQL
    cols = [
        'id',
        'time_ts',
        'building',
        'winter_flag',
        'spring_flag',
        'summer_flag',
        'fall_flag',
        'outdoor_temp_c',
        'humidity_pct',
        'cloud_cover_pct',
        'solar_radiation_w_m2',
        'hour_of_day',
        'day_of_week',
        'month_num',
        'day_of_year',
        'is_weekend',
        'is_holiday',
        'is_peak_hour',
    ]
    df_db = df_db[cols]

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # 3) Créer une table temporaire
        print("🔄 Création de la table temporaire...")
        cur.execute("""
            CREATE TEMP TABLE temp_predicted_energy (
                id                     VARCHAR(50)    NOT NULL,
                time_ts                TIMESTAMP      NOT NULL,
                building               VARCHAR(50)    NOT NULL,
                winter_flag            SMALLINT       NOT NULL,
                spring_flag            SMALLINT       NOT NULL,
                summer_flag            SMALLINT       NOT NULL,
                fall_flag              SMALLINT       NOT NULL,
                outdoor_temp_c         NUMERIC(5,2),
                humidity_pct           NUMERIC(5,2),
                cloud_cover_pct        NUMERIC(5,2),
                solar_radiation_w_m2   NUMERIC(8,2),
                hour_of_day            SMALLINT       NOT NULL,
                day_of_week            SMALLINT       NOT NULL,
                month_num              SMALLINT       NOT NULL,
                day_of_year            SMALLINT       NOT NULL,
                is_weekend             SMALLINT       NOT NULL,
                is_holiday             SMALLINT       NOT NULL,
                is_peak_hour           SMALLINT       NOT NULL
            )
        """)

        # 4) Charger les données dans la table temporaire via COPY
        buffer = StringIO()
        df_db.to_csv(buffer, index=False, header=False)
        buffer.seek(0)

        copy_sql = """
        COPY temp_predicted_energy (
            id,
            time_ts,
            building,
            winter_flag,
            spring_flag,
            summer_flag,
            fall_flag,
            outdoor_temp_c,
            humidity_pct,
            cloud_cover_pct,
            solar_radiation_w_m2,
            hour_of_day,
            day_of_week,
            month_num,
            day_of_year,
            is_weekend,
            is_holiday,
            is_peak_hour
        )
        FROM STDIN WITH (FORMAT csv)
        """

        print("📥 Chargement des données dans la table temporaire...")
        cur.copy_expert(copy_sql, buffer)

        # 5) UPDATE des enregistrements existants (features only, keep predictions)
        print("🔄 Mise à jour des features existantes...")
        update_sql = """
        UPDATE predicted_energy_consumption pec
        SET 
            time_ts = t.time_ts,
            building = t.building,
            winter_flag = t.winter_flag,
            spring_flag = t.spring_flag,
            summer_flag = t.summer_flag,
            fall_flag = t.fall_flag,
            outdoor_temp_c = t.outdoor_temp_c,
            humidity_pct = t.humidity_pct,
            cloud_cover_pct = t.cloud_cover_pct,
            solar_radiation_w_m2 = t.solar_radiation_w_m2,
            hour_of_day = t.hour_of_day,
            day_of_week = t.day_of_week,
            month_num = t.month_num,
            day_of_year = t.day_of_year,
            is_weekend = t.is_weekend,
            is_holiday = t.is_holiday,
            is_peak_hour = t.is_peak_hour
        FROM temp_predicted_energy t
        WHERE pec.id = t.id
        """
        cur.execute(update_sql)
        updated_count = cur.rowcount

        # 6) INSERT des nouveaux enregistrements
        print("➕ Insertion des nouvelles lignes...")
        insert_sql = """
        INSERT INTO predicted_energy_consumption (
            id,
            time_ts,
            building,
            winter_flag,
            spring_flag,
            summer_flag,
            fall_flag,
            outdoor_temp_c,
            humidity_pct,
            cloud_cover_pct,
            solar_radiation_w_m2,
            hour_of_day,
            day_of_week,
            month_num,
            day_of_year,
            is_weekend,
            is_holiday,
            is_peak_hour,
            predicted_use_kw,
            predicted_use_kw_min,
            predicted_use_kw_max
        )
        SELECT 
            t.id,
            t.time_ts,
            t.building,
            t.winter_flag,
            t.spring_flag,
            t.summer_flag,
            t.fall_flag,
            t.outdoor_temp_c,
            t.humidity_pct,
            t.cloud_cover_pct,
            t.solar_radiation_w_m2,
            t.hour_of_day,
            t.day_of_week,
            t.month_num,
            t.day_of_year,
            t.is_weekend,
            t.is_holiday,
            t.is_peak_hour,
            NULL,  -- predicted_use_kw (à remplir par le modèle)
            NULL,  -- predicted_use_kw_min
            NULL   -- predicted_use_kw_max
        FROM temp_predicted_energy t
        WHERE NOT EXISTS (
            SELECT 1 
            FROM predicted_energy_consumption pec 
            WHERE pec.id = t.id
        )
        """
        cur.execute(insert_sql)
        inserted_count = cur.rowcount

        # 7) Commit
        conn.commit()

        print("\n" + "=" * 80)
        print("✅ UPSERT TERMINÉ")
        print(f"🔄 Lignes mises à jour: {updated_count}")
        print(f"➕ Nouvelles lignes insérées: {inserted_count}")
        print(f"📊 Total traité: {len(df_db)} lignes")
        print(f"⚠️  Colonnes predicted_use_kw* restent NULL (à remplir par le modèle ML)")
        print("=" * 80)

    except Exception as e:
        conn.rollback()
        print(f"\n❌ ERREUR lors de l'UPSERT: {e}")
        raise
    finally:
        cur.close()
        conn.close()


# ============================================================================
#   FONCTION PRINCIPALE
# ============================================================================

def main():
    """
    Pipeline complet de préparation des données de prédiction
    """
    print("=" * 80)
    print("📊 PRÉPARATION DES DONNÉES DE PRÉDICTION (7 JOURS)")
    print("=" * 80)
    print(f"🏢 Nombre de bâtiments: {len(BUILDINGS)}")
    print(f"⚠️  Les prédictions ML seront NULL (à remplir par le modèle)")
    
    # 1) Récupérer les prévisions météo (7 jours)
    weather_df = fetch_weather_forecast_7days()
    
    if weather_df is None or weather_df.empty:
        print("❌ Impossible de continuer sans prévisions météo")
        return
    
    # 2) Préparer les features pour tous les bâtiments
    features_df = prepare_prediction_features(weather_df)
    
    # 3) UPSERT dans la base (sans les prédictions ML)
    upsert_prediction_data_to_db(features_df)
    
    print("\n" + "=" * 80)
    print("✅ PIPELINE TERMINÉ AVEC SUCCÈS")
    print("=" * 80)
    print("\n💡 PROCHAINES ÉTAPES:")
    print("  1. Les données sont prêtes pour le modèle ML")
    print("  2. Lancer le script de prédiction ML pour remplir predicted_use_kw*")
    print("  3. Ce script se met à jour automatiquement à chaque mise à jour de la météo")
    print("=" * 80)


if __name__ == "__main__":
    main()