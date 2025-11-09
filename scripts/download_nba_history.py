"""Download NBA historical data"""

import sys
from pathlib import Path
import argparse
import time
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from utils import load_config, setup_logging
from ingest.nba_scraper import NBAStatsScraper
from database import get_session, PlayerStats
import pandas as pd
import logging

logger = logging.getLogger(__name__)


def download_player_season(
    scraper: NBAStatsScraper,
    player_name: str,
    season: str,
    save_dir: Path
):
    """Download full season for a player

    Args:
        scraper: NBA scraper instance
        player_name: Player full name
        season: Season (e.g., "2024-25")
        save_dir: Directory to save data
    """
    logger.info(f"Downloading {player_name} - {season}...")

    try:
        # Get game log
        game_log = scraper.get_player_game_log(
            player_name=player_name,
            season=season,
            last_n_games=None  # All games
        )

        if game_log.empty:
            logger.warning(f"No data for {player_name} in {season}")
            return

        # Save to CSV
        filename = f"{player_name.replace(' ', '_')}_{season}.csv"
        filepath = save_dir / filename

        game_log.to_csv(filepath, index=False)
        logger.info(f"Saved {len(game_log)} games to {filepath}")

        # Rate limiting
        time.sleep(1)

    except Exception as e:
        logger.error(f"Error downloading {player_name}: {e}")


def download_top_players(
    seasons: list,
    n_players: int = 50,
    output_dir: str = 'data/raw/nba'
):
    """Download historical data for top NBA players

    Args:
        seasons: List of seasons to download (e.g., ["2023-24", "2024-25"])
        n_players: Number of top players to download
        output_dir: Output directory
    """
    logger.info("=" * 60)
    logger.info("NBA HISTORICAL DATA DOWNLOAD")
    logger.info("=" * 60)

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Initialize scraper
    scraper = NBAStatsScraper()

    # Top players to track (manually curated list)
    # In production, could get this from all-star rosters or top scorers
    top_players = [
        # Current superstars
        "LeBron James",
        "Stephen Curry",
        "Kevin Durant",
        "Giannis Antetokounmpo",
        "Luka Doncic",
        "Nikola Jokic",
        "Joel Embiid",
        "Jayson Tatum",
        "Damian Lillard",
        "Anthony Davis",

        # All-stars
        "Devin Booker",
        "Donovan Mitchell",
        "Trae Young",
        "Jimmy Butler",
        "Kawhi Leonard",
        "Paul George",
        "Anthony Edwards",
        "De'Aaron Fox",
        "Tyrese Haliburton",
        "Shai Gilgeous-Alexander",

        # Rising stars
        "Paolo Banchero",
        "Franz Wagner",
        "Scottie Barnes",
        "Cade Cunningham",
        "Jalen Green",
        "Evan Mobley",
        "LaMelo Ball",
        "Ja Morant",
        "Zion Williamson",
        "Victor Wembanyama"
    ][:n_players]

    logger.info(f"Downloading data for {len(top_players)} players")
    logger.info(f"Seasons: {seasons}")

    total_downloads = 0

    for season in seasons:
        season_dir = output_path / season
        season_dir.mkdir(exist_ok=True)

        logger.info(f"\n📅 Season: {season}")
        logger.info("-" * 60)

        for player in top_players:
            download_player_season(scraper, player, season, season_dir)
            total_downloads += 1

            # Progress
            if total_downloads % 10 == 0:
                logger.info(f"Progress: {total_downloads} / {len(top_players) * len(seasons)}")

    logger.info("\n" + "=" * 60)
    logger.info(f"✅ Download complete! {total_downloads} player-seasons downloaded")
    logger.info(f"📁 Data saved to: {output_path}")


def import_to_database(data_dir: str = 'data/raw/nba'):
    """Import downloaded data to database

    Args:
        data_dir: Directory with downloaded CSVs
    """
    logger.info("\n" + "=" * 60)
    logger.info("IMPORTING TO DATABASE")
    logger.info("=" * 60)

    session = get_session()
    data_path = Path(data_dir)

    total_imported = 0

    for csv_file in data_path.rglob("*.csv"):
        logger.info(f"Importing {csv_file.name}...")

        try:
            df = pd.read_csv(csv_file)

            for _, row in df.iterrows():
                # Create PlayerStats record
                stat = PlayerStats(
                    player_name=row.get('Player_Name', ''),
                    sport='basketball',
                    league='nba',
                    season=row.get('SEASON_ID', ''),
                    game_date=pd.to_datetime(row.get('GAME_DATE')) if 'GAME_DATE' in row else None,
                    opponent=row.get('MATCHUP', '').split()[-1] if 'MATCHUP' in row else '',
                    home_away='home' if '@' not in str(row.get('MATCHUP', '')) else 'away',

                    # Basketball stats
                    minutes=float(row.get('MIN', 0)) if pd.notna(row.get('MIN')) else None,
                    points=int(row.get('PTS', 0)) if pd.notna(row.get('PTS')) else None,
                    rebounds=int(row.get('REB', 0)) if pd.notna(row.get('REB')) else None,
                    assists=int(row.get('AST', 0)) if pd.notna(row.get('AST')) else None,
                    steals=int(row.get('STL', 0)) if pd.notna(row.get('STL')) else None,
                    blocks=int(row.get('BLK', 0)) if pd.notna(row.get('BLK')) else None,
                    turnovers=int(row.get('TOV', 0)) if pd.notna(row.get('TOV')) else None,
                    threes_made=int(row.get('FG3M', 0)) if pd.notna(row.get('FG3M')) else None,
                    threes_attempted=int(row.get('FG3A', 0)) if pd.notna(row.get('FG3A')) else None
                )

                session.add(stat)
                total_imported += 1

            # Commit every file
            session.commit()

        except Exception as e:
            logger.error(f"Error importing {csv_file}: {e}")
            session.rollback()

    session.close()

    logger.info(f"\n✅ Imported {total_imported} records to database")


def main():
    """Main download function"""
    parser = argparse.ArgumentParser(description="Download NBA historical data")
    parser.add_argument(
        '--seasons',
        nargs='+',
        default=['2023-24', '2024-25'],
        help='Seasons to download (e.g., 2023-24 2024-25)'
    )
    parser.add_argument(
        '--players',
        type=int,
        default=30,
        help='Number of top players to download'
    )
    parser.add_argument(
        '--import-db',
        action='store_true',
        help='Import downloaded data to database'
    )

    args = parser.parse_args()

    config = load_config()
    setup_logging(
        log_level=config['general']['log_level'],
        log_file='logs/nba_download.log'
    )

    # Download
    download_top_players(
        seasons=args.seasons,
        n_players=args.players
    )

    # Import to database
    if args.import_db:
        import_to_database()

    logger.info("\n🎯 Next steps:")
    logger.info("1. Verify data in data/raw/nba/")
    logger.info("2. Run calibration: python scripts/calibrate_models.py")
    logger.info("3. Test predictions: python scripts/run_predictions.py")


if __name__ == "__main__":
    main()
