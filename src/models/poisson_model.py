"""Poisson-based models for count data (points, rebounds, corners, aces, etc.)"""

import numpy as np
from scipy import stats
from typing import Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class PoissonModel:
    """Poisson model for count-based props"""

    def __init__(self, alpha: float = 0.05):
        """Initialize Poisson model

        Args:
            alpha: Regularization parameter
        """
        self.alpha = alpha
        self.lambda_estimate = None

    def fit(self, data: np.ndarray) -> float:
        """Fit Poisson model to data

        Args:
            data: Array of count data

        Returns:
            Lambda estimate
        """
        if len(data) == 0:
            logger.warning("No data provided for Poisson fit")
            return 0.0

        # Simple MLE estimate with regularization
        self.lambda_estimate = np.mean(data) + self.alpha

        logger.info(f"Fitted Poisson with lambda = {self.lambda_estimate:.2f}")
        return self.lambda_estimate

    def predict_prob_over(self, line: float, lambda_param: Optional[float] = None) -> float:
        """Predict probability of going over the line

        Args:
            line: Over/under line
            lambda_param: Lambda parameter (uses fitted if None)

        Returns:
            Probability of over
        """
        if lambda_param is None:
            lambda_param = self.lambda_estimate

        if lambda_param is None or lambda_param <= 0:
            return 0.5

        # P(X > line) = 1 - P(X <= line)
        prob_over = 1 - stats.poisson.cdf(line, lambda_param)

        return prob_over

    def predict_prob_under(self, line: float, lambda_param: Optional[float] = None) -> float:
        """Predict probability of going under the line

        Args:
            line: Over/under line
            lambda_param: Lambda parameter (uses fitted if None)

        Returns:
            Probability of under
        """
        return 1 - self.predict_prob_over(line, lambda_param)

    def predict_distribution(
        self,
        max_value: int = 50,
        lambda_param: Optional[float] = None
    ) -> Dict[int, float]:
        """Get full probability distribution

        Args:
            max_value: Maximum value to compute
            lambda_param: Lambda parameter

        Returns:
            Dictionary mapping value -> probability
        """
        if lambda_param is None:
            lambda_param = self.lambda_estimate

        if lambda_param is None or lambda_param <= 0:
            return {}

        distribution = {}
        for k in range(max_value + 1):
            distribution[k] = stats.poisson.pmf(k, lambda_param)

        return distribution

    def confidence_interval(
        self,
        confidence: float = 0.95,
        lambda_param: Optional[float] = None
    ) -> Tuple[float, float]:
        """Get confidence interval for the prediction

        Args:
            confidence: Confidence level (0-1)
            lambda_param: Lambda parameter

        Returns:
            Tuple of (lower_bound, upper_bound)
        """
        if lambda_param is None:
            lambda_param = self.lambda_estimate

        if lambda_param is None or lambda_param <= 0:
            return (0, 0)

        alpha = 1 - confidence
        lower = stats.poisson.ppf(alpha / 2, lambda_param)
        upper = stats.poisson.ppf(1 - alpha / 2, lambda_param)

        return (lower, upper)


class NegativeBinomialModel:
    """Negative Binomial model for overdispersed count data"""

    def __init__(self):
        """Initialize Negative Binomial model"""
        self.n = None  # dispersion parameter
        self.p = None  # success probability

    def fit(self, data: np.ndarray) -> Tuple[float, float]:
        """Fit Negative Binomial model to data

        Args:
            data: Array of count data

        Returns:
            Tuple of (n, p) parameters
        """
        if len(data) == 0:
            return (0, 0)

        mean = np.mean(data)
        var = np.var(data)

        # Method of moments estimation
        if var > mean:
            # Overdispersed
            self.p = mean / var
            self.n = mean * self.p / (1 - self.p)
        else:
            # Falls back to Poisson-like
            self.p = 0.5
            self.n = 2 * mean

        logger.info(f"Fitted NegBin with n={self.n:.2f}, p={self.p:.2f}")
        return (self.n, self.p)

    def predict_prob_over(self, line: float) -> float:
        """Predict probability of going over the line

        Args:
            line: Over/under line

        Returns:
            Probability of over
        """
        if self.n is None or self.p is None:
            return 0.5

        # P(X > line) = 1 - P(X <= line)
        prob_over = 1 - stats.nbinom.cdf(line, self.n, self.p)

        return prob_over

    def predict_prob_under(self, line: float) -> float:
        """Predict probability of going under the line"""
        return 1 - self.predict_prob_over(line)


class AdjustedPoissonModel(PoissonModel):
    """Poisson model with contextual adjustments"""

    def __init__(self, alpha: float = 0.05):
        """Initialize adjusted Poisson model"""
        super().__init__(alpha)
        self.adjustments = {}

    def add_adjustment(self, name: str, factor: float):
        """Add a contextual adjustment factor

        Args:
            name: Adjustment name (e.g., 'opponent', 'home_away')
            factor: Multiplicative factor
        """
        self.adjustments[name] = factor

    def get_adjusted_lambda(self, base_lambda: float) -> float:
        """Get lambda adjusted by all factors

        Args:
            base_lambda: Base lambda estimate

        Returns:
            Adjusted lambda
        """
        adjusted = base_lambda

        for name, factor in self.adjustments.items():
            adjusted *= factor
            logger.debug(f"Applied {name} adjustment: {factor:.2f}")

        return adjusted

    def predict_prob_over(self, line: float, lambda_param: Optional[float] = None) -> float:
        """Predict probability with adjustments"""
        if lambda_param is None:
            lambda_param = self.lambda_estimate

        # Apply adjustments
        adjusted_lambda = self.get_adjusted_lambda(lambda_param)

        return super().predict_prob_over(line, adjusted_lambda)


class BasketballPoissonModel:
    """Specialized Poisson model for basketball props"""

    def __init__(self):
        """Initialize basketball model"""
        self.base_model = PoissonModel()

    def predict_player_points(
        self,
        features: Dict,
        line: float
    ) -> Dict[str, float]:
        """Predict player points probability

        Args:
            features: Player feature dictionary
            line: Over/under line

        Returns:
            Dictionary with probabilities and stats
        """
        # Use recent average with adjustments
        base_avg = features.get('pts_mean_5', 0)

        # Adjust for trend
        trend = features.get('pts_trend_5', 0)
        trend_adj = 1 + (trend * 0.1)  # Dampen trend effect

        # Adjust for minutes
        expected_min = features.get('min_mean_5', 30)
        min_factor = expected_min / 30  # Normalize to 30 mins

        # Opponent defense
        opp_def = features.get('opp_def_rating', 100)
        def_factor = 100 / opp_def

        # Pace
        pace = features.get('opp_pace', 100)
        pace_factor = pace / 100

        # Calculate adjusted lambda
        adjusted_avg = base_avg * trend_adj * min_factor * def_factor * pace_factor

        # Fit Poisson
        self.base_model.lambda_estimate = adjusted_avg

        # Get probabilities
        prob_over = self.base_model.predict_prob_over(line)
        prob_under = self.base_model.predict_prob_under(line)

        # Confidence interval
        ci = self.base_model.confidence_interval(0.90)

        return {
            'expected_value': adjusted_avg,
            'prob_over': prob_over,
            'prob_under': prob_under,
            'confidence_interval_90': ci,
            'base_avg': base_avg,
            'adjustments': {
                'trend': trend_adj,
                'minutes': min_factor,
                'defense': def_factor,
                'pace': pace_factor
            }
        }


class SoccerPoissonModel:
    """Specialized Poisson model for soccer props"""

    def __init__(self):
        """Initialize soccer model"""
        self.base_model = PoissonModel()

    def predict_team_corners(
        self,
        features: Dict,
        line: float
    ) -> Dict[str, float]:
        """Predict team corners probability

        Args:
            features: Team feature dictionary
            line: Over/under line

        Returns:
            Dictionary with probabilities
        """
        # Use recent average
        base_avg = features.get('corners_mean_5', 0)

        # Home/away adjustment
        if features.get('home_away') == 'home':
            home_factor = 1.1  # Home teams typically get more corners
        else:
            home_factor = 0.9

        # Opponent factor
        opp_conceded = features.get('opp_corners_conceded_mean', base_avg)
        if opp_conceded > 0:
            opp_factor = opp_conceded / max(base_avg, 1)
        else:
            opp_factor = 1.0

        # Adjusted lambda
        adjusted_avg = base_avg * home_factor * opp_factor

        self.base_model.lambda_estimate = adjusted_avg

        prob_over = self.base_model.predict_prob_over(line)
        prob_under = self.base_model.predict_prob_under(line)

        return {
            'expected_value': adjusted_avg,
            'prob_over': prob_over,
            'prob_under': prob_under,
            'base_avg': base_avg,
            'adjustments': {
                'home_away': home_factor,
                'opponent': opp_factor
            }
        }
