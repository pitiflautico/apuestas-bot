"""Master script to populate all historical data"""

import sys
from pathlib import Path
import argparse
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from utils import load_config, setup_logging
from database import init_db
import logging

logger = logging.getLogger(__name__)


def populate_nba_data(seasons: list):
    """Populate NBA historical data

    Args:
        seasons: List of seasons
    """
    logger.info("📊 Populating NBA data...")

    from ingest.nba_scraper import NBAStatsScraper

    scraper = NBAStatsScraper()

    # Top 20 players for quick demo
    demo_players = [
        "LeBron James",
        "Stephen Curry",
        "Luka Doncic",
        "Nikola Jokic",
        "Giannis Antetokounmpo",
        "Joel Embiid",
        "Jayson Tatum",
        "Kevin Durant",
        "Damian Lillard",
        "Anthony Davis",
        "Devin Booker",
        "Trae Young",
        "Donovan Mitchell",
        "Anthony Edwards",
        "Shai Gilgeous-Alexander"
    ]

    total_collected = 0

    for season in seasons:
        logger.info(f"  Season: {season}")

        for player in demo_players:
            try:
                game_log = scraper.get_player_game_log(player, season, last_n_games=10)

                if not game_log.empty:
                    total_collected += len(game_log)
                    logger.info(f"    ✓ {player}: {len(game_log)} games")

                # Rate limiting
                import time
                time.sleep(1)

            except Exception as e:
                logger.error(f"    ✗ {player}: {e}")

    logger.info(f"  Total NBA games collected: {total_collected}")
    return total_collected


def populate_laliga_data():
    """Populate La Liga historical data"""
    logger.info("⚽ Populating La Liga data...")

    # Would use soccer scraper here
    # For now, just log
    logger.info("  La Liga data collection: DEMO MODE")
    logger.info("  In production: would scrape FBref + SofaScore")

    return 0


def populate_tennis_data():
    """Populate Tennis historical data"""
    logger.info("🎾 Populating Tennis data...")

    # Would use tennis scraper here
    logger.info("  Tennis data collection: DEMO MODE")
    logger.info("  In production: would scrape SofaScore + Tennis Abstract")

    return 0


def populate_acb_data():
    """Populate ACB historical data"""
    logger.info("🏀 Populating ACB data...")

    logger.info("  ACB data collection: DEMO MODE")
    logger.info("  In production: would use SofaScore API")

    return 0


def generate_summary_stats(config: dict):
    """Generate summary statistics of populated data

    Args:
        config: Configuration dictionary
    """
    from database import get_session, PlayerStats, TeamStats

    session = get_session()

    # Count records
    player_stats_count = session.query(PlayerStats).count()
    team_stats_count = session.query(TeamStats).count()

    logger.info("\n" + "=" * 60)
    logger.info("DATABASE SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Player stats records: {player_stats_count}")
    logger.info(f"Team stats records: {team_stats_count}")

    # Stats by sport
    if player_stats_count > 0:
        from sqlalchemy import func

        sports = session.query(
            PlayerStats.sport,
            func.count(PlayerStats.id)
        ).group_by(PlayerStats.sport).all()

        logger.info("\nRecords by sport:")
        for sport, count in sports:
            logger.info(f"  {sport}: {count}")

    session.close()


def main():
    """Main population function"""
    parser = argparse.ArgumentParser(description="Populate historical sports data")
    parser.add_argument(
        '--sports',
        nargs='+',
        default=['nba', 'laliga', 'tennis', 'acb'],
        choices=['nba', 'laliga', 'tennis', 'acb'],
        help='Sports to populate'
    )
    parser.add_argument(
        '--seasons',
        nargs='+',
        default=['2023-24', '2024-25'],
        help='Seasons to download'
    )
    parser.add_argument(
        '--quick',
        action='store_true',
        help='Quick mode: only last 10 games per player'
    )

    args = parser.parse_args()

    config = load_config()
    setup_logging(
        log_level=config['general']['log_level'],
        log_file='logs/populate_data.log'
    )

    logger.info("=" * 60)
    logger.info("POPULATING HISTORICAL DATA")
    logger.info("=" * 60)
    logger.info(f"Sports: {args.sports}")
    logger.info(f"Seasons: {args.seasons}")
    logger.info(f"Quick mode: {args.quick}")
    logger.info("")

    # Initialize database
    logger.info("Initializing database...")
    init_db()

    total_records = 0

    # Populate each sport
    if 'nba' in args.sports:
        nba_records = populate_nba_data(args.seasons)
        total_records += nba_records

    if 'laliga' in args.sports:
        laliga_records = populate_laliga_data()
        total_records += laliga_records

    if 'tennis' in args.sports:
        tennis_records = populate_tennis_data()
        total_records += tennis_records

    if 'acb' in args.sports:
        acb_records = populate_acb_data()
        total_records += acb_records

    # Generate summary
    generate_summary_stats(config)

    logger.info("\n" + "=" * 60)
    logger.info("POPULATION COMPLETE")
    logger.info("=" * 60)
    logger.info(f"✅ Total records populated: {total_records}")

    logger.info("\n🎯 Next steps:")
    logger.info("1. Verify data: sqlite3 data/results/sports_bot.db")
    logger.info("2. Calibrate models: python scripts/calibrate_models.py")
    logger.info("3. Run predictions: python scripts/run_predictions.py")
    logger.info("4. Launch dashboard: streamlit run app.py")


if __name__ == "__main__":
    main()
