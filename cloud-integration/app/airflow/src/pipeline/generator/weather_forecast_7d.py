# src/pipeline/generator/weather_forecast_7d.py
import os
from datetime import datetime, timedelta
from pathlib import Path
import requests
import pandas as pd
from src.pipeline.load.weather_loader_7d import load_weather_forecast_to_db

LAT = 33.5731
LON = -7.5898
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
HOURLY_VARS = [
    "temperature_2m", "relativehumidity_2m", "precipitation",
    "precipitation_probability", "weathercode", "windspeed_10m",
    "winddirection_10m", "pressure_msl", "cloudcover", "shortwave_radiation"
]
TIMEZONE = "Africa/Casablanca"

def get_weather_description(code: int) -> str:
    codes = {
        0: "Ciel dégagé", 1: "Principalement dégagé", 2: "Partiellement nuageux", 3: "Couvert",
        45: "Brouillard", 48: "Brouillard givrant", 51: "Bruine légère", 53: "Bruine modérée",
        61: "Pluie légère", 63: "Pluie modérée", 65: "Pluie forte", 71: "Neige légère",
        80: "Averses légères", 81: "Averses modérées", 95: "Orage", 96: "Orage avec grêle"
    }
    return codes.get(code, f"Code {code}")

def fetch_7d_forecast():
    print("\nPRÉVISIONS MÉTÉO 7 JOURS → weather_forecast_hourly")
    
    params = {
        "latitude": LAT,
        "longitude": LON,
        "hourly": ",".join(HOURLY_VARS),
        "timezone": TIMEZONE,
        "forecast_days": 7
    }
    
    response = requests.get(FORECAST_URL, params=params)
    response.raise_for_status()
    data = response.json()
    
    hourly = data["hourly"]
    rows = []
    for i in range(len(hourly["time"])):
        dt = datetime.fromisoformat(hourly["time"][i])
        rows.append({
            "Date": dt.strftime("%Y-%m-%d"),
            "Heure": dt.strftime("%H:%M"),
            "Temperature (°C)": hourly["temperature_2m"][i],
            "Humidité (%)": hourly["relativehumidity_2m"][i],
            "Précipitation (mm)": hourly["precipitation"][i],
            "Probabilité Pluie (%)": hourly["precipitation_probability"][i] or 0,
            "Conditions": get_weather_description(hourly["weathercode"][i]),
            "Vitesse Vent (km/h)": hourly["windspeed_10m"][i],
            "Direction Vent (°)": hourly["winddirection_10m"][i],
            "Pression (hPa)": hourly["pressure_msl"][i],
            "Couverture Nuageuse (%)": hourly["cloudcover"][i],
            "Solar Radiation (W/m²)": hourly["shortwave_radiation"][i],
        })
    
    df = pd.DataFrame(rows)
    now = datetime.now()
    df["__ts"] = pd.to_datetime(df["Date"] + " " + df["Heure"])
    df = df[df["__ts"] >= now].drop(columns=["__ts"])
    
    print(f"{len(df)} heures récupérées → {df['Date'].iloc[0]} {df['Heure'].iloc[0]} → {df['Date'].iloc[-1]} {df['Heure'].iloc[-1]}")
    load_weather_forecast_to_db(df)

if __name__ == "__main__":
    fetch_7d_forecast()