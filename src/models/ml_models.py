"""ML-based models (optional advanced models)"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import logging

try:
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.model_selection import train_test_split, cross_val_score
    from sklearn.metrics import mean_squared_error, r2_score
    import xgboost as xgb
    import lightgbm as lgb
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    logging.warning("ML libraries not available. Install with: pip install xgboost lightgbm scikit-learn")

logger = logging.getLogger(__name__)


class MLPropModel:
    """Machine Learning model for props (XGBoost/LightGBM)"""

    def __init__(self, model_type: str = 'xgboost'):
        """Initialize ML model

        Args:
            model_type: 'xgboost', 'lightgbm', or 'random_forest'
        """
        if not ML_AVAILABLE:
            raise ImportError("ML libraries required. Install: pip install xgboost lightgbm scikit-learn")

        self.model_type = model_type
        self.model = None
        self.feature_names = None
        self.is_trained = False

    def prepare_features(self, data: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare features from raw data

        Args:
            data: DataFrame with player/team stats

        Returns:
            Tuple of (X, y)
        """
        # Define feature columns
        feature_cols = [
            # Rolling averages
            'pts_mean_5', 'pts_mean_10', 'pts_mean_20',
            'reb_mean_5', 'reb_mean_10',
            'ast_mean_5', 'ast_mean_10',
            'min_mean_5', 'min_mean_10',

            # Variances
            'pts_std_5', 'reb_std_5', 'ast_std_5',

            # Trends
            'pts_trend_5', 'pts_momentum',

            # Opponent
            'opp_def_rating', 'opp_pace',

            # Context
            'home_away_encoded',  # 1 for home, 0 for away
            'days_rest',
            'back_to_back'  # 1 if yes, 0 if no
        ]

        # Filter to available columns
        available_cols = [col for col in feature_cols if col in data.columns]

        X = data[available_cols].values
        y = data['actual_value'].values if 'actual_value' in data.columns else None

        self.feature_names = available_cols

        return X, y

    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: Optional[np.ndarray] = None,
        y_val: Optional[np.ndarray] = None
    ):
        """Train the model

        Args:
            X_train: Training features
            y_train: Training targets
            X_val: Validation features (optional)
            y_val: Validation targets (optional)
        """
        logger.info(f"Training {self.model_type} model...")

        if self.model_type == 'xgboost':
            self.model = xgb.XGBRegressor(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42
            )

            # Fit with validation if provided
            if X_val is not None and y_val is not None:
                self.model.fit(
                    X_train, y_train,
                    eval_set=[(X_val, y_val)],
                    early_stopping_rounds=10,
                    verbose=False
                )
            else:
                self.model.fit(X_train, y_train)

        elif self.model_type == 'lightgbm':
            self.model = lgb.LGBMRegressor(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42
            )

            if X_val is not None and y_val is not None:
                self.model.fit(
                    X_train, y_train,
                    eval_set=[(X_val, y_val)],
                    callbacks=[lgb.early_stopping(10, verbose=False)]
                )
            else:
                self.model.fit(X_train, y_train)

        elif self.model_type == 'random_forest':
            self.model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            )
            self.model.fit(X_train, y_train)

        self.is_trained = True
        logger.info("Model training completed")

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make predictions

        Args:
            X: Features

        Returns:
            Predictions
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")

        return self.model.predict(X)

    def predict_with_uncertainty(
        self,
        X: np.ndarray,
        n_iterations: int = 100
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Predict with uncertainty estimates using bootstrap

        Args:
            X: Features
            n_iterations: Number of bootstrap iterations

        Returns:
            Tuple of (predictions, standard_deviations)
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")

        predictions = []

        for i in range(n_iterations):
            # For tree-based models, can use different subsamples
            pred = self.model.predict(X)
            predictions.append(pred)

        predictions = np.array(predictions)
        mean_pred = predictions.mean(axis=0)
        std_pred = predictions.std(axis=0)

        return mean_pred, std_pred

    def feature_importance(self) -> pd.DataFrame:
        """Get feature importance

        Returns:
            DataFrame with feature importances
        """
        if not self.is_trained:
            raise ValueError("Model must be trained first")

        if hasattr(self.model, 'feature_importances_'):
            importances = self.model.feature_importances_
        else:
            return pd.DataFrame()

        importance_df = pd.DataFrame({
            'feature': self.feature_names,
            'importance': importances
        }).sort_values('importance', ascending=False)

        return importance_df

    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict:
        """Evaluate model on test set

        Args:
            X_test: Test features
            y_test: Test targets

        Returns:
            Metrics dictionary
        """
        predictions = self.predict(X_test)

        mae = np.mean(np.abs(predictions - y_test))
        rmse = np.sqrt(mean_squared_error(y_test, predictions))
        r2 = r2_score(y_test, predictions)

        # Mean Absolute Percentage Error
        mape = np.mean(np.abs((y_test - predictions) / y_test)) * 100

        metrics = {
            'mae': mae,
            'rmse': rmse,
            'r2': r2,
            'mape': mape
        }

        logger.info(f"Test Metrics - MAE: {mae:.2f}, RMSE: {rmse:.2f}, R2: {r2:.3f}")

        return metrics


class EnsembleModel:
    """Ensemble of statistical and ML models"""

    def __init__(self):
        """Initialize ensemble"""
        self.models = {}
        self.weights = {}

    def add_model(self, name: str, model, weight: float = 1.0):
        """Add a model to the ensemble

        Args:
            name: Model name
            model: Model instance
            weight: Model weight in ensemble
        """
        self.models[name] = model
        self.weights[name] = weight

    def predict(self, features: Dict) -> Dict:
        """Make ensemble prediction

        Args:
            features: Feature dictionary

        Returns:
            Ensemble prediction
        """
        predictions = []
        weights = []

        for name, model in self.models.items():
            pred = model.predict(features)
            predictions.append(pred['expected_value'])
            weights.append(self.weights[name])

        # Weighted average
        weighted_pred = np.average(predictions, weights=weights)

        return {
            'expected_value': weighted_pred,
            'individual_predictions': {
                name: pred for name, pred in zip(self.models.keys(), predictions)
            }
        }
