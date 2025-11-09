"""NBA data scraper using nba_api"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pandas as pd
import time

try:
    from nba_api.stats.endpoints import (
        playergamelog,
        teamgamelog,
        leaguegamefinder,
        commonplayerinfo,
        playerdashboardbygeneralsplits
    )
    from nba_api.stats.static import players, teams
    NBA_API_AVAILABLE = True
except ImportError:
    NBA_API_AVAILABLE = False
    logging.warning("nba_api not installed. Install with: pip install nba-api")

logger = logging.getLogger(__name__)


class NBAStatsScraper:
    """Scraper for NBA statistics"""

    def __init__(self):
        """Initialize NBA scraper"""
        if not NBA_API_AVAILABLE:
            raise ImportError("nba_api is required for NBA scraper")

        self.all_players = players.get_players()
        self.all_teams = teams.get_teams()

    def get_player_id(self, player_name: str) -> Optional[int]:
        """Get player ID from name

        Args:
            player_name: Player full name

        Returns:
            Player ID or None
        """
        for player in self.all_players:
            if player['full_name'].lower() == player_name.lower():
                return player['id']
        return None

    def get_player_game_log(
        self,
        player_name: str,
        season: str = "2024-25",
        last_n_games: int = 10
    ) -> pd.DataFrame:
        """Get player game log

        Args:
            player_name: Player full name
            season: Season (e.g., "2024-25")
            last_n_games: Number of recent games

        Returns:
            DataFrame with game log
        """
        player_id = self.get_player_id(player_name)
        if not player_id:
            logger.error(f"Player not found: {player_name}")
            return pd.DataFrame()

        try:
            game_log = playergamelog.PlayerGameLog(
                player_id=player_id,
                season=season
            )

            df = game_log.get_data_frames()[0]

            # Get last N games
            if last_n_games:
                df = df.head(last_n_games)

            # Clean and format
            df['GAME_DATE'] = pd.to_datetime(df['GAME_DATE'])

            logger.info(f"Retrieved {len(df)} games for {player_name}")
            return df

        except Exception as e:
            logger.error(f"Error fetching game log for {player_name}: {e}")
            return pd.DataFrame()

    def get_player_season_stats(
        self,
        player_name: str,
        season: str = "2024-25"
    ) -> Dict:
        """Get player season averages

        Args:
            player_name: Player full name
            season: Season

        Returns:
            Dictionary with season stats
        """
        game_log = self.get_player_game_log(player_name, season, last_n_games=None)

        if game_log.empty:
            return {}

        # Calculate averages
        stats = {
            'player_name': player_name,
            'season': season,
            'games_played': len(game_log),
            'avg_minutes': game_log['MIN'].astype(float).mean(),
            'avg_points': game_log['PTS'].mean(),
            'avg_rebounds': game_log['REB'].mean(),
            'avg_assists': game_log['AST'].mean(),
            'avg_steals': game_log['STL'].mean(),
            'avg_blocks': game_log['BLK'].mean(),
            'avg_turnovers': game_log['TOV'].mean(),
            'avg_threes_made': game_log['FG3M'].mean(),
            'avg_threes_attempted': game_log['FG3A'].mean(),
            'avg_pra': (game_log['PTS'] + game_log['REB'] + game_log['AST']).mean(),

            # Standard deviations for variance
            'std_points': game_log['PTS'].std(),
            'std_rebounds': game_log['REB'].std(),
            'std_assists': game_log['AST'].std(),
            'std_pra': (game_log['PTS'] + game_log['REB'] + game_log['AST']).std()
        }

        return stats

    def get_team_pace(self, team_abbrev: str, season: str = "2024-25") -> float:
        """Get team pace (possessions per game)

        Args:
            team_abbrev: Team abbreviation (e.g., 'LAL')
            season: Season

        Returns:
            Team pace
        """
        # Placeholder - would need additional API calls
        # Average NBA pace is around 100
        return 100.0

    def get_upcoming_games(self, days_ahead: int = 7) -> pd.DataFrame:
        """Get upcoming NBA games (placeholder - needs schedule API)

        Args:
            days_ahead: How many days ahead to look

        Returns:
            DataFrame with upcoming games
        """
        # This would require the NBA schedule API
        # For now, return empty DataFrame
        logger.warning("Upcoming games requires NBA schedule API - placeholder")
        return pd.DataFrame()

    def get_player_vs_opponent(
        self,
        player_name: str,
        opponent_abbrev: str,
        season: str = "2024-25"
    ) -> Dict:
        """Get player stats vs specific opponent

        Args:
            player_name: Player name
            opponent_abbrev: Opponent team abbreviation
            season: Season

        Returns:
            Stats vs opponent
        """
        game_log = self.get_player_game_log(player_name, season, last_n_games=None)

        if game_log.empty:
            return {}

        # Filter for opponent
        vs_opponent = game_log[game_log['MATCHUP'].str.contains(opponent_abbrev)]

        if vs_opponent.empty:
            return {}

        return {
            'player_name': player_name,
            'opponent': opponent_abbrev,
            'games': len(vs_opponent),
            'avg_points': vs_opponent['PTS'].mean(),
            'avg_rebounds': vs_opponent['REB'].mean(),
            'avg_assists': vs_opponent['AST'].mean(),
            'avg_pra': (vs_opponent['PTS'] + vs_opponent['REB'] + vs_opponent['AST']).mean()
        }


class NBAFeatureExtractor:
    """Extract features for NBA props modeling"""

    def __init__(self):
        """Initialize feature extractor"""
        self.scraper = NBAStatsScraper()

    def extract_player_features(
        self,
        player_name: str,
        opponent: str,
        home_away: str,
        season: str = "2024-25"
    ) -> Dict:
        """Extract comprehensive features for a player

        Args:
            player_name: Player name
            opponent: Opponent team abbreviation
            home_away: 'home' or 'away'
            season: Season

        Returns:
            Feature dictionary
        """
        # Recent form (last 5, 10, 20 games)
        recent_5 = self.scraper.get_player_game_log(player_name, season, 5)
        recent_10 = self.scraper.get_player_game_log(player_name, season, 10)
        recent_20 = self.scraper.get_player_game_log(player_name, season, 20)

        # Season averages
        season_stats = self.scraper.get_player_season_stats(player_name, season)

        # Vs opponent
        vs_opp = self.scraper.get_player_vs_opponent(player_name, opponent, season)

        features = {
            'player_name': player_name,
            'opponent': opponent,
            'home_away': home_away,

            # Rolling averages
            'pts_l5': recent_5['PTS'].mean() if not recent_5.empty else 0,
            'pts_l10': recent_10['PTS'].mean() if not recent_10.empty else 0,
            'pts_l20': recent_20['PTS'].mean() if not recent_20.empty else 0,

            'reb_l5': recent_5['REB'].mean() if not recent_5.empty else 0,
            'reb_l10': recent_10['REB'].mean() if not recent_10.empty else 0,

            'ast_l5': recent_5['AST'].mean() if not recent_5.empty else 0,
            'ast_l10': recent_10['AST'].mean() if not recent_10.empty else 0,

            'min_l5': recent_5['MIN'].astype(float).mean() if not recent_5.empty else 0,
            'min_l10': recent_10['MIN'].astype(float).mean() if not recent_10.empty else 0,

            # Variance
            'pts_std': season_stats.get('std_points', 0),
            'reb_std': season_stats.get('std_rebounds', 0),
            'ast_std': season_stats.get('std_assists', 0),

            # Season
            'season_avg_pts': season_stats.get('avg_points', 0),
            'season_avg_reb': season_stats.get('avg_rebounds', 0),
            'season_avg_ast': season_stats.get('avg_assists', 0),
            'season_avg_pra': season_stats.get('avg_pra', 0),

            # Vs opponent
            'vs_opp_avg_pts': vs_opp.get('avg_points', 0),
            'vs_opp_games': vs_opp.get('games', 0)
        }

        return features
