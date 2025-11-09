#!/usr/bin/env python3
"""
Ejemplo de cómo obtener odds con URLs directas a las casas de apuestas

Este script muestra cómo:
1. Obtener odds de The Odds API
2. Enriquecer con URLs directas a los bookmakers
3. Mostrar dónde hacer las apuestas

Deportes soportados: NBA, ACB (Liga Endesa), La Liga, Tenis (ATP/WTA)
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ingest.odds_collector import MultiBookCollector, BookmakerURLBuilder
import json

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not installed, environment variables should be set manually
    pass


def example_get_bookmaker_urls():
    """Ejemplo 1: Obtener URLs de todas las casas de apuestas"""
    print("=" * 80)
    print("EJEMPLO 1: URLs de Casas de Apuestas Disponibles")
    print("=" * 80)

    url_builder = BookmakerURLBuilder()

    # Obtener URLs para NBA
    print("\n📱 BALONCESTO - NBA:")
    nba_bookies = url_builder.get_all_bookmaker_urls('basketball')

    for key, info in sorted(nba_bookies.items(), key=lambda x: x[1]['priority']):
        print(f"\n  {info['name']} ({info['type']})")
        print(f"  URL: {info['url']}")
        print(f"  Prioridad: {info['priority']}")

    # Obtener URLs para La Liga
    print("\n\n⚽ FÚTBOL - La Liga:")
    soccer_bookies = url_builder.get_all_bookmaker_urls('soccer')

    for key, info in sorted(soccer_bookies.items(), key=lambda x: x[1]['priority']):
        print(f"\n  {info['name']} ({info['type']})")
        print(f"  URL: {info['url']}")

    # Obtener URLs para Tenis
    print("\n\n🎾 TENIS - ATP/WTA:")
    tennis_bookies = url_builder.get_all_bookmaker_urls('tennis')

    for key, info in sorted(tennis_bookies.items(), key=lambda x: x[1]['priority']):
        print(f"\n  {info['name']} ({info['type']})")
        print(f"  URL: {info['url']}")


def example_collect_odds_with_urls():
    """Ejemplo 2: Obtener odds con URLs (requiere API key)"""
    print("\n\n")
    print("=" * 80)
    print("EJEMPLO 2: Obtener Odds con URLs Directas")
    print("=" * 80)

    api_key = os.getenv('THE_ODDS_API_KEY')

    if not api_key or api_key.startswith('${'):
        print("\n⚠️  THE_ODDS_API_KEY no configurada")
        print("   Para usar esta funcionalidad:")
        print("   1. Obtén una API key gratis en: https://the-odds-api.com/")
        print("   2. Añade THE_ODDS_API_KEY=tu_key en el archivo .env")
        print("\n   Por ahora, mostrando ejemplo con datos simulados...")
        show_simulated_example()
        return

    # Configuración
    config = {
        'the_odds_api': {
            'enabled': True,
            'api_key': api_key
        }
    }

    collector = MultiBookCollector(config)

    # Obtener odds para NBA
    print("\n📱 Obteniendo odds de NBA...")
    odds_data = collector.collect_all_odds(
        sports=['nba'],
        markets=['player_points', 'player_rebounds', 'player_assists']
    )

    # Mostrar primeros eventos
    if 'nba' in odds_data and odds_data['nba']:
        display_odds_with_urls(odds_data['nba'][:2], 'NBA')  # Mostrar solo 2 eventos

    # Obtener odds para La Liga
    print("\n⚽ Obteniendo odds de La Liga...")
    odds_data = collector.collect_all_odds(
        sports=['laliga'],
        markets=['h2h', 'totals']
    )

    if 'laliga' in odds_data and odds_data['laliga']:
        display_odds_with_urls(odds_data['laliga'][:2], 'La Liga')

    # Info de rate limit
    if 'the_odds_api' in collector.collectors:
        rate_info = collector.collectors['the_odds_api'].get_rate_limit_info()
        print(f"\n📊 Rate Limit: {rate_info['remaining']} requests restantes")


def display_odds_with_urls(events, sport_name):
    """Mostrar eventos con URLs de bookmakers"""
    print(f"\n{'=' * 80}")
    print(f"{sport_name} - Eventos con URLs")
    print('=' * 80)

    for event in events:
        print(f"\n🏀 {event.get('home_team', 'TBD')} vs {event.get('away_team', 'TBD')}")
        print(f"   Fecha: {event.get('commence_time', 'TBD')}")

        # Mostrar bookmakers disponibles
        print("\n   📍 Casas de Apuestas Disponibles:")

        for bookmaker in event.get('bookmakers', []):
            display_name = bookmaker.get('display_name', bookmaker.get('key'))
            betting_url = bookmaker.get('betting_url', 'URL no disponible')

            print(f"\n   ✓ {display_name}")
            print(f"     URL: {betting_url}")

            # Mostrar algunas odds
            for market in bookmaker.get('markets', [])[:1]:  # Solo primer mercado
                market_type = market.get('key', 'unknown')
                print(f"     Mercado: {market_type}")

                for outcome in market.get('outcomes', [])[:2]:  # Solo primeras 2 outcomes
                    print(f"       - {outcome.get('name')}: {outcome.get('price', 'N/A')}")


def show_simulated_example():
    """Mostrar ejemplo simulado de cómo se verían los datos"""
    print("\n" + "=" * 80)
    print("EJEMPLO SIMULADO - Estructura de datos con URLs")
    print("=" * 80)

    simulated_data = {
        "home_team": "Los Angeles Lakers",
        "away_team": "Golden State Warriors",
        "commence_time": "2025-11-10T02:00:00Z",
        "sport": "NBA",
        "bookmakers": [
            {
                "key": "bet365",
                "display_name": "Bet365",
                "betting_url": "https://www.bet365.es/#/AC/B3/C20604387/D48/E174/F48/",
                "markets": [
                    {
                        "key": "player_points",
                        "outcomes": [
                            {
                                "name": "LeBron James Over 25.5",
                                "price": 1.90
                            },
                            {
                                "name": "LeBron James Under 25.5",
                                "price": 1.90
                            }
                        ]
                    }
                ]
            },
            {
                "key": "williamhill",
                "display_name": "William Hill",
                "betting_url": "https://sports.williamhill.es/betting/es-es/baloncesto/competiciones/NBA",
                "markets": [
                    {
                        "key": "player_points",
                        "outcomes": [
                            {
                                "name": "LeBron James Over 25.5",
                                "price": 1.95
                            },
                            {
                                "name": "LeBron James Under 25.5",
                                "price": 1.85
                            }
                        ]
                    }
                ]
            },
            {
                "key": "codere",
                "display_name": "Codere",
                "betting_url": "https://www.codere.es/deportes/baloncesto/nba",
                "markets": [
                    {
                        "key": "player_points",
                        "outcomes": [
                            {
                                "name": "LeBron James Over 25.5",
                                "price": 1.88
                            },
                            {
                                "name": "LeBron James Under 25.5",
                                "price": 1.92
                            }
                        ]
                    }
                ]
            }
        ]
    }

    print(f"\n🏀 {simulated_data['home_team']} vs {simulated_data['away_team']}")
    print(f"   Deporte: {simulated_data['sport']}")
    print(f"   Fecha: {simulated_data['commence_time']}")

    print("\n   📍 Casas de Apuestas con URLs Directas:")

    for bookie in simulated_data['bookmakers']:
        print(f"\n   ✓ {bookie['display_name']}")
        print(f"     🔗 URL: {bookie['betting_url']}")
        print(f"     📊 Mercado: {bookie['markets'][0]['key']}")

        for outcome in bookie['markets'][0]['outcomes']:
            print(f"        - {outcome['name']}: {outcome['price']}")

    print("\n   💡 En producción, puedes hacer clic en las URLs para ir directamente")
    print("      a la casa de apuestas y realizar la apuesta.")


def example_get_best_odds_with_links():
    """Ejemplo 3: Encontrar mejores cuotas y mostrar dónde apostar"""
    print("\n\n")
    print("=" * 80)
    print("EJEMPLO 3: Mejores Cuotas + Dónde Apostar")
    print("=" * 80)

    # Datos simulados de diferentes bookmakers
    simulated_odds = [
        {
            "bookmaker": "bet365",
            "display_name": "Bet365",
            "url": "https://www.bet365.es/#/AC/B3/C20604387/D48/E174/F48/",
            "over_odds": 1.90,
            "under_odds": 1.90
        },
        {
            "bookmaker": "williamhill",
            "display_name": "William Hill",
            "url": "https://sports.williamhill.es/betting/es-es/baloncesto/competiciones/NBA",
            "over_odds": 1.95,
            "under_odds": 1.85
        },
        {
            "bookmaker": "codere",
            "display_name": "Codere",
            "url": "https://www.codere.es/deportes/baloncesto/nba",
            "over_odds": 1.88,
            "under_odds": 1.92
        },
        {
            "bookmaker": "bwin",
            "display_name": "Bwin",
            "url": "https://sports.bwin.es/es/sports/baloncesto-7/apuestas/estados-unidos/nba-42648",
            "over_odds": 1.87,
            "under_odds": 1.93
        }
    ]

    print("\n📊 Apuesta: LeBron James Over/Under 25.5 Puntos")
    print("\n   Comparación de Cuotas:")

    # Encontrar mejores cuotas
    best_over = max(simulated_odds, key=lambda x: x['over_odds'])
    best_under = max(simulated_odds, key=lambda x: x['under_odds'])

    print("\n   Todas las casas:")
    for bookie in simulated_odds:
        print(f"\n   {bookie['display_name']}:")
        print(f"     Over:  {bookie['over_odds']}" + (" ⭐ MEJOR" if bookie == best_over else ""))
        print(f"     Under: {bookie['under_odds']}" + (" ⭐ MEJOR" if bookie == best_under else ""))
        print(f"     URL:   {bookie['url']}")

    print("\n\n   🎯 RECOMENDACIÓN:")
    print(f"\n   Si quieres apostar OVER 25.5:")
    print(f"     ✓ Casa: {best_over['display_name']}")
    print(f"     ✓ Cuota: {best_over['over_odds']}")
    print(f"     ✓ URL: {best_over['url']}")

    print(f"\n   Si quieres apostar UNDER 25.5:")
    print(f"     ✓ Casa: {best_under['display_name']}")
    print(f"     ✓ Cuota: {best_under['under_odds']}")
    print(f"     ✓ URL: {best_under['url']}")


def main():
    """Run all examples"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 15 + "SISTEMA DE ODDS CON URLS A CASAS DE APUESTAS" + " " * 18 + "║")
    print("╚" + "=" * 78 + "╝")

    # Ejemplo 1: Ver todas las URLs disponibles
    example_get_bookmaker_urls()

    # Ejemplo 2: Obtener odds reales con URLs (requiere API key)
    example_collect_odds_with_urls()

    # Ejemplo 3: Encontrar mejores cuotas y dónde apostar
    example_get_best_odds_with_links()

    print("\n\n" + "=" * 80)
    print("RESUMEN DE CASAS DE APUESTAS DISPONIBLES")
    print("=" * 80)
    print("""
🏆 CASAS PRINCIPALES (España):

  1. Bet365        - https://www.bet365.es/
  2. William Hill  - https://sports.williamhill.es/
  3. Codere        - https://www.codere.es/deportes
  4. Bwin          - https://sports.bwin.es/
  5. Betfair       - https://www.betfair.com/exchange/plus/
  6. Pinnacle      - https://www.pinnacle.com/en/
  7. Marathon Bet  - https://www.marathonbet.es/
  8. Unibet        - https://www.unibet.es/

📱 DEPORTES SOPORTADOS:

  🏀 NBA (Baloncesto)
  🏀 ACB / Liga Endesa (Baloncesto España)
  ⚽ La Liga (Fútbol España)
  🎾 ATP/WTA (Tenis)

🔧 CONFIGURACIÓN:

  Para obtener odds en vivo:
  1. Crea cuenta gratuita en https://the-odds-api.com/
  2. Obtén tu API key
  3. Añade en .env: THE_ODDS_API_KEY=tu_key_aqui

💡 USO:

  El sistema automáticamente:
  - Obtiene las cuotas de múltiples casas
  - Te muestra la URL directa para hacer la apuesta
  - Compara cuotas para encontrar las mejores
  - Guarda todo en la base de datos con URLs
    """)

    print("=" * 80)
    print("✅ Script completado. Revisa los ejemplos arriba.")
    print("=" * 80)
    print()


if __name__ == "__main__":
    main()
