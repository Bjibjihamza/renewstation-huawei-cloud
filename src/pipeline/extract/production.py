import requests
import pandas as pd
import pvlib
from pvlib.location import Location
from pvlib.pvsystem import PVSystem
from pvlib.modelchain import ModelChain
from datetime import datetime
import numpy as np

def get_weather_forecast_for_solar():
    """
    Récupère les prévisions météo avec données solaires pour Casablanca
    """
    # Coordonnées Casablanca (ou ajustez pour votre localisation)
    latitude = 33.5731
    longitude = -7.5898
    
    url = "https://api.open-meteo.com/v1/forecast"
    
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": [
            "temperature_2m",
            "relative_humidity_2m",
            "wind_speed_10m",
            "shortwave_radiation",  # GHI (Global Horizontal Irradiance)
            "direct_radiation",      # DNI (Direct Normal Irradiance)
            "diffuse_radiation",     # DHI (Diffuse Horizontal Irradiance)
            "cloud_cover"
        ],
        "timezone": "Africa/Casablanca",
        "forecast_days": 3
    }
    
    print("🔄 Récupération données météo Open-Meteo...")
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    
    # Convertir en DataFrame
    df = pd.DataFrame({
        'time': pd.to_datetime(data['hourly']['time']),
        'temp_air': data['hourly']['temperature_2m'],
        'wind_speed': data['hourly']['wind_speed_10m'],
        'ghi': data['hourly']['shortwave_radiation'],
        'dni': data['hourly']['direct_radiation'],
        'dhi': data['hourly']['diffuse_radiation'],
        'cloud_cover': data['hourly']['cloud_cover'],
        'humidity': data['hourly']['relative_humidity_2m']
    })
    
    df.set_index('time', inplace=True)
    
    print(f"✅ Données récupérées: {len(df)} heures")
    return df, latitude, longitude


def calculate_solar_production(weather_df, latitude, longitude):
    """
    Calcule la production solaire avec pvlib
    Configuration: 1,364 panneaux JinkoSolar Tiger Neo 550W
    """
    
    print("\n⚙️ Configuration du système PV...")
    
    # Localisation
    site = Location(
        latitude=latitude,
        longitude=longitude,
        tz='Africa/Casablanca',
        altitude=0,
        name='Centre Energie Casablanca'
    )
    
    # Récupérer base de données modules
    module_db = pvlib.pvsystem.retrieve_sam('CECMod')
    
    # Trouver un module proche de 550W
    # Utilisons un module réel de la base
    print("📦 Modules disponibles proche de 550W:")
    high_power_modules = [name for name in module_db.columns if '550' in name or '540' in name or '545' in name]
    
    if high_power_modules:
        module_name = high_power_modules[0]
        print(f"   ✅ Module sélectionné: {module_name}")
    else:
        # Si pas de 550W, utiliser un module et l'ajuster
        print("   ⚠️ Pas de module 550W exact, utilisation module de référence ajusté")
        module_name = 'Canadian_Solar_Inc__CS1U_410MS'  # Module de référence
    
    module_params = module_db[module_name]
    
    # Ajuster pour correspondre à 550W si nécessaire
    # On scale les paramètres proportionnellement
    scaling_factor = 550 / module_params['STC']
    
    # Créer paramètres module ajustés
    adjusted_module = module_params.copy()
    adjusted_module['STC'] = 550  # 550W nominal
    adjusted_module['I_mp_ref'] = module_params['I_mp_ref'] * np.sqrt(scaling_factor)
    adjusted_module['V_mp_ref'] = module_params['V_mp_ref'] * np.sqrt(scaling_factor)
    
    # Onduleurs (9 onduleurs de 100kW)
    inverter_db = pvlib.pvsystem.retrieve_sam('CECInverter')
    # Chercher onduleur ~100kW
    large_inverters = [name for name in inverter_db.columns if '100' in name]
    if large_inverters:
        inverter_name = large_inverters[0]
    else:
        inverter_name = inverter_db.columns[0]
    
    inverter_params = inverter_db[inverter_name]
    
    # Paramètres de température
    temperature_params = pvlib.temperature.TEMPERATURE_MODEL_PARAMETERS['sapm']['open_rack_glass_polymer']
    
    # Configuration système
    # 1,364 panneaux = 750 kWc
    # Répartis sur 9 onduleurs
    # ~152 panneaux par onduleur (en moyenne)
    # Configuration strings: 19 strings de 8 panneaux par onduleur
    
    modules_per_string = 8
    strings_per_inverter = 171  # 171 strings × 8 modules = 1,368 panneaux ≈ 1,364
    total_modules = modules_per_string * strings_per_inverter
    
    system = PVSystem(
        surface_tilt=30,  # Inclinaison optimale Maroc
        surface_azimuth=180,  # Plein sud
        module_parameters=adjusted_module,
        inverter_parameters=inverter_params,
        temperature_model_parameters=temperature_params,
        modules_per_string=modules_per_string,
        strings_per_inverter=strings_per_inverter
    )
    
    print(f"\n🔆 Configuration système:")
    print(f"   📊 Total panneaux: {total_modules}")
    print(f"   ⚡ Puissance crête: {total_modules * 550 / 1000:.1f} kWc")
    print(f"   📐 Inclinaison: 30°")
    print(f"   🧭 Orientation: Plein Sud (180°)")
    
    # ModelChain
    mc = ModelChain(
        system,
        site,
        aoi_model='physical',
        spectral_model='no_loss'
    )
    
    print("\n🔄 Calcul production solaire...")
    
    # Préparer les données météo pour pvlib
    weather_pvlib = weather_df[['ghi', 'dni', 'dhi', 'temp_air', 'wind_speed']].copy()
    
    # Nettoyer les valeurs négatives (nuit)
    weather_pvlib[weather_pvlib < 0] = 0
    
    # Calculer la production
    mc.run_model(weather_pvlib)
    
    # Créer DataFrame résultats
    # Extraire les valeurs correctement (gérer les arrays multidimensionnels)
    cell_temp = mc.results.cell_temperature
    if hasattr(cell_temp, 'values'):
        cell_temp = cell_temp.values
    if len(cell_temp.shape) > 1:
        cell_temp = cell_temp.flatten()[:len(weather_df)]
    
    dc_power = mc.results.dc
    if hasattr(dc_power, 'values'):
        dc_power = dc_power.values
    if len(dc_power.shape) > 1:
        dc_power = dc_power.flatten()[:len(weather_df)]
        
    ac_power = mc.results.ac
    if hasattr(ac_power, 'values'):
        ac_power = ac_power.values
    if len(ac_power.shape) > 1:
        ac_power = ac_power.flatten()[:len(weather_df)]
    
    results = pd.DataFrame({
        'datetime': weather_df.index,
        'ghi': weather_df['ghi'].values,
        'temp_air': weather_df['temp_air'].values,
        'cloud_cover': weather_df['cloud_cover'].values,
        'cell_temperature': cell_temp,
        'dc_power_kw': dc_power / 1000,  # Convertir en kW
        'ac_power_kw': ac_power / 1000,  # Convertir en kW
    })
    
    results.set_index('datetime', inplace=True)
    
    print("✅ Calculs terminés!\n")
    
    return results


def display_results(results):
    """
    Affiche les résultats de production
    """
    print("=" * 80)
    print("📊 PRÉVISIONS DE PRODUCTION SOLAIRE - CENTRE D'ÉNERGIE")
    print("=" * 80)
    print(f"🔆 Configuration: 1,364 panneaux JinkoSolar Tiger Neo 550W (750 kWc)")
    print(f"📅 Période: {results.index[0].strftime('%d/%m/%Y %H:%M')} → {results.index[-1].strftime('%d/%m/%Y %H:%M')}")
    print("=" * 80)
    
    # Statistiques par jour
    results['date'] = results.index.date
    daily_summary = results.groupby('date').agg({
        'ac_power_kw': ['max', 'sum'],
        'ghi': 'mean',
        'temp_air': 'mean',
        'cloud_cover': 'mean'
    })
    
    print("\n📈 PRODUCTION JOURNALIÈRE PRÉVUE:\n")
    print(f"{'Date':<15} {'Énergie (kWh)':<18} {'Pic (kW)':<12} {'GHI moy':<12} {'Temp moy':<12} {'Nuages %'}")
    print("-" * 80)
    
    for date, row in daily_summary.iterrows():
        energy_kwh = row[('ac_power_kw', 'sum')]
        peak_kw = row[('ac_power_kw', 'max')]
        ghi_avg = row[('ghi', 'mean')]
        temp_avg = row[('temp_air', 'mean')]
        cloud_avg = row[('cloud_cover', 'mean')]
        
        print(f"{date} │ {energy_kwh:>13,.1f} kWh │ {peak_kw:>7,.1f} kW │ {ghi_avg:>7,.1f} W/m² │ {temp_avg:>7,.1f}°C │ {cloud_avg:>5,.0f}%")
    
    # Totaux
    total_energy = results['ac_power_kw'].sum()
    max_power = results['ac_power_kw'].max()
    avg_power_daytime = results[results['ac_power_kw'] > 0]['ac_power_kw'].mean()
    
    print("-" * 80)
    print(f"{'TOTAL 3 JOURS':<15} │ {total_energy:>13,.1f} kWh │ {max_power:>7,.1f} kW │")
    print("=" * 80)
    
    print(f"\n📊 STATISTIQUES GLOBALES:")
    print(f"   ⚡ Énergie totale (3 jours): {total_energy:,.1f} kWh")
    print(f"   📈 Puissance maximale: {max_power:,.1f} kW")
    print(f"   📊 Puissance moyenne (jour): {avg_power_daytime:,.1f} kW")
    print(f"   ⏰ Heures de production: {len(results[results['ac_power_kw'] > 10])} heures")
    
    # Projection annuelle
    daily_avg = total_energy / 3
    annual_projection = daily_avg * 365
    print(f"\n🔮 PROJECTION ANNUELLE:")
    print(f"   📅 Production estimée: {annual_projection:,.0f} kWh/an")
    print(f"   💰 Valeur économique (0.12 €/kWh): {annual_projection * 0.12:,.0f} €/an")
    
    # Comparaison avec consommation
    consumption_annual = 788_456  # kWh/an de votre résidence
    print(f"\n📊 COUVERTURE DES BESOINS:")
    print(f"   🏘️ Consommation résidence: {consumption_annual:,} kWh/an")
    print(f"   ☀️ Production solaire: {annual_projection:,.0f} kWh/an")
    print(f"   📈 Taux de couverture: {(annual_projection/consumption_annual)*100:.1f}%")
    
    if annual_projection > consumption_annual:
        surplus = annual_projection - consumption_annual
        print(f"   ✅ Surplus: +{surplus:,.0f} kWh/an ({(surplus/consumption_annual)*100:.1f}%)")
        print(f"   💵 Revente surplus: {surplus * 0.08:,.0f} €/an (estimation)")
    else:
        deficit = consumption_annual - annual_projection
        print(f"   ⚠️ Déficit: -{deficit:,.0f} kWh/an ({(deficit/consumption_annual)*100:.1f}%)")
    
    print("=" * 80)
    
    # Top 10 heures les plus productives
    print("\n🌟 TOP 10 HEURES LES PLUS PRODUCTIVES:\n")
    top_hours = results.nlargest(10, 'ac_power_kw')[['ac_power_kw', 'ghi', 'temp_air', 'cloud_cover']]
    print(f"{'Date & Heure':<20} {'Puissance':<15} {'GHI':<15} {'Temp':<12} {'Nuages'}")
    print("-" * 80)
    for idx, row in top_hours.iterrows():
        print(f"{idx.strftime('%d/%m/%Y %H:%M'):<20} {row['ac_power_kw']:>10,.1f} kW │ {row['ghi']:>8,.0f} W/m² │ {row['temp_air']:>6,.1f}°C │ {row['cloud_cover']:>5,.0f}%")
    
    return results


def save_to_csv(results):
    """
    Sauvegarde les résultats en CSV
    """
    filename = f"production_solaire_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    results_export = results.copy()
    results_export.reset_index(inplace=True)
    results_export.to_csv(filename, index=False, encoding='utf-8')
    
    print(f"\n💾 Résultats sauvegardés: {filename}")
    return filename


def main():
    """
    Fonction principale
    """
    print("=" * 80)
    print("⚡ CALCULATEUR DE PRODUCTION SOLAIRE")
    print("🔆 Centre d'Énergie - 1,364 panneaux JinkoSolar 550W")
    print("=" * 80)
    
    try:
        # 1. Récupérer données météo
        weather_df, latitude, longitude = get_weather_forecast_for_solar()
        
        # 2. Calculer production
        results = calculate_solar_production(weather_df, latitude, longitude)
        
        # 3. Afficher résultats
        display_results(results)
        
        # 4. Sauvegarder CSV
        save_to_csv(results)
        
        print("\n✅ Analyse terminée avec succès!")
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()