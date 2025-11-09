#!/usr/bin/env python3
"""
Ejemplo COMPLETO: Cómo hacer una predicción nueva

Este script muestra el flujo completo:
1. Obtener estadísticas del jugador (NBA API)
2. Obtener cuotas actuales (The Odds API)
3. Hacer predicción con el modelo
4. Calcular Expected Value (EV)
5. Generar recomendación con URL para apostar

Ejemplo: Predecir puntos de un jugador de NBA
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Try importing modules, but don't fail if not available
try:
    from src.ingest.nba_scraper import NBAStatsScraper, NBAFeatureExtractor
    NBA_AVAILABLE = True
except ImportError:
    NBA_AVAILABLE = False

try:
    from src.ingest.odds_collector import MultiBookCollector
    ODDS_COLLECTOR_AVAILABLE = True
except ImportError:
    ODDS_COLLECTOR_AVAILABLE = False

try:
    from src.models.poisson_model import PoissonPropModel
    POISSON_AVAILABLE = True
except ImportError:
    POISSON_AVAILABLE = False

try:
    from src.database import init_db, get_session, Pick
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False

from datetime import datetime
import json

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def ejemplo_prediccion_completa():
    """
    Ejemplo completo: Hacer una predicción de puntos de LeBron James
    """
    print("=" * 80)
    print("EJEMPLO: HACER UNA PREDICCIÓN COMPLETA - LeBron James Puntos")
    print("=" * 80)

    # ========================================================================
    # PASO 1: OBTENER ESTADÍSTICAS DEL JUGADOR
    # ========================================================================
    print("\n📊 PASO 1: Obteniendo estadísticas del jugador...")
    print("-" * 80)

    if not NBA_AVAILABLE:
        print("⚠️  nba-api no está instalado")
        print("   Usando datos simulados para el ejemplo...")
        avg_points = 25.3
        std_points = 6.2
        last_5_avg = 26.8
        player_name = "LeBron James"
    else:
        try:
            scraper = NBAStatsScraper()

            # Obtener últimos 10 partidos de LeBron
            player_name = "LeBron James"
            game_log = scraper.get_player_game_log(
                player_name=player_name,
                season="2024-25",
                last_n_games=10
            )

            if not game_log.empty:
                # Calcular estadísticas
                avg_points = game_log['PTS'].mean()
                std_points = game_log['PTS'].std()
                last_5_avg = game_log.head(5)['PTS'].mean()

                print(f"\n✓ Jugador: {player_name}")
                print(f"  - Promedio últimos 10 partidos: {avg_points:.1f} puntos")
                print(f"  - Desviación estándar: {std_points:.1f}")
                print(f"  - Promedio últimos 5 partidos: {last_5_avg:.1f} puntos")
                print(f"  - Rango reciente: {game_log['PTS'].min():.0f} - {game_log['PTS'].max():.0f} puntos")

                print("\n  Últimos 5 partidos:")
                for idx, row in game_log.head(5).iterrows():
                    print(f"    {row['GAME_DATE'].strftime('%Y-%m-%d')}: {row['PTS']} pts vs {row['MATCHUP']}")
            else:
                print("⚠️  No se pudieron obtener datos de NBA API (puede que no esté instalado nba-api)")
                print("   Usando datos simulados para el ejemplo...")
                avg_points = 25.3
                std_points = 6.2
                last_5_avg = 26.8

        except Exception as e:
            print(f"⚠️  Error obteniendo datos de NBA: {e}")
            print("   Usando datos simulados para el ejemplo...")
            avg_points = 25.3
            std_points = 6.2
            last_5_avg = 26.8

    # ========================================================================
    # PASO 2: OBTENER CUOTAS ACTUALES
    # ========================================================================
    print("\n\n💰 PASO 2: Obteniendo cuotas de casas de apuestas...")
    print("-" * 80)

    api_key = os.getenv('THE_ODDS_API_KEY')

    if api_key and not api_key.startswith('${') and ODDS_COLLECTOR_AVAILABLE:
        try:
            config = {
                'the_odds_api': {
                    'enabled': True,
                    'api_key': api_key
                }
            }

            collector = MultiBookCollector(config)
            odds_data = collector.collect_all_odds(
                sports=['nba'],
                markets=['player_points']
            )

            print("\n✓ Cuotas obtenidas de The Odds API")
            print(f"  Encontrados {len(odds_data.get('nba', []))} eventos")

            # Buscar odds de LeBron (simulado por ahora)
            line = 25.5
            odds_over = 1.90
            odds_under = 1.90
            best_bookmaker = "Bet365"
            bookmaker_url = "https://www.bet365.es/#/AC/B3/C20604387/D48/E174/F48/"

        except Exception as e:
            print(f"⚠️  Error obteniendo odds: {e}")
            print("   Usando odds simuladas...")
            line = 25.5
            odds_over = 1.90
            odds_under = 1.90
            best_bookmaker = "Bet365"
            bookmaker_url = "https://www.bet365.es/#/AC/B3/C20604387/D48/E174/F48/"
    else:
        print("⚠️  THE_ODDS_API_KEY no configurada")
        print("   Usando odds simuladas para el ejemplo...")
        line = 25.5
        odds_over = 1.90
        odds_under = 1.90
        best_bookmaker = "Bet365"
        bookmaker_url = "https://www.bet365.es/#/AC/B3/C20604387/D48/E174/F48/"

    print(f"\n  Línea actual: {line} puntos")
    print(f"  Over {line}: {odds_over} (Bet365)")
    print(f"  Under {line}: {odds_under} (William Hill)")

    # ========================================================================
    # PASO 3: HACER PREDICCIÓN CON EL MODELO
    # ========================================================================
    print("\n\n🎯 PASO 3: Calculando predicción con modelo Poisson...")
    print("-" * 80)

    if not POISSON_AVAILABLE:
        print("⚠️  scipy no está instalado")
        print("   Usando cálculo simple para el ejemplo...")
        # Cálculo simple asumiendo distribución normal
        z_score = (line - avg_points) / std_points
        prob_under = 0.5 + (0.5 * (z_score / abs(z_score)) * min(abs(z_score), 1))
        prob_over = 1 - prob_under
        predicted_value = avg_points
    else:
        try:
            model = PoissonPropModel()

            # Hacer predicción
            prediction = model.predict_value(
                mean=avg_points,
                std=std_points,
                line=line
            )

            prob_over = prediction['prob_over']
            prob_under = prediction['prob_under']
            predicted_value = prediction['predicted_value']

            print(f"\n✓ Predicción calculada:")
            print(f"  - Valor esperado: {predicted_value:.1f} puntos")
            print(f"  - Probabilidad OVER {line}: {prob_over:.2%}")
            print(f"  - Probabilidad UNDER {line}: {prob_under:.2%}")

        except Exception as e:
            print(f"⚠️  Error en predicción: {e}")
            # Calcular manualmente una predicción simple
            try:
                from scipy.stats import norm
                z_score = (line - avg_points) / std_points
                prob_under = norm.cdf(z_score)
                prob_over = 1 - prob_under
                predicted_value = avg_points
            except:
                z_score = (line - avg_points) / std_points
                prob_under = 0.5 + (0.5 * (z_score / abs(z_score)) * min(abs(z_score), 1))
                prob_over = 1 - prob_under
                predicted_value = avg_points

            print(f"\n✓ Predicción calculada (método simple):")
            print(f"  - Valor esperado: {predicted_value:.1f} puntos")
            print(f"  - Probabilidad OVER {line}: {prob_over:.2%}")
            print(f"  - Probabilidad UNDER {line}: {prob_under:.2%}")

    # ========================================================================
    # PASO 4: CALCULAR EXPECTED VALUE (EV)
    # ========================================================================
    print("\n\n💎 PASO 4: Calculando Expected Value (EV)...")
    print("-" * 80)

    # Convertir odds decimales a probabilidad implícita
    implied_prob_over = 1 / odds_over
    implied_prob_under = 1 / odds_under

    print(f"\n  Probabilidad implícita de las cuotas:")
    print(f"    Over: {implied_prob_over:.2%} (odds {odds_over})")
    print(f"    Under: {implied_prob_under:.2%} (odds {odds_under})")

    print(f"\n  Nuestra predicción:")
    print(f"    Over: {prob_over:.2%}")
    print(f"    Under: {prob_under:.2%}")

    # Calcular EV
    ev_over = (prob_over * (odds_over - 1)) - (prob_under * 1)
    ev_under = (prob_under * (odds_under - 1)) - (prob_over * 1)

    ev_over_percent = ev_over * 100
    ev_under_percent = ev_under * 100

    print(f"\n  Expected Value (EV):")
    print(f"    Over {line}: {ev_over_percent:+.2f}%")
    print(f"    Under {line}: {ev_under_percent:+.2f}%")

    # ========================================================================
    # PASO 5: GENERAR RECOMENDACIÓN
    # ========================================================================
    print("\n\n⭐ PASO 5: RECOMENDACIÓN FINAL")
    print("=" * 80)

    # Umbral de EV mínimo para apostar (ej: 5%)
    ev_threshold = 5.0

    if ev_over_percent > ev_threshold:
        recommendation = "OVER"
        ev_value = ev_over_percent
        odds_value = odds_over
        prob_value = prob_over
    elif ev_under_percent > ev_threshold:
        recommendation = "UNDER"
        ev_value = ev_under_percent
        odds_value = odds_under
        prob_value = prob_under
    else:
        recommendation = "NO APOSTAR"
        ev_value = max(ev_over_percent, ev_under_percent)
        odds_value = None
        prob_value = None

    print(f"\n🎯 RECOMENDACIÓN: {recommendation}")

    if recommendation != "NO APOSTAR":
        print(f"\n📋 Detalles de la apuesta:")
        print(f"   Jugador: {player_name}")
        print(f"   Mercado: Puntos")
        print(f"   Línea: {recommendation} {line}")
        print(f"   Casa: {best_bookmaker}")
        print(f"   Cuota: {odds_value}")
        print(f"   EV: +{ev_value:.2f}%")
        print(f"   Probabilidad estimada: {prob_value:.1%}")

        print(f"\n🔗 DÓNDE APOSTAR:")
        print(f"   {bookmaker_url}")

        # Calcular stake recomendado (Kelly Criterion simplificado)
        edge = (prob_value * odds_value - 1) / (odds_value - 1)
        kelly_fraction = edge if edge > 0 else 0
        recommended_stake_percent = kelly_fraction * 0.25  # Quarter Kelly

        print(f"\n💰 STAKE RECOMENDADO:")
        print(f"   {recommended_stake_percent * 100:.1f}% de tu bankroll")
        print(f"   (Ej: si bankroll = 1000€, apostar {recommended_stake_percent * 1000:.2f}€)")

    else:
        print(f"\n❌ NO hay valor suficiente en esta apuesta")
        print(f"   EV máximo encontrado: {ev_value:.2f}%")
        print(f"   Umbral mínimo: {ev_threshold:.2f}%")
        print(f"\n💡 Espera mejores oportunidades o líneas más favorables")

    # ========================================================================
    # PASO 6: GUARDAR EN BASE DE DATOS (OPCIONAL)
    # ========================================================================
    print("\n\n💾 PASO 6: Guardando en base de datos...")
    print("-" * 80)

    if not DATABASE_AVAILABLE:
        print("⚠️  SQLAlchemy no está instalado")
        print("   Saltando guardado en base de datos...")
    else:
        try:
            # Inicializar DB
            engine = init_db()
            session = get_session(engine)

            if recommendation != "NO APOSTAR":
                # Crear pick
                pick = Pick(
                    match_id=1,  # En producción, esto vendría de la tabla matches
                    market_type='points',
                    player_name=player_name,
                    selection=recommendation.lower(),
                    line=line,
                    odds=odds_value,
                    bookmaker=best_bookmaker,
                    bookmaker_display_name=best_bookmaker,
                    betting_url=bookmaker_url,
                    estimated_prob=prob_value,
                    expected_value=ev_value / 100,
                    edge_percent=ev_value,
                    recommended_stake=recommended_stake_percent,
                    status='recommended',
                    result='pending'
                )

                session.add(pick)
                session.commit()

                print(f"✓ Pick guardado en la base de datos (ID: {pick.id})")
            else:
                print("  No se guardó pick (EV insuficiente)")

            session.close()

        except Exception as e:
            print(f"⚠️  Error guardando en DB: {e}")
            print("   (Esto es normal si la DB no está inicializada)")

    print("\n" + "=" * 80)
    print("✅ PREDICCIÓN COMPLETA")
    print("=" * 80)


def ejemplo_prediccion_rapida():
    """
    Ejemplo rápido sin API calls - solo cálculos
    """
    print("\n\n" + "=" * 80)
    print("EJEMPLO RÁPIDO: Predicción sin API calls")
    print("=" * 80)

    # Datos de ejemplo
    player = "Luka Doncic"
    avg_points = 28.5
    std_points = 6.8
    line = 27.5
    odds_over = 1.95
    odds_under = 1.85

    print(f"\n📊 Datos:")
    print(f"   Jugador: {player}")
    print(f"   Promedio: {avg_points} puntos")
    print(f"   Desviación: {std_points}")
    print(f"   Línea: {line}")
    print(f"   Odds Over: {odds_over}")
    print(f"   Odds Under: {odds_under}")

    # Cálculo rápido
    try:
        from scipy.stats import norm
        z_score = (line - avg_points) / std_points
        prob_under = norm.cdf(z_score)
        prob_over = 1 - prob_under
    except:
        # Fallback sin scipy
        z_score = (line - avg_points) / std_points
        prob_under = 0.5 + (0.5 * (z_score / abs(z_score) if z_score != 0 else 0) * min(abs(z_score), 1))
        prob_over = 1 - prob_under

    # EV
    ev_over = (prob_over * (odds_over - 1)) - (prob_under * 1)
    ev_under = (prob_under * (odds_under - 1)) - (prob_over * 1)

    print(f"\n🎯 Resultados:")
    print(f"   Prob Over: {prob_over:.1%}")
    print(f"   Prob Under: {prob_under:.1%}")
    print(f"   EV Over: {ev_over * 100:+.2f}%")
    print(f"   EV Under: {ev_under * 100:+.2f}%")

    if ev_over > 0.05:
        print(f"\n⭐ RECOMENDACIÓN: Apostar OVER {line} @ {odds_over}")
    elif ev_under > 0.05:
        print(f"\n⭐ RECOMENDACIÓN: Apostar UNDER {line} @ {odds_under}")
    else:
        print(f"\n❌ NO APOSTAR - EV insuficiente")


def main():
    """Run examples"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "CÓMO HACER UNA PREDICCIÓN NUEVA" + " " * 27 + "║")
    print("╚" + "=" * 78 + "╝")

    print("""
Este script te muestra el FLUJO COMPLETO para hacer predicciones:

1. 📊 STATS: Obtener estadísticas del jugador (NBA API, etc.)
2. 💰 ODDS: Obtener cuotas actuales (The Odds API)
3. 🎯 PREDICCIÓN: Calcular probabilidades con el modelo
4. 💎 EV: Calcular Expected Value
5. ⭐ RECOMENDACIÓN: Generar pick con URL para apostar
6. 💾 GUARDAR: Almacenar en la base de datos

¡Vamos a verlo en acción!
    """)

    input("Presiona Enter para continuar...")

    # Ejemplo completo
    ejemplo_prediccion_completa()

    # Ejemplo rápido
    ejemplo_prediccion_rapida()

    print("\n\n" + "=" * 80)
    print("RESUMEN: CÓMO HACER PREDICCIONES")
    print("=" * 80)
    print("""
Para hacer tus propias predicciones:

1. **Obtener Stats**:
   ```python
   from src.ingest.nba_scraper import NBAStatsScraper
   scraper = NBAStatsScraper()
   game_log = scraper.get_player_game_log("LeBron James", last_n_games=10)
   avg_points = game_log['PTS'].mean()
   ```

2. **Obtener Odds**:
   ```python
   from src.ingest.odds_collector import MultiBookCollector
   collector = MultiBookCollector(config)
   odds = collector.collect_all_odds(['nba'], ['player_points'])
   ```

3. **Hacer Predicción**:
   ```python
   from src.models.poisson_model import PoissonPropModel
   model = PoissonPropModel()
   prediction = model.predict_value(mean=avg_points, std=std, line=25.5)
   ```

4. **Calcular EV**:
   ```python
   ev = (prob_over * (odds - 1)) - (prob_under * 1)
   ```

5. **Apostar si EV > 5%** con el URL del bookmaker

📚 Más información:
   - docs/FUENTES_DE_DATOS_Y_URLS.md
   - examples/example_odds_with_urls.py
   - src/models/poisson_model.py

🚀 Scripts útiles:
   - python examples/example_hacer_prediccion.py  (este script)
   - python examples/example_odds_with_urls.py    (ver URLs bookmakers)
   - python src/main.py                           (bot completo)
    """)

    print("=" * 80)
    print()


if __name__ == "__main__":
    main()
