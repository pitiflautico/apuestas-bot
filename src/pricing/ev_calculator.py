"""Expected Value (EV) and Edge calculation"""

import logging
from typing import Dict, List, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)


class EVCalculator:
    """Calculator for Expected Value and betting edge"""

    def __init__(self, config: Dict):
        """Initialize EV calculator

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.min_ev_threshold = config.get('pricing', {}).get('min_ev_threshold', 0.03)
        self.max_vig = config.get('pricing', {}).get('max_vig', 0.10)

    def calculate_implied_probability(
        self,
        odds: float,
        odds_format: str = 'decimal'
    ) -> float:
        """Calculate implied probability from odds

        Args:
            odds: Odds value
            odds_format: Format (decimal, american, fractional)

        Returns:
            Implied probability (0-1)
        """
        if odds_format == 'decimal':
            return 1 / odds
        elif odds_format == 'american':
            if odds > 0:
                return 100 / (odds + 100)
            else:
                return abs(odds) / (abs(odds) + 100)
        else:
            raise ValueError(f"Unsupported odds format: {odds_format}")

    def remove_vigorish(
        self,
        over_odds: float,
        under_odds: float
    ) -> Tuple[float, float]:
        """Remove vigorish to get true probabilities

        Args:
            over_odds: Over odds (decimal)
            under_odds: Under odds (decimal)

        Returns:
            Tuple of (true_prob_over, true_prob_under)
        """
        # Implied probabilities
        impl_over = self.calculate_implied_probability(over_odds)
        impl_under = self.calculate_implied_probability(under_odds)

        # Total (should be > 1 due to vig)
        total = impl_over + impl_under

        # Normalize
        if total > 0:
            true_over = impl_over / total
            true_under = impl_under / total
        else:
            true_over = 0.5
            true_under = 0.5

        return (true_over, true_under)

    def calculate_vigorish(
        self,
        over_odds: float,
        under_odds: float
    ) -> float:
        """Calculate bookmaker vigorish (juice)

        Args:
            over_odds: Over odds (decimal)
            under_odds: Under odds (decimal)

        Returns:
            Vigorish percentage
        """
        impl_over = self.calculate_implied_probability(over_odds)
        impl_under = self.calculate_implied_probability(under_odds)

        total = impl_over + impl_under
        vig = total - 1

        return vig

    def calculate_ev(
        self,
        true_probability: float,
        odds: float,
        stake: float = 1.0
    ) -> float:
        """Calculate Expected Value

        Args:
            true_probability: True probability of winning (0-1)
            odds: Decimal odds
            stake: Bet stake

        Returns:
            Expected value
        """
        # Profit if win
        profit = (odds - 1) * stake

        # Loss if lose
        loss = stake

        # EV = P(win) * profit - P(lose) * loss
        ev = true_probability * profit - (1 - true_probability) * loss

        return ev

    def calculate_edge(
        self,
        true_probability: float,
        odds: float
    ) -> float:
        """Calculate betting edge percentage

        Args:
            true_probability: True probability (0-1)
            odds: Decimal odds

        Returns:
            Edge percentage
        """
        implied_prob = self.calculate_implied_probability(odds)
        edge = true_probability - implied_prob

        return edge

    def calculate_edge_percent(
        self,
        true_probability: float,
        odds: float
    ) -> float:
        """Calculate edge as percentage of stake

        Args:
            true_probability: True probability (0-1)
            odds: Decimal odds

        Returns:
            Edge percentage (0-100)
        """
        ev = self.calculate_ev(true_probability, odds, stake=1.0)
        edge_pct = ev * 100

        return edge_pct

    def is_positive_ev(
        self,
        true_probability: float,
        odds: float,
        min_threshold: Optional[float] = None
    ) -> bool:
        """Check if bet has positive EV above threshold

        Args:
            true_probability: True probability (0-1)
            odds: Decimal odds
            min_threshold: Minimum edge threshold (uses config if None)

        Returns:
            True if positive EV above threshold
        """
        if min_threshold is None:
            min_threshold = self.min_ev_threshold

        edge = self.calculate_edge(true_probability, odds)

        return edge >= min_threshold

    def kelly_criterion(
        self,
        true_probability: float,
        odds: float,
        fraction: float = 0.25
    ) -> float:
        """Calculate Kelly Criterion bet size

        Args:
            true_probability: True probability (0-1)
            odds: Decimal odds
            fraction: Kelly fraction (0-1)

        Returns:
            Fraction of bankroll to bet (0-1)
        """
        b = odds - 1  # net odds
        q = 1 - true_probability

        # Kelly formula: (bp - q) / b
        kelly = (b * true_probability - q) / b

        # Apply fraction and ensure non-negative
        kelly_frac = max(0, kelly * fraction)

        # Cap at reasonable maximum (e.g., 10% of bankroll)
        kelly_frac = min(kelly_frac, 0.10)

        return kelly_frac

    def calculate_stake(
        self,
        bankroll: float,
        true_probability: float,
        odds: float,
        strategy: str = 'fractional_kelly',
        kelly_fraction: float = 0.25,
        min_bet: float = 10,
        max_bet: float = 100
    ) -> float:
        """Calculate recommended stake

        Args:
            bankroll: Current bankroll
            true_probability: True probability (0-1)
            odds: Decimal odds
            strategy: Betting strategy (fractional_kelly, flat)
            kelly_fraction: Kelly fraction if using Kelly
            min_bet: Minimum bet size
            max_bet: Maximum bet size

        Returns:
            Recommended stake
        """
        if strategy == 'fractional_kelly':
            kelly_pct = self.kelly_criterion(true_probability, odds, kelly_fraction)
            stake = bankroll * kelly_pct
        elif strategy == 'flat':
            stake = min_bet
        else:
            stake = min_bet

        # Apply min/max constraints
        stake = max(stake, min_bet)
        stake = min(stake, max_bet)

        # Round to nearest unit
        stake = round(stake, 2)

        return stake


class CLVCalculator:
    """Closing Line Value calculator"""

    def __init__(self):
        """Initialize CLV calculator"""
        pass

    def calculate_clv(
        self,
        bet_odds: float,
        closing_odds: float
    ) -> float:
        """Calculate Closing Line Value

        Args:
            bet_odds: Odds when bet was placed
            closing_odds: Closing line odds

        Returns:
            CLV percentage
        """
        # CLV = (closing_odds - bet_odds) / bet_odds
        clv = (closing_odds - bet_odds) / bet_odds

        return clv

    def calculate_clv_hold(
        self,
        bet_odds: float,
        closing_over: float,
        closing_under: float,
        side: str
    ) -> float:
        """Calculate CLV accounting for market hold

        Args:
            bet_odds: Odds when bet was placed
            closing_over: Closing over odds
            closing_under: Closing under odds
            side: 'over' or 'under'

        Returns:
            CLV percentage
        """
        # Get the relevant closing odds
        if side.lower() == 'over':
            closing_odds = closing_over
        else:
            closing_odds = closing_under

        # Calculate basic CLV
        clv = self.calculate_clv(bet_odds, closing_odds)

        return clv
