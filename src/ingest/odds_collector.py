"""Odds collection from The Odds API and other sources"""

import requests
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import time
import yaml
from pathlib import Path

logger = logging.getLogger(__name__)


class TheOddsAPICollector:
    """Collector for The Odds API"""

    BASE_URL = "https://api.the-odds-api.com/v4"

    SPORT_MAPPINGS = {
        'nba': 'basketball_nba',
        'euroleague': 'basketball_euroleague',
        'laliga': 'soccer_spain_la_liga',
        'atp': 'tennis_atp',
        'wta': 'tennis_wta',
        # Aliases
        'basketball_euroleague': 'basketball_euroleague',
        'basketball_nba': 'basketball_nba'
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


class BookmakerURLBuilder:
    """Build URLs to bookmaker betting pages"""

    def __init__(self, books_config_path: str = None):
        """Initialize URL builder

        Args:
            books_config_path: Path to books.yaml config file
        """
        if books_config_path is None:
            # Default to config/books.yaml
            config_dir = Path(__file__).parent.parent.parent / 'config'
            books_config_path = config_dir / 'books.yaml'

        self.books_config_path = Path(books_config_path)
        self.bookmakers = self._load_bookmakers_config()

    def _load_bookmakers_config(self) -> Dict:
        """Load bookmakers configuration from YAML"""
        try:
            with open(self.books_config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                return config.get('bookmakers', {})
        except Exception as e:
            logger.error(f"Error loading bookmakers config: {e}")
            return {}

    def get_bookmaker_url(self, bookmaker_key: str, sport: str = None) -> str:
        """Get URL for a bookmaker

        Args:
            bookmaker_key: Bookmaker key (e.g., 'bet365', 'pinnacle')
            sport: Optional sport to get specific betting URL

        Returns:
            URL to bookmaker or sport-specific page
        """
        bookmaker = self.bookmakers.get(bookmaker_key)
        if not bookmaker:
            logger.warning(f"Bookmaker {bookmaker_key} not found in config")
            return ""

        # If sport specified, try to get sport-specific URL
        if sport:
            betting_urls = bookmaker.get('betting_urls', {})
            sport_url = betting_urls.get(sport)
            if sport_url:
                return sport_url

        # Return base URL
        return bookmaker.get('url', '')

    def get_bookmaker_name(self, bookmaker_key: str) -> str:
        """Get display name for bookmaker

        Args:
            bookmaker_key: Bookmaker key

        Returns:
            Display name
        """
        bookmaker = self.bookmakers.get(bookmaker_key)
        if not bookmaker:
            return bookmaker_key.replace('_', ' ').title()

        return bookmaker.get('name', bookmaker_key)

    def get_all_bookmaker_urls(self, sport: str = None) -> Dict[str, Dict]:
        """Get URLs for all configured bookmakers

        Args:
            sport: Optional sport filter

        Returns:
            Dictionary with bookmaker info and URLs
        """
        result = {}

        for key, bookmaker in self.bookmakers.items():
            # Filter by sport if specified
            if sport and sport not in bookmaker.get('sports', []):
                continue

            url = self.get_bookmaker_url(key, sport)

            result[key] = {
                'name': bookmaker.get('name'),
                'url': url,
                'type': bookmaker.get('type'),
                'priority': bookmaker.get('priority', 999),
                'the_odds_api_key': bookmaker.get('the_odds_api_key')
            }

        return result

    def match_the_odds_api_key(self, the_odds_api_key: str) -> Optional[str]:
        """Match The Odds API key to our bookmaker key

        Args:
            the_odds_api_key: Key from The Odds API (e.g., 'williamhill')

        Returns:
            Our internal bookmaker key or None
        """
        for key, bookmaker in self.bookmakers.items():
            if bookmaker.get('the_odds_api_key') == the_odds_api_key:
                return key

        # Fallback: try direct match
        if the_odds_api_key in self.bookmakers:
            return the_odds_api_key

        return None


class MultiBookCollector:
    """Aggregate collector for multiple bookmakers"""

    def __init__(self, config: Dict):
        """Initialize multi-book collector

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.collectors = {}
        self.url_builder = BookmakerURLBuilder()

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

                    # Enrich with bookmaker URLs
                    odds = self._enrich_with_urls(odds, sport)

                    all_odds[sport].extend(odds)
                    logger.info(f"Collected {len(odds)} events for {sport} from The Odds API")

                    # Rate limiting
                    time.sleep(1)
                except Exception as e:
                    logger.error(f"Error collecting odds for {sport}: {e}")

        return all_odds

    def _enrich_with_urls(self, odds_data: List[Dict], sport: str) -> List[Dict]:
        """Enrich odds data with bookmaker URLs

        Args:
            odds_data: List of odds from The Odds API
            sport: Sport name

        Returns:
            Enriched odds data with URLs
        """
        for event in odds_data:
            # Add base sport URL for each bookmaker
            for bookmaker_data in event.get('bookmakers', []):
                bookmaker_key = bookmaker_data.get('key', '')

                # Match The Odds API key to our config
                our_key = self.url_builder.match_the_odds_api_key(bookmaker_key)

                if our_key:
                    # Get URL for this bookmaker
                    url = self.url_builder.get_bookmaker_url(our_key, sport)
                    display_name = self.url_builder.get_bookmaker_name(our_key)

                    # Add to bookmaker data
                    bookmaker_data['betting_url'] = url
                    bookmaker_data['display_name'] = display_name
                    bookmaker_data['our_key'] = our_key
                else:
                    logger.debug(f"No URL mapping found for bookmaker: {bookmaker_key}")

        return odds_data

    def get_bookmaker_info_for_event(
        self,
        sport: str,
        event_name: str = None
    ) -> Dict[str, Dict]:
        """Get bookmaker information for an event

        Args:
            sport: Sport name
            event_name: Optional event name for context

        Returns:
            Dictionary with bookmaker info and URLs
        """
        return self.url_builder.get_all_bookmaker_urls(sport)

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
