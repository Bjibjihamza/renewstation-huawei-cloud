import os
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests

from src.pipeline.load.weather_loader import load_weather_forecast_to_db

# ============================================================================
#   RÉCUPÉRATION DES PRÉVISIONS MÉTÉO + CHARGEMENT EN DB
# ============================================================================


def get_hourly_weather_forecast():
    """
    Récupère les prévisions météo horaires sur 3 jours pour Casablanca
    et les enregistre dans un fichier CSV + charge en DB
    """
    
    # Coordonnées de Casablanca
    latitude = 33.5731
    longitude = -7.5898
    
    # URL de l'API Open-Meteo
    url = "https://api.open-meteo.com/v1/forecast"
    
    # Paramètres de la requête pour données horaires
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": [
            "temperature_2m",
            "relativehumidity_2m",
            "precipitation",
            "precipitation_probability",
            "weathercode",
            "windspeed_10m",
            "winddirection_10m",
            "pressure_msl",
            "cloudcover"
        ],
        "timezone": "Africa/Casablanca",
        "forecast_days": 3  # 3 jours = 72 heures
    }
    
    try:
        # Effectuer la requête
        print("=" * 80)
        print("RÉCUPÉRATION DES PRÉVISIONS MÉTÉO CASABLANCA")
        print("=" * 80)
        print("🔄 Récupération des données météo depuis Open-Meteo...")
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        hourly_data = data["hourly"]
        total_hours = len(hourly_data["time"])
        
        # Créer le DataFrame
        rows = []
        for i in range(total_hours):
            dt = datetime.fromisoformat(hourly_data["time"][i])
            
            row = {
                'Date': dt.strftime('%Y-%m-%d'),
                'Heure': dt.strftime('%H:%M'),
                'Temperature (°C)': hourly_data["temperature_2m"][i],
                'Humidité (%)': hourly_data["relativehumidity_2m"][i],
                'Précipitation (mm)': hourly_data["precipitation"][i],
                'Probabilité Pluie (%)': hourly_data["precipitation_probability"][i] or 0,
                'Conditions': get_weather_description(hourly_data["weathercode"][i]),
                'Vitesse Vent (km/h)': hourly_data["windspeed_10m"][i],
                'Direction Vent (°)': hourly_data["winddirection_10m"][i],
                'Pression (hPa)': hourly_data["pressure_msl"][i],
                'Couverture Nuageuse (%)': hourly_data["cloudcover"][i]
            }
            rows.append(row)
        
        df = pd.DataFrame(rows)
        
        # Sauvegarder dans le dossier data/
        base_dir = Path(__file__).resolve().parents[3]
        data_dir = base_dir / "data"
        os.makedirs(data_dir, exist_ok=True)
        
        filename = data_dir / f"meteo_casablanca_horaire_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(filename, index=False)
        
        print(f"\n📦 Fichier CSV créé: {filename}")
        print(f"📊 Nombre total d'heures: {total_hours} heures (3 jours)")
        print(f"📍 Ville: Casablanca, Maroc")
        print(f"🕐 Période: {hourly_data['time'][0]} → {hourly_data['time'][-1]}")
        print(f"🌐 Source: Open-Meteo.com")
        
        # Charger dans la DB
        load_weather_forecast_to_db(df)
        
        # Afficher un aperçu
        print("\n📋 Aperçu des 5 premières heures:")
        print("-" * 80)
        for i in range(min(5, total_hours)):
            dt = datetime.fromisoformat(hourly_data["time"][i])
            temp = hourly_data["temperature_2m"][i]
            conditions = get_weather_description(hourly_data["weathercode"][i])
            icon = get_weather_icon(hourly_data["weathercode"][i])
            print(f"{icon} {dt.strftime('%d/%m/%Y %H:%M')} - {temp}°C - {conditions}")
        
        print("\n" + "=" * 80)
        print("✅ SUCCÈS! Prévisions météo récupérées et chargées en DB")
        print(f"📦 Fichier: {filename}")
        print("=" * 80)
        
        return str(filename)
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur lors de la récupération des données: {e}")
        return None
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return None


def get_weather_description(code):
    """Retourne la description météo selon le code WMO"""
    weather_codes = {
        0: "Ciel dégagé",
        1: "Principalement dégagé",
        2: "Partiellement nuageux",
        3: "Couvert",
        45: "Brouillard",
        48: "Brouillard givrant",
        51: "Bruine légère",
        53: "Bruine modérée",
        55: "Bruine dense",
        61: "Pluie légère",
        63: "Pluie modérée",
        65: "Pluie forte",
        71: "Chute de neige légère",
        73: "Chute de neige modérée",
        75: "Chute de neige forte",
        77: "Grains de neige",
        80: "Averses de pluie légères",
        81: "Averses de pluie modérées",
        82: "Averses de pluie violentes",
        85: "Averses de neige légères",
        86: "Averses de neige fortes",
        95: "Orage",
        96: "Orage avec grêle légère",
        99: "Orage avec grêle forte"
    }
    return weather_codes.get(code, f"Code: {code}")


def get_weather_icon(code):
    """Retourne un emoji selon le code météo"""
    if code == 0:
        return "☀️"
    elif code in [1, 2]:
        return "⛅"
    elif code == 3:
        return "☁️"
    elif code in [45, 48]:
        return "🌫️"
    elif code in [51, 53, 55, 61, 63, 65, 80, 81, 82]:
        return "🌧️"
    elif code in [71, 73, 75, 77, 85, 86]:
        return "❄️"
    elif code in [95, 96, 99]:
        return "⛈️"
    else:
        return "🌤️"


if __name__ == "__main__":
    get_hourly_weather_forecast()