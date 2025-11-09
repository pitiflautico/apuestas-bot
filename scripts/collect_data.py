"""Script to collect data from all sources"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from utils import load_config, setup_logging
from ingest.odds_collector import MultiBookCollector
from database import init_db, get_session
import logging

logger = logging.getLogger(__name__)


def main():
    """Main data collection function"""
    # Load config
    config = load_config()
    setup_logging(
        log_level=config['general']['log_level'],
        log_file=config['general']['log_file']
    )

    logger.info("Starting data collection...")

    # Initialize database
    init_db()

    # Initialize odds collector
    odds_config = config.get('data_sources', {}).get('odds', {})
    collector = MultiBookCollector(odds_config)

    # Collect odds for enabled sports
    sports_to_collect = []

    if config['sports']['basketball']['nba']['enabled']:
        sports_to_collect.append('nba')

    if config['sports']['soccer']['laliga']['enabled']:
        sports_to_collect.append('laliga')

    if config['sports']['tennis']['atp']['enabled']:
        sports_to_collect.append('atp')

    if config['sports']['tennis']['wta']['enabled']:
        sports_to_collect.append('wta')

    logger.info(f"Collecting odds for: {sports_to_collect}")

    # Collect odds
    all_odds = collector.collect_all_odds(
        sports=sports_to_collect,
        markets=['h2h', 'totals', 'player_points', 'player_rebounds', 'player_assists']
    )

    # Log results
    for sport, odds in all_odds.items():
        logger.info(f"Collected {len(odds)} events for {sport}")

    # TODO: Store odds in database

    logger.info("Data collection completed!")


if __name__ == "__main__":
    main()
