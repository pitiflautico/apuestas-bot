"""Script to calibrate models using historical data"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from utils import load_config, setup_logging
from models.calibration import PoissonCalibrator, OptimalFactorFinder, ModelValidator
from database import get_session, PlayerStats, Result
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


def generate_mock_historical_data(n_samples: int = 1000) -> pd.DataFrame:
    """Generate mock historical data for demonstration

    In production, this would query actual historical data from database

    Args:
        n_samples: Number of samples to generate

    Returns:
        DataFrame with historical data
    """
    np.random.seed(42)

    data = {
        'player_name': ['LeBron James'] * n_samples,
        'actual_value': np.random.poisson(27, n_samples),  # Actual points scored
        'base_prediction': np.random.normal(26.5, 2, n_samples),  # Model's base prediction
        'predicted_lambda': np.random.normal(26.5, 2, n_samples),
        'opponent_def_rating': np.random.normal(110, 10, n_samples),
        'home_away': np.random.choice(['home', 'away'], n_samples),
        'pace': np.random.normal(100, 5, n_samples),
        'minutes': np.random.normal(35, 3, n_samples),
        'line': [25.5] * n_samples
    }

    df = pd.DataFrame(data)

    # Add binary outcome (over/under)
    df['outcome_over'] = (df['actual_value'] > df['line']).astype(int)

    # Add predicted probability (from Poisson model)
    from scipy.stats import poisson
    df['prob_over'] = df['predicted_lambda'].apply(
        lambda lam: 1 - poisson.cdf(25.5, lam)
    )

    return df


def calibrate_poisson_factors():
    """Calibrate Poisson model adjustment factors"""
    logger.info("=" * 60)
    logger.info("CALIBRATING POISSON MODEL FACTORS")
    logger.info("=" * 60)

    # Load historical data
    logger.info("Loading historical data...")
    historical_data = generate_mock_historical_data(n_samples=500)

    logger.info(f"Loaded {len(historical_data)} historical samples")
    logger.info(f"Average actual value: {historical_data['actual_value'].mean():.2f}")

    # Initialize calibrator
    calibrator = PoissonCalibrator()

    # Calibrate factors
    factors = calibrator.calibrate_from_historical(historical_data)

    logger.info("\nCalibrated Factors:")
    for factor_name, factor_value in factors.items():
        logger.info(f"  {factor_name}: {factor_value:.3f}")

    # Validate probabilities
    logger.info("\nValidating predicted probabilities...")

    predictions = historical_data[['prob_over']]
    actual_outcomes = historical_data['outcome_over']

    metrics = calibrator.validate_probabilities(predictions, actual_outcomes)

    logger.info("\nValidation Metrics:")
    logger.info(f"  Brier Score: {metrics['brier_score']:.4f} (lower is better, 0 = perfect)")
    logger.info(f"  Log Loss: {metrics['log_loss']:.4f} (lower is better)")
    logger.info(f"  Calibration Error: {metrics['calibration_error']:.4f} (lower is better)")
    logger.info(f"  Samples: {metrics['n_samples']}")

    return factors, metrics


def optimize_adjustment_factors():
    """Find optimal adjustment factors using optimization"""
    logger.info("\n" + "=" * 60)
    logger.info("OPTIMIZING ADJUSTMENT FACTORS")
    logger.info("=" * 60)

    # Load data
    historical_data = generate_mock_historical_data(n_samples=500)

    # Initialize optimizer
    optimizer = OptimalFactorFinder(historical_data)

    # Find optimal factors
    optimal_factors = optimizer.optimize()

    logger.info("\nOptimal Factors:")
    for factor_name, factor_value in optimal_factors.items():
        logger.info(f"  {factor_name}: {factor_value:.3f}")

    return optimal_factors


def validate_model_accuracy():
    """Validate model accuracy on hold-out set"""
    logger.info("\n" + "=" * 60)
    logger.info("VALIDATING MODEL ACCURACY")
    logger.info("=" * 60)

    # Generate train and test data
    train_data = generate_mock_historical_data(n_samples=400)
    test_data = generate_mock_historical_data(n_samples=100)

    # Prepare predictions and actuals
    predictions = pd.DataFrame({
        'expected_value': test_data['predicted_lambda']
    })

    actuals = pd.DataFrame({
        'actual_value': test_data['actual_value']
    })

    # Calculate metrics
    validator = ModelValidator()
    metrics = validator.calculate_actual_vs_predicted(predictions, actuals)

    logger.info("\nModel Accuracy Metrics:")
    logger.info(f"  MAE (Mean Absolute Error): {metrics['mae']:.2f} points")
    logger.info(f"  RMSE (Root Mean Squared Error): {metrics['rmse']:.2f} points")
    logger.info(f"  R² (R-squared): {metrics['r2']:.3f}")
    logger.info(f"  MAPE (Mean Absolute % Error): {metrics['mape']:.1f}%")

    # Generate calibration plot data
    predicted_probs = test_data['prob_over'].values
    actual_outcomes = test_data['outcome_over'].values

    calibration_data = validator.probability_calibration_plot_data(
        predicted_probs,
        actual_outcomes,
        n_bins=10
    )

    logger.info("\nProbability Calibration:")
    logger.info(calibration_data.to_string())

    return metrics


def main():
    """Main calibration function"""
    config = load_config()
    setup_logging(
        log_level=config['general']['log_level'],
        log_file='logs/calibration.log'
    )

    logger.info("Starting model calibration process...")
    logger.info("Using mock data for demonstration")
    logger.info("In production, this would use actual historical data from database\n")

    # 1. Calibrate Poisson factors
    factors, validation_metrics = calibrate_poisson_factors()

    # 2. Optimize adjustment factors
    optimal_factors = optimize_adjustment_factors()

    # 3. Validate model accuracy
    accuracy_metrics = validate_model_accuracy()

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("CALIBRATION SUMMARY")
    logger.info("=" * 60)

    logger.info("\n✅ Calibration Complete!")
    logger.info(f"\nBrier Score: {validation_metrics['brier_score']:.4f}")
    logger.info(f"Model MAE: {accuracy_metrics['mae']:.2f} points")
    logger.info(f"Model R²: {accuracy_metrics['r2']:.3f}")

    logger.info("\nNext steps:")
    logger.info("1. Update config/config.yaml with calibrated factors")
    logger.info("2. Monitor performance on new predictions")
    logger.info("3. Re-calibrate monthly as needed")

    # Save factors to file
    import yaml

    factors_to_save = {
        'calibrated_factors': factors,
        'optimal_factors': optimal_factors,
        'validation_metrics': {
            'brier_score': float(validation_metrics['brier_score']),
            'log_loss': float(validation_metrics['log_loss']),
            'calibration_error': float(validation_metrics['calibration_error'])
        },
        'accuracy_metrics': {
            'mae': float(accuracy_metrics['mae']),
            'rmse': float(accuracy_metrics['rmse']),
            'r2': float(accuracy_metrics['r2'])
        }
    }

    output_path = Path(__file__).parent.parent / 'config' / 'calibrated_factors.yaml'
    with open(output_path, 'w') as f:
        yaml.dump(factors_to_save, f, default_flow_style=False)

    logger.info(f"\n📁 Saved calibrated factors to: {output_path}")


if __name__ == "__main__":
    main()
