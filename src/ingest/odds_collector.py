"""Odds collection from The Odds API and other sources"""

import requests
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import time

logger = logging.getLogger(__name__)


class TheOddsAPICollector:
    """Collector for The Odds API"""

    BASE_URL = "https://api.the-odds-api.com/v4"

    SPORT_MAPPINGS = {
        'nba': 'basketball_nba',
        'euroleague': 'basketball_euroleague',
        'laliga': 'soccer_spain_la_liga',
        'atp': 'tennis_atp',
        'wta': 'tennis_wta'
    }

    def __init__(self, api_key: str):
        """Initialize The Odds API collector

        Args:
            api_key: The Odds API key
        """
        self.api_key = api_key
        self.session = requests.Session()
        self.rate_limit_remaining = None
        self.rate_limit_used = None

    def get_sports(self) -> List[Dict]:
        """Get available sports

        Returns:
            List of available sports
        """
        url = f"{self.BASE_URL}/sports"
        params = {'apiKey': self.api_key}

        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            self._update_rate_limit(response.headers)

            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error fetching sports: {e}")
            return []

    def get_odds(
        self,
        sport: str,
        regions: List[str] = ['eu'],
        markets: List[str] = ['h2h'],
        bookmakers: Optional[List[str]] = None
    ) -> List[Dict]:
        """Get odds for a sport

        Args:
            sport: Sport key (use SPORT_MAPPINGS)
            regions: Regions to get odds from (eu, us, uk, au)
            markets: Market types (h2h, spreads, totals, player_props)
            bookmakers: Specific bookmakers to filter

        Returns:
            List of matches with odds
        """
        sport_key = self.SPORT_MAPPINGS.get(sport, sport)
        url = f"{self.BASE_URL}/sports/{sport_key}/odds"

        params = {
            'apiKey': self.api_key,
            'regions': ','.join(regions),
            'markets': ','.join(markets),
            'oddsFormat': 'decimal',
            'dateFormat': 'iso'
        }

        if bookmakers:
            params['bookmakers'] = ','.join(bookmakers)

        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            self._update_rate_limit(response.headers)

            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error fetching odds for {sport}: {e}")
            return []

    def get_player_props(
        self,
        sport: str,
        event_id: str = None
    ) -> List[Dict]:
        """Get player prop odds

        Args:
            sport: Sport key
            event_id: Specific event ID (optional)

        Returns:
            List of player prop markets
        """
        sport_key = self.SPORT_MAPPINGS.get(sport, sport)

        if event_id:
            url = f"{self.BASE_URL}/sports/{sport_key}/events/{event_id}/odds"
        else:
            url = f"{self.BASE_URL}/sports/{sport_key}/odds"

        params = {
            'apiKey': self.api_key,
            'regions': 'eu,us',
            'markets': 'player_points,player_rebounds,player_assists,player_threes',
            'oddsFormat': 'decimal',
            'dateFormat': 'iso'
        }

        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            self._update_rate_limit(response.headers)

            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error fetching player props for {sport}: {e}")
            return []

    def _update_rate_limit(self, headers: Dict):
        """Update rate limit info from response headers"""
        if 'x-requests-remaining' in headers:
            self.rate_limit_remaining = int(headers['x-requests-remaining'])
            logger.info(f"Rate limit remaining: {self.rate_limit_remaining}")

        if 'x-requests-used' in headers:
            self.rate_limit_used = int(headers['x-requests-used'])

    def get_rate_limit_info(self) -> Dict:
        """Get current rate limit information"""
        return {
            'remaining': self.rate_limit_remaining,
            'used': self.rate_limit_used
        }


class BetfairCollector:
    """Collector for Betfair Exchange (placeholder - requires full API integration)"""

    def __init__(self, username: str, password: str, app_key: str):
        """Initialize Betfair collector

        Args:
            username: Betfair username
            password: Betfair password
            app_key: Betfair application key
        """
        self.username = username
        self.password = password
        self.app_key = app_key
        self.session_token = None

    def login(self):
        """Login to Betfair - placeholder"""
        logger.warning("Betfair integration is a placeholder - implement full API")
        # TODO: Implement full Betfair API integration
        pass

    def get_market_odds(self, market_id: str):
        """Get market odds - placeholder"""
        logger.warning("Betfair integration is a placeholder")
        return {}


class MultiBookCollector:
    """Aggregate collector for multiple bookmakers"""

    def __init__(self, config: Dict):
        """Initialize multi-book collector

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.collectors = {}

        # Initialize The Odds API if configured
        if config.get('the_odds_api', {}).get('enabled'):
            api_key = config['the_odds_api'].get('api_key')
            if api_key and not api_key.startswith('${'):
                self.collectors['the_odds_api'] = TheOddsAPICollector(api_key)

    def collect_all_odds(
        self,
        sports: List[str],
        markets: List[str] = ['h2h', 'totals']
    ) -> Dict[str, List[Dict]]:
        """Collect odds from all configured sources

        Args:
            sports: List of sports to collect
            markets: Market types to collect

        Returns:
            Dictionary mapping sport -> odds data
        """
        all_odds = {}

        for sport in sports:
            all_odds[sport] = []

            # Collect from The Odds API
            if 'the_odds_api' in self.collectors:
                try:
                    odds = self.collectors['the_odds_api'].get_odds(
                        sport=sport,
                        markets=markets
                    )
                    all_odds[sport].extend(odds)
                    logger.info(f"Collected {len(odds)} events for {sport} from The Odds API")

                    # Rate limiting
                    time.sleep(1)
                except Exception as e:
                    logger.error(f"Error collecting odds for {sport}: {e}")

        return all_odds

    def get_best_odds(self, odds_list: List[Dict]) -> Dict:
        """Find best odds across bookmakers

        Args:
            odds_list: List of odds from different bookmakers

        Returns:
            Best odds available
        """
        if not odds_list:
            return {}

        best = {
            'over': {'odds': 0, 'bookmaker': None},
            'under': {'odds': 0, 'bookmaker': None}
        }

        for odd in odds_list:
            for market in odd.get('bookmakers', []):
                for outcome in market.get('markets', []):
                    for price in outcome.get('outcomes', []):
                        if price['name'] == 'Over':
                            if price['price'] > best['over']['odds']:
                                best['over'] = {
                                    'odds': price['price'],
                                    'bookmaker': market['key']
                                }
                        elif price['name'] == 'Under':
                            if price['price'] > best['under']['odds']:
                                best['under'] = {
                                    'odds': price['price'],
                                    'bookmaker': market['key']
                                }

        return best
