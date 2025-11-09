"""Model calibration and training module"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from scipy.optimize import minimize
from sklearn.metrics import log_loss, brier_score_loss
import logging

logger = logging.getLogger(__name__)


class PoissonCalibrator:
    """Calibrate Poisson model factors using historical data"""

    def __init__(self):
        """Initialize calibrator"""
        self.factors = {
            'opponent_defense': 1.0,
            'home_away_home': 1.05,
            'home_away_away': 0.95,
            'pace': 1.0,
            'minutes': 1.0,
            'trend': 0.1  # Dampening factor for trend
        }

    def calibrate_from_historical(
        self,
        historical_data: pd.DataFrame
    ) -> Dict[str, float]:
        """Calibrate factors from historical data

        Args:
            historical_data: DataFrame with columns:
                - actual_value: Actual outcome
                - predicted_lambda: Model's lambda prediction
                - opponent_def_rating: Opponent defense rating
                - home_away: 'home' or 'away'
                - pace: Team pace
                - minutes: Minutes played

        Returns:
            Calibrated factors dictionary
        """
        logger.info("Calibrating Poisson model factors...")

        # Calibrate home/away factor
        home_games = historical_data[historical_data['home_away'] == 'home']
        away_games = historical_data[historical_data['home_away'] == 'away']

        if len(home_games) > 0 and len(away_games) > 0:
            home_mean = home_games['actual_value'].mean()
            away_mean = away_games['actual_value'].mean()
            overall_mean = historical_data['actual_value'].mean()

            self.factors['home_away_home'] = home_mean / overall_mean
            self.factors['home_away_away'] = away_mean / overall_mean

            logger.info(f"Home factor: {self.factors['home_away_home']:.3f}")
            logger.info(f"Away factor: {self.factors['home_away_away']:.3f}")

        # Calibrate opponent defense factor using regression
        if 'opponent_def_rating' in historical_data.columns:
            # Simple linear relationship
            correlation = historical_data[['actual_value', 'opponent_def_rating']].corr().iloc[0, 1]
            logger.info(f"Opponent defense correlation: {correlation:.3f}")

        return self.factors

    def validate_probabilities(
        self,
        predictions: pd.DataFrame,
        actual_results: pd.Series
    ) -> Dict[str, float]:
        """Validate predicted probabilities against actual outcomes

        Args:
            predictions: DataFrame with 'prob_over' column
            actual_results: Binary series (1 = over, 0 = under)

        Returns:
            Validation metrics
        """
        if len(predictions) != len(actual_results):
            raise ValueError("Predictions and results must have same length")

        prob_over = predictions['prob_over'].values
        actual = actual_results.values

        # Brier Score (lower is better, 0 = perfect)
        brier = brier_score_loss(actual, prob_over)

        # Log Loss (lower is better)
        logloss = log_loss(actual, prob_over)

        # Calibration: group by predicted probability bins
        bins = np.linspace(0, 1, 11)  # 10 bins
        bin_indices = np.digitize(prob_over, bins)

        calibration_data = []
        for i in range(1, len(bins)):
            mask = bin_indices == i
            if mask.sum() > 0:
                predicted_prob = prob_over[mask].mean()
                actual_freq = actual[mask].mean()
                calibration_data.append({
                    'bin': i,
                    'predicted': predicted_prob,
                    'actual': actual_freq,
                    'count': mask.sum()
                })

        calibration_df = pd.DataFrame(calibration_data)

        # Mean absolute calibration error
        if len(calibration_df) > 0:
            calibration_error = np.abs(
                calibration_df['predicted'] - calibration_df['actual']
            ).mean()
        else:
            calibration_error = np.nan

        metrics = {
            'brier_score': brier,
            'log_loss': logloss,
            'calibration_error': calibration_error,
            'n_samples': len(predictions)
        }

        logger.info(f"Validation metrics: Brier={brier:.4f}, LogLoss={logloss:.4f}, CalibError={calibration_error:.4f}")

        return metrics


class OptimalFactorFinder:
    """Find optimal adjustment factors using optimization"""

    def __init__(self, historical_data: pd.DataFrame):
        """Initialize optimizer

        Args:
            historical_data: Historical outcomes with features
        """
        self.data = historical_data

    def objective_function(self, factors: np.ndarray) -> float:
        """Objective function to minimize

        Args:
            factors: Array of factor values to test

        Returns:
            Loss value (mean squared error)
        """
        opponent_factor, home_factor, pace_factor = factors

        predictions = []
        actuals = []

        for idx, row in self.data.iterrows():
            base_lambda = row['base_prediction']

            # Apply factors
            adjusted = base_lambda
            adjusted *= (100 / row['opponent_def_rating']) * opponent_factor
            adjusted *= home_factor if row['home_away'] == 'home' else 1.0
            adjusted *= (row['pace'] / 100) * pace_factor

            predictions.append(adjusted)
            actuals.append(row['actual_value'])

        # Mean squared error
        mse = np.mean((np.array(predictions) - np.array(actuals)) ** 2)

        return mse

    def optimize(self) -> Dict[str, float]:
        """Find optimal factors

        Returns:
            Dictionary of optimal factors
        """
        logger.info("Optimizing adjustment factors...")

        # Initial guess
        x0 = np.array([1.0, 1.05, 1.0])  # opponent, home, pace

        # Bounds
        bounds = [
            (0.5, 1.5),  # opponent factor
            (0.9, 1.2),  # home factor
            (0.8, 1.2)   # pace factor
        ]

        # Optimize
        result = minimize(
            self.objective_function,
            x0,
            method='L-BFGS-B',
            bounds=bounds
        )

        optimal_factors = {
            'opponent_defense': result.x[0],
            'home_away': result.x[1],
            'pace': result.x[2]
        }

        logger.info(f"Optimal factors found: {optimal_factors}")
        logger.info(f"Final MSE: {result.fun:.4f}")

        return optimal_factors


class ModelValidator:
    """Validate model performance on hold-out data"""

    @staticmethod
    def calculate_actual_vs_predicted(
        predictions: pd.DataFrame,
        actuals: pd.DataFrame
    ) -> Dict:
        """Calculate actual vs predicted metrics

        Args:
            predictions: Predicted values
            actuals: Actual values

        Returns:
            Metrics dictionary
        """
        pred_values = predictions['expected_value'].values
        actual_values = actuals['actual_value'].values

        # Mean Absolute Error
        mae = np.mean(np.abs(pred_values - actual_values))

        # Root Mean Squared Error
        rmse = np.sqrt(np.mean((pred_values - actual_values) ** 2))

        # R-squared
        ss_res = np.sum((actual_values - pred_values) ** 2)
        ss_tot = np.sum((actual_values - np.mean(actual_values)) ** 2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

        # Mean Absolute Percentage Error
        mape = np.mean(np.abs((actual_values - pred_values) / actual_values)) * 100

        return {
            'mae': mae,
            'rmse': rmse,
            'r2': r2,
            'mape': mape
        }

    @staticmethod
    def probability_calibration_plot_data(
        predicted_probs: np.ndarray,
        actual_outcomes: np.ndarray,
        n_bins: int = 10
    ) -> pd.DataFrame:
        """Generate data for calibration plot

        Args:
            predicted_probs: Predicted probabilities
            actual_outcomes: Binary actual outcomes (0/1)
            n_bins: Number of bins

        Returns:
            DataFrame with calibration data
        """
        bins = np.linspace(0, 1, n_bins + 1)
        bin_indices = np.digitize(predicted_probs, bins) - 1

        calibration_data = []
        for i in range(n_bins):
            mask = bin_indices == i
            if mask.sum() > 0:
                bin_mean_pred = predicted_probs[mask].mean()
                bin_mean_actual = actual_outcomes[mask].mean()
                calibration_data.append({
                    'predicted_prob': bin_mean_pred,
                    'actual_freq': bin_mean_actual,
                    'count': mask.sum()
                })

        return pd.DataFrame(calibration_data)
