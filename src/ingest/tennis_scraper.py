"""Tennis data scraper for ATP and WTA"""

import logging
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import time
import cloudscraper

logger = logging.getLogger(__name__)


class FlashScoreTennisScraper:
    """Scraper for FlashScore tennis data"""

    BASE_URL = "https://www.flashscore.com"

    def __init__(self):
        """Initialize FlashScore scraper"""
        self.scraper = cloudscraper.create_scraper()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    def get_player_matches(
        self,
        player_name: str,
        last_n: int = 10
    ) -> List[Dict]:
        """Get player recent matches (placeholder)

        Args:
            player_name: Player name
            last_n: Number of recent matches

        Returns:
            List of matches
        """
        # FlashScore requires dynamic scraping - this is a placeholder
        logger.warning("FlashScore scraping requires browser automation")
        return []


class SofaScoreTennisScraper:
    """Scraper for SofaScore tennis data"""

    BASE_URL = "https://api.sofascore.com/api/v1"

    def __init__(self):
        """Initialize SofaScore tennis scraper"""
        self.session = cloudscraper.create_scraper()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    def get_player_matches(
        self,
        player_id: int,
        last_n: int = 10
    ) -> List[Dict]:
        """Get player matches

        Args:
            player_id: Player ID
            last_n: Number of recent matches

        Returns:
            List of matches
        """
        url = f"{self.BASE_URL}/player/{player_id}/events/last/{last_n}"

        try:
            response = self.session.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()

            matches = data.get('events', [])
            logger.info(f"Retrieved {len(matches)} matches for player {player_id}")
            return matches

        except Exception as e:
            logger.error(f"Error fetching player matches: {e}")
            return []

    def get_match_statistics(self, match_id: int) -> Dict:
        """Get detailed match statistics

        Args:
            match_id: Match ID

        Returns:
            Dictionary with match stats including aces, double faults, etc.
        """
        url = f"{self.BASE_URL}/event/{match_id}/statistics"

        try:
            response = self.session.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()

            stats = {}
            for period in data.get('statistics', []):
                for group in period.get('groups', []):
                    for stat in group.get('statisticsItems', []):
                        stat_name = stat.get('name', '').lower().replace(' ', '_')
                        stats[f"player1_{stat_name}"] = stat.get('home')
                        stats[f"player2_{stat_name}"] = stat.get('away')

            return stats

        except Exception as e:
            logger.error(f"Error fetching match statistics: {e}")
            return {}

    def get_player_stats_by_surface(
        self,
        player_id: int,
        surface: str,
        season: int = 2024
    ) -> Dict:
        """Get player stats filtered by surface

        Args:
            player_id: Player ID
            surface: Surface type (hard, clay, grass)
            season: Season year

        Returns:
            Stats by surface
        """
        # This would require filtering matches by surface
        # Placeholder implementation
        logger.warning("Surface filtering requires additional API calls")
        return {}


class TennisFeatureExtractor:
    """Extract features for tennis props modeling"""

    def __init__(self):
        """Initialize feature extractor"""
        self.sofascore = SofaScoreTennisScraper()

    def extract_player_ace_features(
        self,
        player_id: int,
        opponent_id: int,
        surface: str,
        last_n_matches: int = 10
    ) -> Dict:
        """Extract features for ace predictions

        Args:
            player_id: Player ID
            opponent_id: Opponent player ID
            surface: Court surface (hard, clay, grass)
            last_n_matches: Number of recent matches to analyze

        Returns:
            Feature dictionary
        """
        # Get recent matches
        recent_matches = self.sofascore.get_player_matches(player_id, last_n=last_n_matches)

        ace_stats = []
        df_stats = []  # double faults
        service_games = []

        for match in recent_matches:
            match_id = match.get('id')
            stats = self.sofascore.get_match_statistics(match_id)

            # Determine which player stats to use
            if match.get('homeTeam', {}).get('id') == player_id:
                aces = stats.get('player1_aces', 0)
                dfs = stats.get('player1_double_faults', 0)
                first_serve = stats.get('player1_first_serve_percentage', 0)
            else:
                aces = stats.get('player2_aces', 0)
                dfs = stats.get('player2_double_faults', 0)
                first_serve = stats.get('player2_first_serve_percentage', 0)

            if aces is not None:
                ace_stats.append(aces)
            if dfs is not None:
                df_stats.append(dfs)

            time.sleep(1)  # Rate limiting

        features = {
            'player_id': player_id,
            'opponent_id': opponent_id,
            'surface': surface,

            # Ace stats
            'avg_aces': sum(ace_stats) / len(ace_stats) if ace_stats else 0,
            'std_aces': pd.Series(ace_stats).std() if ace_stats else 0,
            'max_aces': max(ace_stats) if ace_stats else 0,
            'min_aces': min(ace_stats) if ace_stats else 0,

            # Double fault stats
            'avg_double_faults': sum(df_stats) / len(df_stats) if df_stats else 0,
            'std_double_faults': pd.Series(df_stats).std() if df_stats else 0,

            # Sample size
            'matches_analyzed': len(ace_stats)
        }

        # Surface adjustments (would need historical data)
        surface_factors = {
            'grass': 1.15,  # More aces on grass
            'hard': 1.0,
            'clay': 0.85  # Fewer aces on clay
        }

        features['surface_factor'] = surface_factors.get(surface.lower(), 1.0)
        features['surface_adjusted_aces'] = features['avg_aces'] * features['surface_factor']

        return features

    def extract_player_games_features(
        self,
        player_id: int,
        opponent_id: int,
        last_n_matches: int = 10
    ) -> Dict:
        """Extract features for total games predictions

        Args:
            player_id: Player ID
            opponent_id: Opponent player ID
            last_n_matches: Number of recent matches

        Returns:
            Feature dictionary for total games
        """
        recent_matches = self.sofascore.get_player_matches(player_id, last_n=last_n_matches)

        games_played = []

        for match in recent_matches:
            # Calculate total games from score
            # This would need score parsing
            # Placeholder
            pass

        return {
            'player_id': player_id,
            'opponent_id': opponent_id,
            'avg_games_played': 0,  # Placeholder
            'matches_analyzed': len(recent_matches)
        }


class TennisAbstractScraper:
    """Scraper for Tennis Abstract data (advanced stats)"""

    BASE_URL = "http://www.tennisabstract.com"

    def __init__(self):
        """Initialize Tennis Abstract scraper"""
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    def get_player_stats(self, player_name: str) -> Dict:
        """Get player stats from Tennis Abstract

        Args:
            player_name: Player name

        Returns:
            Stats dictionary
        """
        # Tennis Abstract has great stats but requires web scraping
        # Placeholder implementation
        logger.warning("Tennis Abstract scraping requires detailed implementation")
        return {}
