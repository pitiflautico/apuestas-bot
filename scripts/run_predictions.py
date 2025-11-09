"""Script to generate predictions for upcoming matches"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from utils import load_config, setup_logging
from models.poisson_model import BasketballPoissonModel, SoccerPoissonModel
from models.monte_carlo import BasketballMonteCarloModel, TennisMonteCarloModel
from pricing.ev_calculator import EVCalculator
from database import get_session
import logging

logger = logging.getLogger(__name__)


def main():
    """Main prediction function"""
    config = load_config()
    setup_logging(
        log_level=config['general']['log_level'],
        log_file=config['general']['log_file']
    )

    logger.info("Starting prediction generation...")

    # Initialize models
    nba_poisson = BasketballPoissonModel()
    nba_mc = BasketballMonteCarloModel()
    soccer_model = SoccerPoissonModel()
    tennis_mc = TennisMonteCarloModel()

    # Initialize EV calculator
    ev_calc = EVCalculator(config)

    # Example: Predict NBA player props
    logger.info("Generating NBA predictions...")

    # Mock features (would come from feature extraction)
    player_features = {
        'pts_mean_5': 27.5,
        'pts_std': 6.2,
        'min_mean_5': 35.0,
        'min_std_5': 3.5,
        'pts_trend_5': 0.05,
        'opp_def_rating': 110,
        'opp_pace': 102
    }

    line = 25.5
    odds = 1.90

    # Poisson prediction
    poisson_pred = nba_poisson.predict_player_points(player_features, line)
    logger.info(f"Poisson prediction: {poisson_pred}")

    # Monte Carlo prediction
    mc_pred = nba_mc.predict_player_points(player_features, line)
    logger.info(f"Monte Carlo prediction: {mc_pred}")

    # Calculate EV
    prob_over = mc_pred['prob_over']
    ev = ev_calc.calculate_ev(prob_over, odds)
    edge = ev_calc.calculate_edge_percent(prob_over, odds)

    logger.info(f"EV: {ev:.2f}, Edge: {edge:.2f}%")

    if ev_calc.is_positive_ev(prob_over, odds):
        logger.info("✅ POSITIVE EV BET FOUND!")

        # Calculate stake
        stake = ev_calc.calculate_stake(
            bankroll=1000,
            true_probability=prob_over,
            odds=odds,
            strategy=config['bankroll']['strategy'],
            kelly_fraction=config['bankroll']['kelly_fraction'],
            min_bet=config['bankroll']['min_bet'],
            max_bet=config['bankroll']['max_bet']
        )

        logger.info(f"Recommended stake: €{stake:.2f}")

    logger.info("Prediction generation completed!")


if __name__ == "__main__":
    main()
