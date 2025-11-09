"""Utility functions for the Sports Props Bot"""

import yaml
import os
from pathlib import Path
from typing import Any, Dict
from datetime import datetime
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def get_project_root() -> Path:
    """Get the project root directory"""
    return Path(__file__).parent.parent


def load_config(config_name: str = "config.yaml") -> Dict[str, Any]:
    """Load YAML configuration file

    Args:
        config_name: Name of config file in config/ directory

    Returns:
        Dictionary with configuration
    """
    config_path = get_project_root() / "config" / config_name

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    # Replace environment variables in config
    config = _replace_env_vars(config)

    return config


def _replace_env_vars(obj: Any) -> Any:
    """Recursively replace ${VAR} with environment variables"""
    if isinstance(obj, dict):
        return {k: _replace_env_vars(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_replace_env_vars(item) for item in obj]
    elif isinstance(obj, str) and obj.startswith("${") and obj.endswith("}"):
        var_name = obj[2:-1]
        return os.getenv(var_name, obj)
    return obj


def setup_logging(log_level: str = "INFO", log_file: str = None) -> logging.Logger:
    """Setup logging configuration

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path

    Returns:
        Logger instance
    """
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {log_level}')

    # Create logs directory if it doesn't exist
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

    # Configure logging
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file) if log_file else logging.NullHandler()
        ]
    )

    return logging.getLogger(__name__)


def calculate_implied_probability(odds: float, format: str = "decimal") -> float:
    """Calculate implied probability from odds

    Args:
        odds: The odds value
        format: Odds format (decimal, american, fractional)

    Returns:
        Implied probability as a decimal (0-1)
    """
    if format == "decimal":
        return 1 / odds
    elif format == "american":
        if odds > 0:
            return 100 / (odds + 100)
        else:
            return abs(odds) / (abs(odds) + 100)
    elif format == "fractional":
        # odds should be like "5/2" as string
        num, den = map(float, str(odds).split('/'))
        return den / (num + den)
    else:
        raise ValueError(f"Unknown odds format: {format}")


def remove_vig(probs: list) -> list:
    """Remove vigorish from implied probabilities

    Args:
        probs: List of implied probabilities

    Returns:
        List of normalized true probabilities
    """
    total = sum(probs)
    if total == 0:
        return probs
    return [p / total for p in probs]


def kelly_criterion(probability: float, odds: float, fraction: float = 1.0) -> float:
    """Calculate Kelly Criterion bet size

    Args:
        probability: True probability of winning (0-1)
        odds: Decimal odds
        fraction: Kelly fraction (0-1), default 1.0 for full Kelly

    Returns:
        Fraction of bankroll to bet (0-1)
    """
    b = odds - 1  # net odds
    q = 1 - probability  # probability of losing

    kelly = (b * probability - q) / b

    # Apply fraction and ensure non-negative
    return max(0, kelly * fraction)


def format_currency(amount: float, currency: str = "EUR") -> str:
    """Format amount as currency

    Args:
        amount: Amount to format
        currency: Currency code

    Returns:
        Formatted string
    """
    return f"{amount:.2f} {currency}"


def timestamp_to_str(timestamp: datetime, format: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Convert timestamp to string

    Args:
        timestamp: Datetime object
        format: String format

    Returns:
        Formatted string
    """
    return timestamp.strftime(format)
