"""Feature engineering for sports props"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class FeatureEngineer:
    """Base feature engineering class"""

    def __init__(self, config: Dict):
        """Initialize feature engineer

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.rolling_windows = config.get('features', {}).get('rolling_windows', [5, 10, 20])
        self.min_sample_size = config.get('features', {}).get('min_sample_size', 5)
        self.outlier_threshold = config.get('features', {}).get('outlier_threshold', 3.0)

    def create_rolling_features(
        self,
        df: pd.DataFrame,
        metric_col: str,
        windows: List[int] = None
    ) -> pd.DataFrame:
        """Create rolling window features

        Args:
            df: DataFrame with time series data
            metric_col: Column name for the metric
            windows: List of window sizes (uses config default if None)

        Returns:
            DataFrame with rolling features
        """
        if windows is None:
            windows = self.rolling_windows

        result = df.copy()

        for window in windows:
            # Rolling mean
            result[f'{metric_col}_mean_{window}'] = (
                result[metric_col].rolling(window=window, min_periods=1).mean()
            )

            # Rolling std
            result[f'{metric_col}_std_{window}'] = (
                result[metric_col].rolling(window=window, min_periods=1).std()
            )

            # Rolling max
            result[f'{metric_col}_max_{window}'] = (
                result[metric_col].rolling(window=window, min_periods=1).max()
            )

            # Rolling min
            result[f'{metric_col}_min_{window}'] = (
                result[metric_col].rolling(window=window, min_periods=1).min()
            )

        return result

    def create_lag_features(
        self,
        df: pd.DataFrame,
        metric_col: str,
        lags: List[int] = [1, 2, 3, 5]
    ) -> pd.DataFrame:
        """Create lagged features

        Args:
            df: DataFrame with time series data
            metric_col: Column name for the metric
            lags: List of lag values

        Returns:
            DataFrame with lag features
        """
        result = df.copy()

        for lag in lags:
            result[f'{metric_col}_lag_{lag}'] = result[metric_col].shift(lag)

        return result

    def create_trend_features(
        self,
        df: pd.DataFrame,
        metric_col: str
    ) -> pd.DataFrame:
        """Create trend features

        Args:
            df: DataFrame with time series data
            metric_col: Column name for the metric

        Returns:
            DataFrame with trend features
        """
        result = df.copy()

        # Linear trend over last 5 games
        result[f'{metric_col}_trend_5'] = (
            result[metric_col].rolling(window=5, min_periods=2)
            .apply(lambda x: np.polyfit(np.arange(len(x)), x, 1)[0] if len(x) >= 2 else 0)
        )

        # Momentum (current vs mean of last 10)
        mean_10 = result[metric_col].rolling(window=10, min_periods=1).mean()
        result[f'{metric_col}_momentum'] = result[metric_col] / mean_10.replace(0, 1)

        return result

    def remove_outliers(
        self,
        df: pd.DataFrame,
        metric_col: str,
        method: str = 'zscore'
    ) -> pd.DataFrame:
        """Remove or cap outliers

        Args:
            df: DataFrame
            metric_col: Column name for the metric
            method: Method to use ('zscore' or 'iqr')

        Returns:
            DataFrame with outliers handled
        """
        result = df.copy()

        if method == 'zscore':
            mean = result[metric_col].mean()
            std = result[metric_col].std()

            # Cap outliers at threshold standard deviations
            lower_bound = mean - self.outlier_threshold * std
            upper_bound = mean + self.outlier_threshold * std

            result[metric_col] = result[metric_col].clip(lower=lower_bound, upper=upper_bound)

        elif method == 'iqr':
            Q1 = result[metric_col].quantile(0.25)
            Q3 = result[metric_col].quantile(0.75)
            IQR = Q3 - Q1

            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR

            result[metric_col] = result[metric_col].clip(lower=lower_bound, upper=upper_bound)

        return result


class BasketballFeatureEngineer(FeatureEngineer):
    """Feature engineering for basketball props"""

    def create_player_features(
        self,
        game_log: pd.DataFrame,
        opponent_stats: Optional[Dict] = None
    ) -> Dict:
        """Create comprehensive player features

        Args:
            game_log: Player game log DataFrame
            opponent_stats: Optional opponent defensive stats

        Returns:
            Feature dictionary
        """
        if game_log.empty or len(game_log) < self.min_sample_size:
            logger.warning("Insufficient sample size for feature creation")
            return {}

        # Create rolling features for key metrics
        metrics = ['PTS', 'REB', 'AST', 'MIN']
        featured_df = game_log.copy()

        for metric in metrics:
            if metric in featured_df.columns:
                featured_df = self.create_rolling_features(featured_df, metric)
                featured_df = self.create_trend_features(featured_df, metric)

        # Extract latest features
        latest = featured_df.iloc[0]

        features = {
            # Points
            'pts_mean_5': latest.get('PTS_mean_5', 0),
            'pts_mean_10': latest.get('PTS_mean_10', 0),
            'pts_std_5': latest.get('PTS_std_5', 0),
            'pts_trend_5': latest.get('PTS_trend_5', 0),

            # Rebounds
            'reb_mean_5': latest.get('REB_mean_5', 0),
            'reb_mean_10': latest.get('REB_mean_10', 0),

            # Assists
            'ast_mean_5': latest.get('AST_mean_5', 0),
            'ast_mean_10': latest.get('AST_mean_10', 0),

            # Minutes (crucial for props)
            'min_mean_5': latest.get('MIN_mean_5', 0),
            'min_mean_10': latest.get('MIN_mean_10', 0),
            'min_std_5': latest.get('MIN_std_5', 0),

            # Combined metrics
            'pra_mean_5': (
                latest.get('PTS_mean_5', 0) +
                latest.get('REB_mean_5', 0) +
                latest.get('AST_mean_5', 0)
            ),

            # Usage and efficiency
            'pts_per_min': latest.get('PTS_mean_5', 0) / max(latest.get('MIN_mean_5', 1), 1),

            # Sample size
            'games_played': len(game_log)
        }

        # Opponent adjustment
        if opponent_stats:
            features['opp_def_rating'] = opponent_stats.get('defensive_rating', 100)
            features['opp_pace'] = opponent_stats.get('pace', 100)

        return features


class SoccerFeatureEngineer(FeatureEngineer):
    """Feature engineering for soccer props"""

    def create_team_corner_features(
        self,
        team_games: pd.DataFrame,
        opponent_games: Optional[pd.DataFrame] = None
    ) -> Dict:
        """Create features for corner predictions

        Args:
            team_games: Team's recent games DataFrame
            opponent_games: Opponent's recent games DataFrame

        Returns:
            Feature dictionary
        """
        if team_games.empty:
            return {}

        featured_df = self.create_rolling_features(team_games, 'corners')

        latest = featured_df.iloc[0]

        features = {
            'corners_mean_5': latest.get('corners_mean_5', 0),
            'corners_mean_10': latest.get('corners_mean_10', 0),
            'corners_std_5': latest.get('corners_std_5', 0),
            'corners_max_10': latest.get('corners_max_10', 0),
            'corners_min_10': latest.get('corners_min_10', 0),
            'games_played': len(team_games)
        }

        # Opponent conceded corners
        if opponent_games is not None and not opponent_games.empty:
            features['opp_corners_conceded_mean'] = opponent_games['corners_conceded'].mean()

        return features

    def create_team_card_features(
        self,
        team_games: pd.DataFrame
    ) -> Dict:
        """Create features for card predictions

        Args:
            team_games: Team's recent games DataFrame

        Returns:
            Feature dictionary
        """
        if team_games.empty:
            return {}

        # Create rolling features for cards
        if 'yellow_cards' in team_games.columns:
            featured_df = self.create_rolling_features(team_games, 'yellow_cards')
        else:
            featured_df = team_games.copy()

        latest = featured_df.iloc[0]

        features = {
            'yellow_cards_mean_5': latest.get('yellow_cards_mean_5', 0),
            'yellow_cards_mean_10': latest.get('yellow_cards_mean_10', 0),
            'total_cards_mean_5': latest.get('yellow_cards_mean_5', 0) + latest.get('red_cards', 0),
            'games_played': len(team_games)
        }

        return features


class TennisFeatureEngineer(FeatureEngineer):
    """Feature engineering for tennis props"""

    def create_player_ace_features(
        self,
        player_matches: pd.DataFrame,
        surface: str
    ) -> Dict:
        """Create features for ace predictions

        Args:
            player_matches: Player's recent matches DataFrame
            surface: Court surface (hard, clay, grass)

        Returns:
            Feature dictionary
        """
        if player_matches.empty:
            return {}

        # Filter by surface if possible
        if 'surface' in player_matches.columns:
            surface_matches = player_matches[player_matches['surface'] == surface]
            if not surface_matches.empty:
                player_matches = surface_matches

        # Create rolling features
        featured_df = self.create_rolling_features(player_matches, 'aces')

        latest = featured_df.iloc[0]

        features = {
            'aces_mean_5': latest.get('aces_mean_5', 0),
            'aces_mean_10': latest.get('aces_mean_10', 0),
            'aces_std_5': latest.get('aces_std_5', 0),
            'aces_max_10': latest.get('aces_max_10', 0),
            'surface': surface,
            'matches_played': len(player_matches)
        }

        # Surface factor
        surface_factors = {
            'grass': 1.15,
            'hard': 1.0,
            'clay': 0.85
        }

        features['surface_factor'] = surface_factors.get(surface.lower(), 1.0)

        return features
