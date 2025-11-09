# Sports Props Intelligence Bot 🎯

AI-powered sports betting analytics system for prop bets across NBA, ACB, La Liga, and Tennis.

## ⚠️ Important Disclaimer

**This bot is for educational and research purposes only.**
- Not financial or betting advice
- Gamble only if legal in your jurisdiction
- Use responsible bankroll management
- No model guarantees profits

## 🎯 Features

- **Multi-Sport Support**: NBA, ACB (Spanish Basketball), La Liga (Soccer), ATP/WTA (Tennis)
- **Smart Prop Analysis**: Points, rebounds, assists, corners, aces, and more
- **Advanced Models**: Poisson, Negative Binomial, Monte Carlo simulations
- **EV Calculation**: Expected value and edge detection
- **Closing Line Value (CLV)**: Track performance vs closing lines
- **Interactive Dashboard**: Streamlit-based visual interface
- **Backtesting**: Historical performance analysis
- **Risk Management**: Kelly criterion, bankroll limits, drawdown protection

## 📊 Supported Markets

### Basketball (NBA/ACB)
- Player Points (Over/Under)
- Player Rebounds (Over/Under)
- Player Assists (Over/Under)
- Player PRA (Points + Rebounds + Assists)
- Player Three-Pointers Made
- Player Steals, Blocks

### Soccer (La Liga)
- Team Corners (Over/Under)
- Team Shots/Shots on Target
- Team Cards (Yellow/Red)
- Team Fouls
- Player Goals, Assists

### Tennis (ATP/WTA)
- Player Aces (Over/Under)
- Player Double Faults
- Total Games (Over/Under)
- Service Points Won

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/your-org/apuestas-bot.git
cd apuestas-bot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API keys
nano .env
```

**Required API Keys:**
- `THE_ODDS_API_KEY`: Get from [The Odds API](https://the-odds-api.com/)

**Optional:**
- Telegram Bot Token (for notifications)
- Email credentials (for alerts)
- Betfair API credentials (for exchange integration)

### 3. Initialize Database

```bash
python -c "from src.database import init_db; init_db()"
```

### 4. Run Dashboard

```bash
streamlit run app.py
```

The dashboard will open at `http://localhost:8501`

## 📁 Project Structure

```
apuestas-bot/
├── config/
│   ├── config.yaml          # Main configuration
│   └── books.yaml           # Bookmaker settings
├── data/
│   ├── raw/                 # Raw data from APIs
│   ├── curated/             # Processed data
│   └── results/             # Database and results
├── src/
│   ├── ingest/              # Data collection
│   │   ├── odds_collector.py    # Odds from The Odds API
│   │   ├── nba_scraper.py       # NBA stats
│   │   ├── acb_scraper.py       # ACB stats
│   │   ├── soccer_scraper.py    # La Liga stats
│   │   └── tennis_scraper.py    # Tennis stats
│   ├── features/            # Feature engineering
│   │   └── feature_engineering.py
│   ├── models/              # Probabilistic models
│   │   ├── poisson_model.py     # Poisson/NegBin models
│   │   └── monte_carlo.py       # MC simulations
│   ├── pricing/             # EV and pricing
│   │   └── ev_calculator.py
│   ├── reporting/           # Analytics and dashboard
│   │   ├── backtest.py
│   │   └── dashboard.py
│   ├── database.py          # Database models
│   └── utils.py             # Utilities
├── logs/                    # Application logs
├── app.py                   # Dashboard entry point
├── requirements.txt         # Python dependencies
└── README.md
```

## 🎮 Usage

### Dashboard Tabs

1. **🎯 Today** - Today's best picks ranked by EV
2. **🏀 Matches** - Detailed match analysis and predictions
3. **📈 Markets** - Market lines, consensus, and line movement
4. **📊 Historical** - Performance analytics, P&L, ROI, CLV
5. **⚙️ Config** - Bankroll, risk management, and sport settings
6. **🚨 Alerts** - Injury updates, line movements, API status

### Configuration

Edit `config/config.yaml` to customize:

- **Sports & Leagues**: Enable/disable specific leagues
- **Markets**: Choose which prop types to analyze
- **EV Thresholds**: Minimum edge required for picks
- **Bankroll Management**: Kelly fraction, bet limits
- **Risk Management**: Max drawdown, exposure limits

### Running Backtests

```python
from src.reporting.backtest import Backtest
from src.database import get_session
from src.utils import load_config
from datetime import datetime, timedelta

config = load_config()
session = get_session()
backtest = Backtest(config, session)

# Run 90-day backtest
results = backtest.run_backtest(
    start_date=datetime.now() - timedelta(days=90),
    end_date=datetime.now(),
    min_ev=0.03  # 3% minimum edge
)

print(f"ROI: {results['roi']:.2f}%")
print(f"Win Rate: {results['win_rate']:.2f}%")
print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
```

## 🔬 Models & Methods

### Poisson Model (Count Data)
Used for: Points, rebounds, corners, aces, etc.
- Estimates lambda from historical data
- Applies contextual adjustments (opponent, pace, minutes)
- Calculates P(Over) and P(Under) for any line

### Monte Carlo Simulation
Used for: Complex props with correlations
- Simulates minutes played → points scored
- Models PRA with component correlations
- Generates full probability distributions

### Expected Value (EV)
```
EV = P(win) × (Odds - 1) - P(lose) × 1
Edge = True Probability - Implied Probability
```

### Kelly Criterion (Bet Sizing)
```
Kelly % = (bp - q) / b
Where: b = net odds, p = win probability, q = lose probability
```

We use **fractional Kelly** (25% by default) for safety.

## 📊 Data Sources

### Odds
- **The Odds API**: Primary odds source (500 requests/month free tier)
- Supports: Pinnacle, Bet365, William Hill, Betfair, and more

### Stats
- **NBA**: nba_api (official NBA stats)
- **ACB**: SofaScore API
- **La Liga**: FBref, SofaScore
- **Tennis**: SofaScore, Tennis Abstract

## 🛡️ Risk Management

### Bankroll Limits
- **Kelly Fraction**: Default 0.25 (25% of full Kelly)
- **Min Bet**: 10€ (configurable)
- **Max Bet**: 100€ (configurable)
- **Max Daily Exposure**: 500€

### Auto-Pause
Bot automatically pauses betting if:
- Weekly drawdown > 15%
- Insufficient sample size (< 30 picks)
- API rate limits exceeded

## 📈 Performance Metrics

- **ROI**: Return on Investment
- **Win Rate**: Percentage of winning bets
- **CLV**: Closing Line Value (avg edge vs closing line)
- **Sharpe Ratio**: Risk-adjusted returns
- **Max Drawdown**: Largest peak-to-trough decline
- **Profit Factor**: Gross profit / Gross loss

## 🔧 Development

### Adding a New Sport

1. Create scraper in `src/ingest/your_sport_scraper.py`
2. Add feature extractor to `src/features/feature_engineering.py`
3. Create specialized model in `src/models/`
4. Update `config/config.yaml` with sport settings
5. Add to dashboard tabs

### Testing

```bash
# Run tests (when implemented)
pytest tests/

# Check coverage
pytest --cov=src tests/
```

## 📝 License

MIT License - See LICENSE file

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/your-org/apuestas-bot/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/apuestas-bot/discussions)

## ⚖️ Legal & Responsible Gambling

- **Age Requirement**: 18+ (or legal age in your jurisdiction)
- **Legality**: Ensure sports betting is legal in your location
- **Addiction Help**: Visit [BeGambleAware](https://www.begambleaware.org/)
- **Self-Exclusion**: Use GamStop (UK) or equivalent services

## 🙏 Acknowledgments

- The Odds API for odds data
- NBA API contributors
- Open source sports data community

---

**Remember**: No model guarantees profits. Sports betting involves risk. Only bet what you can afford to lose.

Good luck! 🍀
