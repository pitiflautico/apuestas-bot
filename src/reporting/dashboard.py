"""Streamlit dashboard for Sports Props Bot"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from utils import load_config, setup_logging
from database import get_session, Match, Pick, Prediction
from sqlalchemy import desc


# Page configuration
st.set_page_config(
    page_title="Sports Props Intelligence Bot",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


@st.cache_resource
def load_app_config():
    """Load configuration"""
    return load_config()


@st.cache_resource
def get_db_session_cached():
    """Get database session"""
    return get_session()


def render_header():
    """Render dashboard header"""
    st.title("📊 Sports Props Intelligence Bot")
    st.markdown("### AI-Powered Sports Betting Analytics")
    st.markdown("---")


def render_sidebar():
    """Render sidebar with filters"""
    st.sidebar.title("🎯 Filters")

    # Sport filter
    sports = st.sidebar.multiselect(
        "Sports",
        ["Basketball (NBA)", "Basketball (ACB)", "Soccer (La Liga)", "Tennis (ATP/WTA)"],
        default=["Basketball (NBA)"]
    )

    # Date range
    date_range = st.sidebar.date_input(
        "Date Range",
        value=(datetime.now(), datetime.now() + timedelta(days=7))
    )

    # EV threshold
    min_ev = st.sidebar.slider(
        "Minimum EV %",
        min_value=0.0,
        max_value=20.0,
        value=3.0,
        step=0.5
    ) / 100

    # Odds range
    odds_range = st.sidebar.slider(
        "Odds Range",
        min_value=1.5,
        max_value=5.0,
        value=(1.5, 3.0),
        step=0.1
    )

    return {
        'sports': sports,
        'date_range': date_range,
        'min_ev': min_ev,
        'odds_range': odds_range
    }


def render_today_tab(filters: Dict):
    """Render Today's Picks tab"""
    st.header("🎯 Today's Best Picks")

    # Mock data for demo
    picks_data = {
        'Player/Team': ['LeBron James', 'Luka Doncic', 'Real Madrid', 'Carlos Alcaraz'],
        'Market': ['Points', 'PRA', 'Corners', 'Aces'],
        'Line': [25.5, 45.5, 5.5, 8.5],
        'Selection': ['Over', 'Over', 'Over', 'Over'],
        'Odds': [1.90, 1.85, 2.10, 1.95],
        'EV %': [5.2, 6.8, 4.1, 3.9],
        'Model Prob': [0.58, 0.62, 0.52, 0.56],
        'Confidence': ['High', 'High', 'Medium', 'Medium'],
        'Bookmaker': ['Bet365', 'Pinnacle', 'William Hill', 'Bet365']
    }

    df = pd.DataFrame(picks_data)

    # Sort by EV
    df = df.sort_values('EV %', ascending=False)

    # Style the dataframe
    def highlight_ev(val):
        if val > 5:
            return 'background-color: #90EE90'
        elif val > 3:
            return 'background-color: #FFFFE0'
        return ''

    styled_df = df.style.applymap(highlight_ev, subset=['EV %'])

    st.dataframe(styled_df, use_container_width=True, height=400)

    # Metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Picks", len(df))

    with col2:
        st.metric("Avg EV", f"{df['EV %'].mean():.1f}%")

    with col3:
        st.metric("High Confidence", len(df[df['Confidence'] == 'High']))

    with col4:
        st.metric("Expected Daily ROI", "4.2%")

    # EV distribution chart
    st.subheader("EV Distribution")
    fig = px.bar(df, x='Player/Team', y='EV %', color='Market',
                 title="Expected Value by Pick")
    st.plotly_chart(fig, use_container_width=True)


def render_matches_tab(filters: Dict):
    """Render Matches tab with details"""
    st.header("🏀 Match Details")

    # Mock matches
    matches = [
        {
            'match': 'Lakers vs Warriors',
            'time': '20:00',
            'sport': 'NBA',
            'available_props': 45
        },
        {
            'match': 'Real Madrid vs Barcelona',
            'time': '21:00',
            'sport': 'La Liga',
            'available_props': 28
        }
    ]

    for match in matches:
        with st.expander(f"⏰ {match['time']} - {match['match']} ({match['available_props']} props)"):
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Player Props")
                st.write("LeBron James - Points O/U 25.5")
                st.write("Stephen Curry - Threes O/U 4.5")

            with col2:
                st.subheader("Model Predictions")
                # Distribution chart
                x = list(range(15, 40))
                y = [abs(i - 27) for i in x]  # Mock distribution
                fig = go.Figure(data=[go.Bar(x=x, y=y)])
                fig.update_layout(title="LeBron Points Distribution", height=300)
                st.plotly_chart(fig, use_container_width=True)


def render_markets_tab():
    """Render Markets tab"""
    st.header("📈 Market Lines & Consensus")

    # Mock market data
    market_data = {
        'Market': ['LeBron Points O25.5', 'Luka PRA O45.5', 'RM Corners O5.5'],
        'Pinnacle': [1.95, 1.90, 2.05],
        'Bet365': [1.90, 1.85, 2.10],
        'William Hill': [1.88, 1.87, 2.15],
        'Best Odds': [1.95, 1.90, 2.15],
        'Avg Odds': [1.91, 1.87, 2.10]
    }

    df = pd.DataFrame(market_data)
    st.dataframe(df, use_container_width=True)

    # Line movement chart
    st.subheader("Line Movement - LeBron James Points")

    timestamps = pd.date_range(end=datetime.now(), periods=24, freq='H')
    odds = [1.95 + (i % 5) * 0.02 for i in range(24)]

    fig = px.line(x=timestamps, y=odds, title="Odds Movement (Last 24h)")
    fig.update_layout(xaxis_title="Time", yaxis_title="Odds")
    st.plotly_chart(fig, use_container_width=True)


def render_historical_tab():
    """Render Historical Performance tab"""
    st.header("📊 Historical Performance")

    # Time period selector
    period = st.selectbox("Period", ["Last 7 Days", "Last 30 Days", "Last 90 Days", "All Time"])

    # Metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Picks", "127", delta="12")

    with col2:
        st.metric("ROI", "8.2%", delta="1.3%")

    with col3:
        st.metric("Win Rate", "54.3%", delta="-0.5%")

    with col4:
        st.metric("Avg CLV", "+2.1%", delta="0.4%")

    # P&L Chart
    st.subheader("Cumulative P&L")

    dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
    cumulative_pnl = [0]
    for i in range(1, 30):
        cumulative_pnl.append(cumulative_pnl[-1] + (5 if i % 3 != 0 else -3))

    fig = px.line(x=dates, y=cumulative_pnl, title="Cumulative Profit/Loss")
    fig.update_layout(xaxis_title="Date", yaxis_title="P&L (units)")
    st.plotly_chart(fig, use_container_width=True)

    # Performance by market
    st.subheader("Performance by Market")

    market_performance = {
        'Market': ['Points', 'Rebounds', 'Assists', 'PRA', 'Corners', 'Aces'],
        'Picks': [45, 32, 28, 15, 20, 18],
        'ROI %': [12.3, 6.5, 4.2, 15.8, 9.1, 7.3],
        'Win Rate %': [56.2, 52.1, 51.4, 58.3, 54.0, 53.2]
    }

    df = pd.DataFrame(market_performance)

    fig = px.bar(df, x='Market', y='ROI %', title="ROI by Market Type")
    st.plotly_chart(fig, use_container_width=True)


def render_config_tab():
    """Render Configuration tab"""
    st.header("⚙️ Configuration")

    config = load_app_config()

    # Bankroll settings
    st.subheader("💰 Bankroll Management")

    col1, col2 = st.columns(2)

    with col1:
        bankroll = st.number_input("Current Bankroll (€)", value=1000.0, step=100.0)
        kelly_fraction = st.slider("Kelly Fraction", 0.0, 1.0, 0.25, 0.05)

    with col2:
        min_bet = st.number_input("Min Bet (€)", value=10.0, step=5.0)
        max_bet = st.number_input("Max Bet (€)", value=100.0, step=10.0)

    # Risk settings
    st.subheader("⚠️ Risk Management")

    col1, col2 = st.columns(2)

    with col1:
        max_daily_exposure = st.number_input("Max Daily Exposure (€)", value=500.0, step=50.0)
        max_dd_pct = st.slider("Max Weekly DD %", 0.0, 50.0, 15.0, 1.0)

    with col2:
        min_ev_pct = st.slider("Min EV %", 0.0, 10.0, 3.0, 0.5)
        max_vig = st.slider("Max Acceptable Vig %", 0.0, 20.0, 10.0, 1.0)

    # Enabled sports
    st.subheader("🏆 Enabled Sports & Leagues")

    col1, col2 = st.columns(2)

    with col1:
        nba_enabled = st.checkbox("NBA", value=True)
        acb_enabled = st.checkbox("ACB", value=True)

    with col2:
        laliga_enabled = st.checkbox("La Liga", value=True)
        tennis_enabled = st.checkbox("Tennis (ATP/WTA)", value=True)

    if st.button("💾 Save Configuration"):
        st.success("Configuration saved successfully!")


def render_alerts_tab():
    """Render Alerts tab"""
    st.header("🚨 Alerts & News")

    # Recent alerts
    st.subheader("Recent Alerts")

    alerts = [
        {
            'time': '10:30',
            'type': 'Injury',
            'message': 'LeBron James questionable (ankle) - Monitor lineup',
            'severity': 'warning'
        },
        {
            'time': '09:15',
            'message': 'Line moved: Luka PRA from 45.5 to 46.5',
            'type': 'Line Movement',
            'severity': 'info'
        },
        {
            'time': '08:00',
            'type': 'Weather',
            'message': 'Rain expected in Madrid - May affect corners',
            'severity': 'info'
        }
    ]

    for alert in alerts:
        severity_colors = {
            'warning': '🟡',
            'info': '🔵',
            'critical': '🔴'
        }

        icon = severity_colors.get(alert['severity'], '🔵')
        st.markdown(f"{icon} **{alert['time']}** - {alert['type']}: {alert['message']}")

    # Rate limit info
    st.subheader("📊 API Status")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("The Odds API", "450/500", help="Requests remaining this month")

    with col2:
        st.metric("Last Update", "5 min ago")

    with col3:
        st.metric("Status", "✅ Healthy")


def main():
    """Main dashboard function"""
    render_header()

    # Sidebar filters
    filters = render_sidebar()

    # Tabs
    tabs = st.tabs([
        "🎯 Today",
        "🏀 Matches",
        "📈 Markets",
        "📊 Historical",
        "⚙️ Config",
        "🚨 Alerts"
    ])

    with tabs[0]:
        render_today_tab(filters)

    with tabs[1]:
        render_matches_tab(filters)

    with tabs[2]:
        render_markets_tab()

    with tabs[3]:
        render_historical_tab()

    with tabs[4]:
        render_config_tab()

    with tabs[5]:
        render_alerts_tab()

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center'>
        <p>Sports Props Intelligence Bot v1.0 | ⚠️ For educational purposes only</p>
        <p>Gamble responsibly. This is not financial advice.</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
