"""Soccer data scraper for La Liga and other leagues"""

import logging
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import time
import cloudscraper

logger = logging.getLogger(__name__)


class SofaScoreSoccerScraper:
    """Scraper for SofaScore soccer data"""

    BASE_URL = "https://api.sofascore.com/api/v1"

    LEAGUE_IDS = {
        'laliga': 8,  # La Liga
        'premier_league': 17,
        'serie_a': 23,
        'bundesliga': 35
    }

    def __init__(self):
        """Initialize SofaScore scraper"""
        self.session = cloudscraper.create_scraper()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    def get_team_matches(
        self,
        team_id: int,
        season_id: int = None,
        last_n: int = 10
    ) -> List[Dict]:
        """Get team matches

        Args:
            team_id: Team ID
            season_id: Season ID
            last_n: Number of recent matches

        Returns:
            List of matches
        """
        url = f"{self.BASE_URL}/team/{team_id}/events/last/{last_n}"

        try:
            response = self.session.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()

            matches = data.get('events', [])
            logger.info(f"Retrieved {len(matches)} matches for team {team_id}")
            return matches

        except Exception as e:
            logger.error(f"Error fetching team matches: {e}")
            return []

    def get_match_statistics(self, match_id: int) -> Dict:
        """Get detailed match statistics

        Args:
            match_id: Match ID

        Returns:
            Dictionary with match stats
        """
        url = f"{self.BASE_URL}/event/{match_id}/statistics"

        try:
            response = self.session.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()

            # Parse statistics
            stats = {}
            for period in data.get('statistics', []):
                for group in period.get('groups', []):
                    for stat in group.get('statisticsItems', []):
                        stat_name = stat.get('name', '').lower().replace(' ', '_')
                        stats[f"home_{stat_name}"] = stat.get('home')
                        stats[f"away_{stat_name}"] = stat.get('away')

            return stats

        except Exception as e:
            logger.error(f"Error fetching match statistics: {e}")
            return {}

    def get_player_statistics(
        self,
        player_id: int,
        season_id: int
    ) -> Dict:
        """Get player season statistics

        Args:
            player_id: Player ID
            season_id: Season ID

        Returns:
            Player stats dictionary
        """
        url = f"{self.BASE_URL}/player/{player_id}/statistics/season/{season_id}"

        try:
            response = self.session.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()

        except Exception as e:
            logger.error(f"Error fetching player statistics: {e}")
            return {}


class FBrefScraper:
    """Scraper for FBref.com soccer statistics"""

    BASE_URL = "https://fbref.com"

    LEAGUE_URLS = {
        'laliga': '/en/comps/12/La-Liga-Stats',
        'premier_league': '/en/comps/9/Premier-League-Stats',
        'serie_a': '/en/comps/11/Serie-A-Stats',
        'bundesliga': '/en/comps/20/Bundesliga-Stats'
    }

    def __init__(self):
        """Initialize FBref scraper"""
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    def get_team_stats(self, league: str, season: str = "2024-2025") -> pd.DataFrame:
        """Get team statistics from FBref

        Args:
            league: League name (laliga, premier_league, etc.)
            season: Season

        Returns:
            DataFrame with team stats
        """
        league_url = self.LEAGUE_URLS.get(league)
        if not league_url:
            logger.error(f"Unknown league: {league}")
            return pd.DataFrame()

        url = f"{self.BASE_URL}{league_url}"

        try:
            # Rate limiting
            time.sleep(3)

            response = self.session.get(url, headers=self.headers)
            response.raise_for_status()

            # Parse with pandas
            tables = pd.read_html(response.text)

            # Usually the first table is the main stats table
            if tables:
                df = tables[0]
                logger.info(f"Retrieved stats for {len(df)} teams in {league}")
                return df

            return pd.DataFrame()

        except Exception as e:
            logger.error(f"Error scraping FBref: {e}")
            return pd.DataFrame()


class SoccerFeatureExtractor:
    """Extract features for soccer props modeling"""

    def __init__(self):
        """Initialize feature extractor"""
        self.sofascore = SofaScoreSoccerScraper()
        self.fbref = FBrefScraper()

    def extract_team_corner_features(
        self,
        team_id: int,
        opponent_id: int,
        home_away: str,
        last_n_games: int = 10
    ) -> Dict:
        """Extract features for corner predictions

        Args:
            team_id: Team ID
            opponent_id: Opponent team ID
            home_away: 'home' or 'away'
            last_n_games: Number of recent games to analyze

        Returns:
            Feature dictionary
        """
        # Get recent matches
        recent_matches = self.sofascore.get_team_matches(team_id, last_n=last_n_games)

        corner_stats = []
        for match in recent_matches:
            match_id = match.get('id')
            stats = self.sofascore.get_match_statistics(match_id)

            if home_away == 'home':
                corners = stats.get('home_corner_kicks', 0)
            else:
                corners = stats.get('away_corner_kicks', 0)

            if corners:
                corner_stats.append(corners)

            time.sleep(1)  # Rate limiting

        features = {
            'team_id': team_id,
            'opponent_id': opponent_id,
            'home_away': home_away,
            'avg_corners': sum(corner_stats) / len(corner_stats) if corner_stats else 0,
            'std_corners': pd.Series(corner_stats).std() if corner_stats else 0,
            'max_corners': max(corner_stats) if corner_stats else 0,
            'min_corners': min(corner_stats) if corner_stats else 0,
            'games_analyzed': len(corner_stats)
        }

        return features

    def extract_team_card_features(
        self,
        team_id: int,
        last_n_games: int = 10
    ) -> Dict:
        """Extract features for card predictions

        Args:
            team_id: Team ID
            last_n_games: Number of recent games

        Returns:
            Feature dictionary for cards
        """
        recent_matches = self.sofascore.get_team_matches(team_id, last_n=last_n_games)

        yellow_cards = []
        red_cards = []

        for match in recent_matches:
            match_id = match.get('id')
            stats = self.sofascore.get_match_statistics(match_id)

            # Determine if team was home or away
            if match.get('homeTeam', {}).get('id') == team_id:
                yellows = stats.get('home_yellow_cards', 0)
                reds = stats.get('home_red_cards', 0)
            else:
                yellows = stats.get('away_yellow_cards', 0)
                reds = stats.get('away_red_cards', 0)

            if yellows is not None:
                yellow_cards.append(yellows)
            if reds is not None:
                red_cards.append(reds)

            time.sleep(1)

        return {
            'team_id': team_id,
            'avg_yellow_cards': sum(yellow_cards) / len(yellow_cards) if yellow_cards else 0,
            'avg_red_cards': sum(red_cards) / len(red_cards) if red_cards else 0,
            'total_cards_avg': (sum(yellow_cards) + sum(red_cards)) / max(len(yellow_cards), 1)
        }
