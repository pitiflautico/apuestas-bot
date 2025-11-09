#!/usr/bin/env python3
"""Test: Verificar que el sistema usa datos reales"""

import os
from pathlib import Path

# Cargar .env
env_file = Path(__file__).parent / '.env'
if env_file.exists():
    print("✅ Archivo .env encontrado")
    with open(env_file, 'r') as f:
        for line in f:
            if line.startswith('THE_ODDS_API_KEY='):
                key = line.split('=')[1].strip()
                if key and not key.startswith('${'):
                    print(f"✅ THE_ODDS_API_KEY configurada: {key[:8]}...")
                else:
                    print("❌ THE_ODDS_API_KEY NO configurada")
else:
    print("❌ Archivo .env NO encontrado")

print("\n--- Test 1: NBA Stats (Datos Reales) ---")
try:
    from src.ingest.nba_scraper import NBAStatsScraper
    scraper = NBAStatsScraper()
    game_log = scraper.get_player_game_log("LeBron James", last_n_games=5)

    if not game_log.empty:
        print(f"✅ NBA API funciona - {len(game_log)} partidos obtenidos")
        print(f"   Último partido: {game_log.iloc[0]['GAME_DATE']} - {game_log.iloc[0]['PTS']} puntos")
        print("   → DATOS REALES ✅")
    else:
        print("⚠️ NBA API devolvió datos vacíos")
except Exception as e:
    print(f"❌ Error NBA API: {e}")
    print("   Instala: pip install nba-api")

print("\n--- Test 2: Odds API (Cuotas Reales) ---")
try:
    from src.ingest.odds_collector import MultiBookCollector

    config = {
        'the_odds_api': {
            'enabled': True,
            'api_key': os.getenv('THE_ODDS_API_KEY', '')
        }
    }

    if config['the_odds_api']['api_key'] and not config['the_odds_api']['api_key'].startswith('${'):
        collector = MultiBookCollector(config)

        # Intentar obtener cuotas de La Liga (siempre hay partidos)
        odds = collector.collect_all_odds(['laliga'], ['h2h'])

        if odds.get('laliga'):
            print(f"✅ The Odds API funciona - {len(odds['laliga'])} partidos obtenidos")
            if odds['laliga']:
                first_match = odds['laliga'][0]
                print(f"   Partido: {first_match.get('home_team')} vs {first_match.get('away_team')}")
                if first_match.get('bookmakers'):
                    print(f"   Casas: {len(first_match['bookmakers'])} bookmakers con cuotas")
                    print("   → CUOTAS REALES ✅")
        else:
            print("⚠️ No se obtuvieron odds (puede ser normal si no hay partidos hoy)")
    else:
        print("❌ THE_ODDS_API_KEY no configurada")
        print("   Configura en .env: THE_ODDS_API_KEY=tu_key")
        print("   Obtén key gratis: https://the-odds-api.com/")

except Exception as e:
    print(f"❌ Error Odds API: {e}")

print("\n--- Test 3: Bookmaker URLs (URLs Reales) ---")
try:
    from src.ingest.odds_collector import BookmakerURLBuilder

    builder = BookmakerURLBuilder()
    bet365_url = builder.get_bookmaker_url('bet365', 'basketball_nba')
    pinnacle_url = builder.get_bookmaker_url('pinnacle', 'basketball_euroleague')

    if bet365_url and pinnacle_url:
        print(f"✅ URLs de casas configuradas")
        print(f"   Bet365 NBA: {bet365_url}")
        print(f"   Pinnacle EuroLeague: {pinnacle_url}")
        print("   → URLs REALES ✅")
    else:
        print("❌ URLs no configuradas correctamente")

except Exception as e:
    print(f"❌ Error URLs: {e}")

print("\n" + "="*60)
print("RESUMEN:")
print("="*60)
print("""
Si ves ✅ en todos los tests → Sistema usa DATOS REALES
Si ves ❌ → Configura las API keys para usar datos reales

Para configurar:
1. Crea archivo .env en la raíz del proyecto
2. Añade: THE_ODDS_API_KEY=tu_key_aqui
3. Obtén key gratis: https://the-odds-api.com/
4. Instala: pip install nba-api cloudscraper
""")
