"""Pick selector - ranks and selects best picks"""

from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class PickSelector:
    """Select and rank picks based on EV, confidence, and constraints"""

    def __init__(self, config: Dict):
        """Initialize pick selector

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.min_ev = config.get('pricing', {}).get('min_ev_threshold', 0.03)
        self.min_odds = config.get('pricing', {}).get('min_odds', 1.50)
        self.max_odds = config.get('pricing', {}).get('max_odds', 5.00)
        self.max_correlated = config.get('bankroll', {}).get('max_correlated_picks', 3)

    def filter_picks(self, picks: List[Dict]) -> List[Dict]:
        """Filter picks based on criteria

        Args:
            picks: List of pick dictionaries

        Returns:
            Filtered picks
        """
        filtered = []

        for pick in picks:
            # EV threshold
            if pick.get('expected_value', 0) < self.min_ev:
                continue

            # Odds range
            odds = pick.get('odds', 0)
            if odds < self.min_odds or odds > self.max_odds:
                continue

            # Add to filtered
            filtered.append(pick)

        logger.info(f"Filtered {len(filtered)} picks from {len(picks)} total")
        return filtered

    def rank_picks(self, picks: List[Dict]) -> List[Dict]:
        """Rank picks by expected value and confidence

        Args:
            picks: List of pick dictionaries

        Returns:
            Ranked picks (sorted)
        """
        # Sort by EV descending, then by confidence
        ranked = sorted(
            picks,
            key=lambda x: (x.get('expected_value', 0), x.get('confidence', 0)),
            reverse=True
        )

        logger.info(f"Ranked {len(ranked)} picks")
        return ranked

    def select_daily_picks(
        self,
        picks: List[Dict],
        max_picks: int = 10,
        max_exposure: float = 500
    ) -> List[Dict]:
        """Select today's picks respecting constraints

        Args:
            picks: List of all available picks
            max_picks: Maximum number of picks
            max_exposure: Maximum total exposure

        Returns:
            Selected picks for the day
        """
        # Filter and rank
        filtered = self.filter_picks(picks)
        ranked = self.rank_picks(filtered)

        # Select top picks within constraints
        selected = []
        total_exposure = 0

        for pick in ranked:
            if len(selected) >= max_picks:
                break

            stake = pick.get('recommended_stake', 0)
            if total_exposure + stake > max_exposure:
                continue

            # Check correlation (avoid too many picks from same game)
            if self._check_correlation_limit(selected, pick):
                continue

            selected.append(pick)
            total_exposure += stake

        logger.info(f"Selected {len(selected)} picks with total exposure €{total_exposure:.2f}")
        return selected

    def _check_correlation_limit(self, selected: List[Dict], new_pick: Dict) -> bool:
        """Check if adding new pick would exceed correlation limit

        Args:
            selected: Already selected picks
            new_pick: New pick to check

        Returns:
            True if limit would be exceeded
        """
        match_id = new_pick.get('match_id')

        # Count picks from same match
        same_match_count = sum(1 for p in selected if p.get('match_id') == match_id)

        return same_match_count >= self.max_correlated
