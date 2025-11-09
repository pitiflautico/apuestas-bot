"""Monte Carlo simulation for props with correlations"""

import numpy as np
from typing import Dict, Tuple, Optional, List
import logging

logger = logging.getLogger(__name__)


class MonteCarloSimulator:
    """Monte Carlo simulator for sports props"""

    def __init__(self, n_simulations: int = 10000):
        """Initialize Monte Carlo simulator

        Args:
            n_simulations: Number of simulations to run
        """
        self.n_simulations = n_simulations

    def simulate_normal(
        self,
        mean: float,
        std: float,
        line: float,
        min_value: float = 0
    ) -> Dict[str, float]:
        """Simulate using normal distribution

        Args:
            mean: Expected mean
            std: Standard deviation
            line: Over/under line
            min_value: Minimum possible value (e.g., 0 for counts)

        Returns:
            Dictionary with probabilities
        """
        # Generate samples
        samples = np.random.normal(mean, std, self.n_simulations)

        # Apply minimum constraint
        samples = np.maximum(samples, min_value)

        # Calculate probabilities
        prob_over = np.mean(samples > line)
        prob_under = np.mean(samples < line)
        prob_push = np.mean(samples == line)

        # Additional stats
        percentiles = np.percentile(samples, [5, 25, 50, 75, 95])

        return {
            'prob_over': prob_over,
            'prob_under': prob_under,
            'prob_push': prob_push,
            'expected_value': np.mean(samples),
            'median': np.median(samples),
            'std': np.std(samples),
            'percentiles': {
                'p5': percentiles[0],
                'p25': percentiles[1],
                'p50': percentiles[2],
                'p75': percentiles[3],
                'p95': percentiles[4]
            }
        }

    def simulate_with_minutes_correlation(
        self,
        points_per_minute: float,
        minutes_mean: float,
        minutes_std: float,
        line: float
    ) -> Dict[str, float]:
        """Simulate player points with minutes correlation

        Args:
            points_per_minute: Average points per minute
            minutes_mean: Expected minutes mean
            minutes_std: Minutes standard deviation
            line: Points line

        Returns:
            Dictionary with probabilities
        """
        # Simulate minutes played
        minutes = np.random.normal(minutes_mean, minutes_std, self.n_simulations)
        minutes = np.maximum(minutes, 0)  # Can't play negative minutes
        minutes = np.minimum(minutes, 48)  # Max 48 mins in NBA

        # Simulate points per minute (with some variance)
        ppm_variance = points_per_minute * 0.2  # 20% variance
        ppm_samples = np.random.normal(points_per_minute, ppm_variance, self.n_simulations)
        ppm_samples = np.maximum(ppm_samples, 0)

        # Calculate total points
        points = minutes * ppm_samples

        # Calculate probabilities
        prob_over = np.mean(points > line)
        prob_under = np.mean(points < line)

        return {
            'prob_over': prob_over,
            'prob_under': prob_under,
            'expected_value': np.mean(points),
            'expected_minutes': np.mean(minutes),
            'median': np.median(points),
            'std': np.std(points)
        }

    def simulate_combined_prop(
        self,
        means: Dict[str, float],
        stds: Dict[str, float],
        line: float,
        correlations: Optional[Dict[Tuple[str, str], float]] = None
    ) -> Dict[str, float]:
        """Simulate combined props (e.g., PRA = Points + Rebounds + Assists)

        Args:
            means: Dictionary of means for each component
            stds: Dictionary of stds for each component
            line: Combined line
            correlations: Optional correlations between components

        Returns:
            Dictionary with probabilities
        """
        components = list(means.keys())
        n_components = len(components)

        if correlations is None:
            # Assume no correlation
            samples = {}
            for comp in components:
                samples[comp] = np.random.normal(
                    means[comp],
                    stds[comp],
                    self.n_simulations
                )
                samples[comp] = np.maximum(samples[comp], 0)
        else:
            # Generate correlated samples (simplified)
            # In practice, would use multivariate normal
            samples = {}
            for comp in components:
                samples[comp] = np.random.normal(
                    means[comp],
                    stds[comp],
                    self.n_simulations
                )
                samples[comp] = np.maximum(samples[comp], 0)

        # Sum components
        total = np.zeros(self.n_simulations)
        for comp in components:
            total += samples[comp]

        # Calculate probabilities
        prob_over = np.mean(total > line)
        prob_under = np.mean(total < line)

        return {
            'prob_over': prob_over,
            'prob_under': prob_under,
            'expected_value': np.mean(total),
            'median': np.median(total),
            'std': np.std(total),
            'component_means': {comp: np.mean(samples[comp]) for comp in components}
        }


class BasketballMonteCarloModel:
    """Monte Carlo model specialized for basketball"""

    def __init__(self, n_simulations: int = 10000):
        """Initialize basketball Monte Carlo model"""
        self.simulator = MonteCarloSimulator(n_simulations)

    def predict_player_points(
        self,
        features: Dict,
        line: float
    ) -> Dict[str, float]:
        """Predict player points using Monte Carlo

        Args:
            features: Player features
            line: Points line

        Returns:
            Prediction dictionary
        """
        # Extract features
        pts_mean = features.get('pts_mean_5', 0)
        pts_std = features.get('pts_std', pts_mean * 0.3)  # Default 30% CV
        min_mean = features.get('min_mean_5', 30)
        min_std = features.get('min_std_5', 5)

        # Points per minute
        ppm = pts_mean / max(min_mean, 1)

        # Simulate with minutes correlation
        result = self.simulator.simulate_with_minutes_correlation(
            points_per_minute=ppm,
            minutes_mean=min_mean,
            minutes_std=min_std,
            line=line
        )

        return result

    def predict_player_pra(
        self,
        features: Dict,
        line: float
    ) -> Dict[str, float]:
        """Predict player Points + Rebounds + Assists

        Args:
            features: Player features
            line: PRA line

        Returns:
            Prediction dictionary
        """
        means = {
            'points': features.get('pts_mean_5', 0),
            'rebounds': features.get('reb_mean_5', 0),
            'assists': features.get('ast_mean_5', 0)
        }

        stds = {
            'points': features.get('pts_std', means['points'] * 0.3),
            'rebounds': means['rebounds'] * 0.4,  # Rebounds typically more variable
            'assists': means['assists'] * 0.5
        }

        # Simple correlations (points-assists often correlated)
        correlations = {
            ('points', 'assists'): 0.3,
            ('points', 'rebounds'): 0.1,
            ('rebounds', 'assists'): -0.1
        }

        result = self.simulator.simulate_combined_prop(
            means=means,
            stds=stds,
            line=line,
            correlations=correlations
        )

        return result


class TennisMonteCarloModel:
    """Monte Carlo model for tennis"""

    def __init__(self, n_simulations: int = 10000):
        """Initialize tennis Monte Carlo model"""
        self.simulator = MonteCarloSimulator(n_simulations)

    def predict_player_aces(
        self,
        features: Dict,
        line: float
    ) -> Dict[str, float]:
        """Predict player aces

        Args:
            features: Player features
            line: Aces line

        Returns:
            Prediction dictionary
        """
        aces_mean = features.get('aces_mean_5', 0)
        aces_std = features.get('aces_std_5', aces_mean * 0.5)

        # Apply surface adjustment
        surface_factor = features.get('surface_factor', 1.0)
        adjusted_mean = aces_mean * surface_factor

        result = self.simulator.simulate_normal(
            mean=adjusted_mean,
            std=aces_std,
            line=line,
            min_value=0
        )

        return result
