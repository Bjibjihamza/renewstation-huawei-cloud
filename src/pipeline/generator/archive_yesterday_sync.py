# src/pipeline/generator/archive_yesterday_sync.py
from src.pipeline.load.daily_archive_loader import archive_yesterday_all

def main():
    print("\n" + "=" * 80)
    print("ARCHIVE JOURNALIÈRE → weather_archive_hourly + energy_consumption_hourly_archive")
    print("=" * 80)

    archive_yesterday_all()

    print("=" * 80)
    print("ARCHIVE JOURNALIÈRE TERMINÉE")
    print("=" * 80)

if __name__ == "__main__":
    main()
