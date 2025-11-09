"""Script to train ML models (optional advanced models)"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from utils import load_config, setup_logging
from models.ml_models import MLPropModel
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


def generate_training_data(n_samples: int = 2000) -> pd.DataFrame:
    """Generate mock training data

    In production, this would query actual historical player stats

    Args:
        n_samples: Number of samples

    Returns:
        Training DataFrame
    """
    np.random.seed(42)

    data = {
        # Rolling averages
        'pts_mean_5': np.random.normal(25, 5, n_samples),
        'pts_mean_10': np.random.normal(24.5, 4.5, n_samples),
        'pts_mean_20': np.random.normal(24, 4, n_samples),

        'reb_mean_5': np.random.normal(7, 2, n_samples),
        'reb_mean_10': np.random.normal(6.8, 2, n_samples),

        'ast_mean_5': np.random.normal(6, 2, n_samples),
        'ast_mean_10': np.random.normal(5.8, 2, n_samples),

        'min_mean_5': np.random.normal(34, 3, n_samples),
        'min_mean_10': np.random.normal(33.5, 3, n_samples),

        # Variances
        'pts_std_5': np.random.normal(6, 1, n_samples),
        'reb_std_5': np.random.normal(2.5, 0.5, n_samples),
        'ast_std_5': np.random.normal(2, 0.5, n_samples),

        # Trends
        'pts_trend_5': np.random.normal(0, 0.5, n_samples),
        'pts_momentum': np.random.normal(1, 0.1, n_samples),

        # Opponent
        'opp_def_rating': np.random.normal(110, 5, n_samples),
        'opp_pace': np.random.normal(100, 5, n_samples),

        # Context
        'home_away_encoded': np.random.choice([0, 1], n_samples),
        'days_rest': np.random.choice([0, 1, 2, 3], n_samples),
        'back_to_back': np.random.choice([0, 1], n_samples, p=[0.8, 0.2])
    }

    df = pd.DataFrame(data)

    # Generate target (actual points scored)
    # Simple linear combination + noise for demonstration
    df['actual_value'] = (
        df['pts_mean_5'] * 0.6 +
        df['pts_mean_10'] * 0.3 +
        df['min_mean_5'] * 0.2 +
        df['home_away_encoded'] * 1.5 -
        (df['opp_def_rating'] - 110) * 0.1 +
        np.random.normal(0, 3, n_samples)
    )

    return df


def train_xgboost_model():
    """Train XGBoost model for player props"""
    logger.info("=" * 60)
    logger.info("TRAINING XGBOOST MODEL")
    logger.info("=" * 60)

    # Generate data
    logger.info("Generating training data...")
    data = generate_training_data(n_samples=2000)

    # Split into train/val/test
    from sklearn.model_selection import train_test_split

    train_val, test = train_test_split(data, test_size=0.2, random_state=42)
    train, val = train_test_split(train_val, test_size=0.2, random_state=42)

    logger.info(f"Train: {len(train)}, Val: {len(val)}, Test: {len(test)}")

    # Initialize model
    model = MLPropModel(model_type='xgboost')

    # Prepare features
    X_train, y_train = model.prepare_features(train)
    X_val, y_val = model.prepare_features(val)
    X_test, y_test = model.prepare_features(test)

    logger.info(f"Features: {model.feature_names}")

    # Train
    model.train(X_train, y_train, X_val, y_val)

    # Evaluate
    logger.info("\nEvaluating on test set...")
    metrics = model.evaluate(X_test, y_test)

    # Feature importance
    logger.info("\nFeature Importance:")
    importance_df = model.feature_importance()
    logger.info("\n" + importance_df.head(10).to_string())

    # Save model
    import pickle
    model_path = Path(__file__).parent.parent / 'data' / 'models' / 'xgboost_points.pkl'
    model_path.parent.mkdir(parents=True, exist_ok=True)

    with open(model_path, 'wb') as f:
        pickle.dump(model, f)

    logger.info(f"\n📁 Model saved to: {model_path}")

    return model, metrics


def train_lightgbm_model():
    """Train LightGBM model for player props"""
    logger.info("\n" + "=" * 60)
    logger.info("TRAINING LIGHTGBM MODEL")
    logger.info("=" * 60)

    # Generate data
    data = generate_training_data(n_samples=2000)

    # Split
    from sklearn.model_selection import train_test_split
    train_val, test = train_test_split(data, test_size=0.2, random_state=42)
    train, val = train_test_split(train_val, test_size=0.2, random_state=42)

    # Initialize model
    model = MLPropModel(model_type='lightgbm')

    # Prepare features
    X_train, y_train = model.prepare_features(train)
    X_val, y_val = model.prepare_features(val)
    X_test, y_test = model.prepare_features(test)

    # Train
    model.train(X_train, y_train, X_val, y_val)

    # Evaluate
    metrics = model.evaluate(X_test, y_test)

    # Save model
    import pickle
    model_path = Path(__file__).parent.parent / 'data' / 'models' / 'lightgbm_points.pkl'

    with open(model_path, 'wb') as f:
        pickle.dump(model, f)

    logger.info(f"\n📁 Model saved to: {model_path}")

    return model, metrics


def compare_models():
    """Compare statistical vs ML models"""
    logger.info("\n" + "=" * 60)
    logger.info("MODEL COMPARISON")
    logger.info("=" * 60)

    # Generate test data
    test_data = generate_training_data(n_samples=200)

    # Statistical model (Poisson baseline)
    poisson_predictions = test_data['pts_mean_5'].values
    poisson_mae = np.mean(np.abs(poisson_predictions - test_data['actual_value'].values))

    logger.info(f"\nPoisson (baseline): MAE = {poisson_mae:.2f}")

    # Would compare with ML models here
    logger.info("\nComparison Summary:")
    logger.info("- Poisson: Simple, interpretable, fast")
    logger.info("- XGBoost: Better accuracy, feature interactions")
    logger.info("- LightGBM: Fast training, similar accuracy to XGBoost")
    logger.info("\nRecommendation: Use Poisson for speed, XGBoost for accuracy")


def main():
    """Main training function"""
    config = load_config()
    setup_logging(
        log_level=config['general']['log_level'],
        log_file='logs/ml_training.log'
    )

    logger.info("Starting ML model training...")
    logger.info("Using mock data for demonstration\n")

    try:
        # Train XGBoost
        xgb_model, xgb_metrics = train_xgboost_model()

        # Train LightGBM
        lgb_model, lgb_metrics = train_lightgbm_model()

        # Compare
        compare_models()

        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("TRAINING SUMMARY")
        logger.info("=" * 60)

        logger.info("\n✅ Training Complete!")
        logger.info(f"\nXGBoost - MAE: {xgb_metrics['mae']:.2f}, R²: {xgb_metrics['r2']:.3f}")
        logger.info(f"LightGBM - MAE: {lgb_metrics['mae']:.2f}, R²: {lgb_metrics['r2']:.3f}")

        logger.info("\nNext steps:")
        logger.info("1. Test models on real data")
        logger.info("2. Compare with Poisson baseline")
        logger.info("3. Retrain monthly with new data")

    except ImportError as e:
        logger.error(f"\n❌ ML libraries not installed: {e}")
        logger.error("Install with: pip install xgboost lightgbm scikit-learn")
        logger.info("\n💡 The bot works fine with statistical models (Poisson/Monte Carlo)")
        logger.info("   ML models are optional for advanced users")


if __name__ == "__main__":
    main()
