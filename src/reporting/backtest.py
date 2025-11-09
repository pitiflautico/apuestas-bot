"""Backtesting framework for sports props"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class Backtest:
    """Backtesting engine for sports props"""

    def __init__(self, config: Dict, db_session: Session):
        """Initialize backtesting engine

        Args:
            config: Configuration dictionary
            db_session: Database session
        """
        self.config = config
        self.db_session = db_session
        self.results = []

    def run_backtest(
        self,
        start_date: datetime,
        end_date: datetime,
        min_ev: float = 0.03,
        min_odds: float = 1.50,
        max_odds: float = 5.00
    ) -> Dict:
        """Run backtest for a date range

        Args:
            start_date: Start date
            end_date: End date
            min_ev: Minimum EV threshold
            min_odds: Minimum odds
            max_odds: Maximum odds

        Returns:
            Backtest results dictionary
        """
        logger.info(f"Running backtest from {start_date} to {end_date}")

        # Query picks in date range
        # This would query the Pick table
        # For now, placeholder

        picks = []  # Would query from database

        results = self.analyze_picks(picks)

        return results

    def analyze_picks(self, picks: List[Dict]) -> Dict:
        """Analyze a set of picks

        Args:
            picks: List of pick dictionaries

        Returns:
            Analysis results
        """
        if not picks:
            return {
                'total_picks': 0,
                'total_staked': 0,
                'total_profit': 0,
                'roi': 0,
                'win_rate': 0
            }

        df = pd.DataFrame(picks)

        # Calculate metrics
        total_picks = len(df)
        total_staked = df['stake'].sum() if 'stake' in df else 0
        total_profit = df['profit_loss'].sum() if 'profit_loss' in df else 0

        roi = (total_profit / total_staked * 100) if total_staked > 0 else 0

        wins = df[df['result'] == 'won'] if 'result' in df else pd.DataFrame()
        win_rate = (len(wins) / total_picks * 100) if total_picks > 0 else 0

        # Average CLV
        avg_clv = df['clv'].mean() if 'clv' in df else 0

        # Sharpe ratio
        if 'profit_loss' in df and len(df) > 1:
            returns = df['profit_loss'] / df['stake']
            sharpe = (returns.mean() / returns.std()) * np.sqrt(252) if returns.std() > 0 else 0
        else:
            sharpe = 0

        # Max drawdown
        if 'profit_loss' in df:
            cumulative = df['profit_loss'].cumsum()
            running_max = cumulative.cummax()
            drawdown = running_max - cumulative
            max_dd = drawdown.max()
        else:
            max_dd = 0

        results = {
            'total_picks': total_picks,
            'total_staked': total_staked,
            'total_profit': total_profit,
            'roi': roi,
            'win_rate': win_rate,
            'avg_clv': avg_clv,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_dd,
            'profit_factor': self._calculate_profit_factor(df)
        }

        return results

    def _calculate_profit_factor(self, df: pd.DataFrame) -> float:
        """Calculate profit factor

        Args:
            df: Picks DataFrame

        Returns:
            Profit factor
        """
        if 'profit_loss' not in df or len(df) == 0:
            return 0

        wins = df[df['profit_loss'] > 0]['profit_loss'].sum()
        losses = abs(df[df['profit_loss'] < 0]['profit_loss'].sum())

        if losses == 0:
            return float('inf') if wins > 0 else 0

        return wins / losses

    def analyze_by_market(self, picks: List[Dict]) -> Dict[str, Dict]:
        """Analyze picks by market type

        Args:
            picks: List of picks

        Returns:
            Dictionary mapping market -> analysis
        """
        if not picks:
            return {}

        df = pd.DataFrame(picks)

        if 'market_type' not in df:
            return {}

        results = {}
        for market in df['market_type'].unique():
            market_picks = df[df['market_type'] == market].to_dict('records')
            results[market] = self.analyze_picks(market_picks)

        return results

    def analyze_by_ev_range(
        self,
        picks: List[Dict],
        ranges: List[Tuple[float, float]] = [
            (0.03, 0.05),
            (0.05, 0.08),
            (0.08, 0.12),
            (0.12, float('inf'))
        ]
    ) -> Dict[str, Dict]:
        """Analyze picks by EV range

        Args:
            picks: List of picks
            ranges: List of (min, max) EV ranges

        Returns:
            Dictionary mapping range -> analysis
        """
        if not picks:
            return {}

        df = pd.DataFrame(picks)

        if 'expected_value' not in df:
            return {}

        results = {}
        for min_ev, max_ev in ranges:
            range_key = f"{min_ev:.2%} - {max_ev:.2%}"
            range_picks = df[
                (df['expected_value'] >= min_ev) &
                (df['expected_value'] < max_ev)
            ].to_dict('records')

            results[range_key] = self.analyze_picks(range_picks)

        return results

    def walk_forward_validation(
        self,
        start_date: datetime,
        end_date: datetime,
        train_days: int = 90,
        test_days: int = 30
    ) -> List[Dict]:
        """Run walk-forward validation

        Args:
            start_date: Start date
            end_date: End date
            train_days: Training period days
            test_days: Testing period days

        Returns:
            List of validation results
        """
        results = []
        current_date = start_date

        while current_date < end_date:
            train_start = current_date
            train_end = current_date + timedelta(days=train_days)
            test_start = train_end
            test_end = test_start + timedelta(days=test_days)

            if test_end > end_date:
                break

            logger.info(f"Walk-forward: train {train_start} to {train_end}, test {test_start} to {test_end}")

            # Train model on training period
            # Test on testing period
            # For now, placeholder

            period_result = {
                'train_start': train_start,
                'train_end': train_end,
                'test_start': test_start,
                'test_end': test_end,
                'test_roi': 0,  # Placeholder
                'test_picks': 0
            }

            results.append(period_result)

            # Move to next period
            current_date = test_end

        return results


class PerformanceAnalyzer:
    """Analyze performance metrics"""

    @staticmethod
    def calculate_roi(profit: float, staked: float) -> float:
        """Calculate ROI percentage"""
        return (profit / staked * 100) if staked > 0 else 0

    @staticmethod
    def calculate_sharpe_ratio(returns: pd.Series, periods_per_year: int = 252) -> float:
        """Calculate Sharpe ratio"""
        if len(returns) < 2 or returns.std() == 0:
            return 0

        return (returns.mean() / returns.std()) * np.sqrt(periods_per_year)

    @staticmethod
    def calculate_max_drawdown(cumulative_returns: pd.Series) -> float:
        """Calculate maximum drawdown"""
        running_max = cumulative_returns.cummax()
        drawdown = running_max - cumulative_returns
        return drawdown.max()

    @staticmethod
    def calculate_win_rate(wins: int, total: int) -> float:
        """Calculate win rate percentage"""
        return (wins / total * 100) if total > 0 else 0

    @staticmethod
    def calculate_avg_odds(odds_list: List[float]) -> float:
        """Calculate average odds"""
        return sum(odds_list) / len(odds_list) if odds_list else 0

    @staticmethod
    def calculate_yield(profit: float, staked: float) -> float:
        """Calculate yield (same as ROI but different terminology)"""
        return (profit / staked * 100) if staked > 0 else 0
