"""Streamlit dashboard for Sports Props Bot - REAL DATA VERSION"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import sys
from pathlib import Path
import os

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from utils import load_config, setup_logging
from database import init_db, get_session, Match, Pick, Prediction, Odds
from sqlalchemy import desc, and_, func
from sqlalchemy.orm import Session


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
    """Get database session (cached)"""
    try:
        init_db()
        return get_session()
    except Exception as e:
        st.error(f"Error connecting to database: {e}")
        return None


def get_fresh_session():
    """Get fresh database session (not cached)"""
    try:
        return get_session()
    except Exception as e:
        st.error(f"Error connecting to database: {e}")
        return None


def render_header():
    """Render dashboard header"""
    st.title("📊 Sports Props Intelligence Bot")
    st.markdown("### AI-Powered Sports Betting Analytics (LIVE DATA)")

    # Status indicator
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown("---")
    with col2:
        if get_fresh_session():
            st.success("🟢 Database Connected")
        else:
            st.error("🔴 Database Error")
    with col3:
        api_key = os.getenv('THE_ODDS_API_KEY')
        if api_key and not api_key.startswith('${'):
            st.success("🟢 Odds API Ready")
        else:
            st.warning("🟡 Odds API Not Configured")


def render_sidebar():
    """Render sidebar with filters and risk controls"""
    st.sidebar.title("🎯 Filters & Risk Controls")

    # ========================================================================
    # RISK CONTROLS
    # ========================================================================
    st.sidebar.header("⚠️ Risk Management")

    # EV threshold
    min_ev = st.sidebar.slider(
        "Minimum EV %",
        min_value=0.0,
        max_value=20.0,
        value=5.0,
        step=0.5,
        help="Only show picks with EV above this threshold"
    ) / 100

    # Kelly fraction
    kelly_fraction = st.sidebar.slider(
        "Kelly Fraction",
        min_value=0.0,
        max_value=1.0,
        value=0.25,
        step=0.05,
        help="Fraction of Kelly to bet (0.25 = Quarter Kelly)"
    )

    # Max stake
    max_stake_pct = st.sidebar.slider(
        "Max Stake %",
        min_value=1.0,
        max_value=10.0,
        value=5.0,
        step=0.5,
        help="Maximum % of bankroll per bet"
    )

    # Odds range
    odds_range = st.sidebar.slider(
        "Odds Range",
        min_value=1.5,
        max_value=5.0,
        value=(1.7, 2.5),
        step=0.1,
        help="Filter picks by odds range"
    )

    st.sidebar.markdown("---")

    # ========================================================================
    # SPORT FILTERS
    # ========================================================================
    st.sidebar.header("🏆 Sports")

    sports_mapping = {
        "🏀 NBA": "basketball_nba",
        "🏀 EuroLeague": "basketball_euroleague",
        "⚽ La Liga": "soccer_laliga",
        "🎾 Tennis": "tennis"
    }

    selected_sports_display = st.sidebar.multiselect(
        "Select Sports",
        list(sports_mapping.keys()),
        default=list(sports_mapping.keys())[:2]
    )

    selected_sports = [sports_mapping[s] for s in selected_sports_display]

    # ========================================================================
    # DATE RANGE
    # ========================================================================
    st.sidebar.header("📅 Date Range")

    date_range = st.sidebar.date_input(
        "Show picks for",
        value=(datetime.now().date(), datetime.now().date() + timedelta(days=3)),
        help="Date range for picks"
    )

    # ========================================================================
    # REFRESH DATA
    # ========================================================================
    st.sidebar.markdown("---")

    if st.sidebar.button("🔄 Refresh Data", type="primary"):
        st.cache_resource.clear()
        st.rerun()

    # Generate new predictions button
    if st.sidebar.button("🎯 Generate New Predictions", type="secondary"):
        with st.spinner("Generating predictions..."):
            st.info("💡 Run: `python scripts/run_predictions.py` to generate new picks")
            st.info("This will use the current risk settings to generate picks")

    return {
        'sports': selected_sports,
        'date_range': date_range,
        'min_ev': min_ev,
        'kelly_fraction': kelly_fraction,
        'max_stake_pct': max_stake_pct,
        'odds_range': odds_range
    }


def get_picks_from_db(session: Session, filters: Dict) -> pd.DataFrame:
    """Get picks from database with filters"""

    if not session:
        return pd.DataFrame()

    try:
        # Build query
        query = session.query(Pick).filter(
            Pick.status == 'recommended'
        )

        # Filter by EV
        if filters.get('min_ev'):
            query = query.filter(Pick.expected_value >= filters['min_ev'])

        # Filter by odds
        if filters.get('odds_range'):
            min_odds, max_odds = filters['odds_range']
            query = query.filter(
                and_(Pick.odds >= min_odds, Pick.odds <= max_odds)
            )

        # Filter by date
        if filters.get('date_range'):
            if isinstance(filters['date_range'], tuple) and len(filters['date_range']) == 2:
                start_date, end_date = filters['date_range']
                query = query.filter(
                    and_(
                        Pick.created_at >= datetime.combine(start_date, datetime.min.time()),
                        Pick.created_at <= datetime.combine(end_date, datetime.max.time())
                    )
                )

        # Order by EV
        query = query.order_by(desc(Pick.expected_value))

        picks = query.all()

        if not picks:
            return pd.DataFrame()

        # Convert to DataFrame
        data = []
        for pick in picks:
            data.append({
                'ID': pick.id,
                'Player/Team': pick.player_name or 'Unknown',
                'Market': pick.market_type or 'Unknown',
                'Line': pick.line,
                'Selection': pick.selection.upper() if pick.selection else 'N/A',
                'Odds': pick.odds,
                'EV %': pick.expected_value * 100 if pick.expected_value else 0,
                'Model Prob': pick.estimated_prob if pick.estimated_prob else 0,
                'Stake %': pick.recommended_stake if pick.recommended_stake else 0,
                'Bookmaker': pick.bookmaker_display_name or pick.bookmaker or 'Unknown',
                'Betting URL': pick.betting_url or '',
                'Created': pick.created_at,
                'Result': pick.result or 'Pending'
            })

        df = pd.DataFrame(data)

        # Apply Kelly fraction and max stake from filters
        if 'kelly_fraction' in filters and not df.empty:
            df['Adjusted Stake %'] = df['Stake %'] * filters['kelly_fraction']
            df['Adjusted Stake %'] = df['Adjusted Stake %'].clip(upper=filters.get('max_stake_pct', 5.0))

        return df

    except Exception as e:
        st.error(f"Error fetching picks: {e}")
        return pd.DataFrame()


def render_today_tab(filters: Dict):
    """Render Today's Picks tab with REAL DATA"""
    st.header("🎯 Today's Best Picks (LIVE DATA)")

    session = get_fresh_session()

    if not session:
        st.error("❌ Cannot connect to database")
        st.info("Run: `python -c \"from src.database import init_db; init_db()\"` to initialize")
        return

    df = get_picks_from_db(session, filters)

    if df.empty:
        st.warning("📭 No picks found matching your filters")
        st.info("""
        **To generate picks:**
        1. Configure THE_ODDS_API_KEY in .env
        2. Run: `python scripts/collect_data.py`
        3. Run: `python scripts/run_predictions.py`
        4. Refresh this dashboard
        """)
        return

    # Show count
    st.success(f"✅ Found {len(df)} picks matching your criteria")

    # Sort by EV
    df_display = df.sort_values('EV %', ascending=False).copy()

    # Create clickable links for bookmakers
    def make_clickable(row):
        if row['Betting URL']:
            return f'<a href="{row["Betting URL"]}" target="_blank">{row["Bookmaker"]} 🔗</a>'
        return row['Bookmaker']

    df_display['Bookmaker Link'] = df_display.apply(make_clickable, axis=1)

    # Display columns
    display_cols = ['Player/Team', 'Market', 'Selection', 'Line', 'Odds',
                    'EV %', 'Model Prob', 'Adjusted Stake %', 'Bookmaker Link']

    # Style the dataframe
    def highlight_ev(val):
        if isinstance(val, (int, float)):
            if val > 8:
                return 'background-color: #90EE90'
            elif val > 5:
                return 'background-color: #FFFFE0'
            elif val > 3:
                return 'background-color: #FFE4B5'
        return ''

    styled_df = df_display[display_cols].style.map(
        highlight_ev, subset=['EV %']
    ).format({
        'EV %': '{:.1f}%',
        'Model Prob': '{:.1%}',
        'Adjusted Stake %': '{:.1f}%',
        'Odds': '{:.2f}',
        'Line': '{:.1f}'
    })

    st.write(styled_df.to_html(escape=False, index=False), unsafe_allow_html=True)

    # Metrics
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Picks", len(df))

    with col2:
        st.metric("Avg EV", f"{df['EV %'].mean():.1f}%")

    with col3:
        high_ev_picks = len(df[df['EV %'] > 8])
        st.metric("High EV Picks (>8%)", high_ev_picks)

    with col4:
        total_stake = df['Adjusted Stake %'].sum()
        st.metric("Total Exposure", f"{total_stake:.1f}%")

    # EV distribution chart
    st.subheader("📊 EV Distribution")
    fig = px.bar(df_display.head(10), x='Player/Team', y='EV %', color='Market',
                 title="Top 10 Picks by Expected Value",
                 hover_data=['Selection', 'Line', 'Odds', 'Bookmaker'])
    st.plotly_chart(fig, use_container_width=True, key='today_ev_chart')

    # Detailed picks
    st.subheader("📋 Detailed Pick Information")

    for idx, row in df_display.head(10).iterrows():
        with st.expander(f"🎯 {row['Player/Team']} - {row['Market']} {row['Selection']} {row['Line']} @ {row['Odds']:.2f}"):
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Expected Value", f"{row['EV %']:.2f}%")
                st.metric("Model Probability", f"{row['Model Prob']:.1%}")

            with col2:
                st.metric("Recommended Stake", f"{row['Adjusted Stake %']:.1f}%")
                st.metric("Odds", f"{row['Odds']:.2f}")

            with col3:
                st.metric("Bookmaker", row['Bookmaker'])
                if row['Betting URL']:
                    st.markdown(f"[🔗 Bet Now at {row['Bookmaker']}]({row['Betting URL']})")

            st.info(f"💡 **Analysis**: Based on model probability of {row['Model Prob']:.1%} vs implied odds of {1/row['Odds']:.1%}, this pick has an edge of {row['EV %']:.2f}%")

    session.close()


def render_matches_tab(filters: Dict):
    """Render Matches tab with details"""
    st.header("🏀 Match Details")

    session = get_fresh_session()

    if not session:
        st.error("❌ Cannot connect to database")
        return

    try:
        # Get matches
        matches = session.query(Match).filter(
            Match.commence_time >= datetime.now()
        ).order_by(Match.commence_time).limit(20).all()

        if not matches:
            st.warning("📭 No upcoming matches found")
            st.info("Run `python scripts/collect_data.py` to fetch match data")
            return

        for match in matches:
            # Get picks for this match
            picks_count = session.query(Pick).filter(
                Pick.match_id == match.id,
                Pick.status == 'recommended'
            ).count()

            match_time = match.commence_time.strftime('%H:%M')
            match_date = match.commence_time.strftime('%Y-%m-%d')

            with st.expander(f"⏰ {match_date} {match_time} - {match.home_team} vs {match.away_team} ({picks_count} props)"):
                # Get picks for this match
                picks = session.query(Pick).filter(
                    Pick.match_id == match.id,
                    Pick.status == 'recommended'
                ).order_by(desc(Pick.expected_value)).all()

                if picks:
                    for pick in picks[:5]:  # Show top 5
                        col1, col2, col3 = st.columns(3)

                        with col1:
                            st.write(f"**{pick.player_name}** - {pick.market_type}")
                            st.write(f"{pick.selection.upper()} {pick.line}")

                        with col2:
                            st.metric("EV", f"{pick.expected_value*100:.1f}%")
                            st.metric("Odds", f"{pick.odds:.2f}")

                        with col3:
                            st.write(f"**{pick.bookmaker_display_name or pick.bookmaker}**")
                            if pick.betting_url:
                                st.markdown(f"[🔗 Bet]({pick.betting_url})")
                else:
                    st.info("No recommended picks for this match")

    except Exception as e:
        st.error(f"Error fetching matches: {e}")
    finally:
        session.close()


def render_markets_tab():
    """Render Markets tab"""
    st.header("📈 Market Lines & Odds Comparison")

    session = get_fresh_session()

    if not session:
        st.error("❌ Cannot connect to database")
        return

    try:
        # Get recent odds
        odds = session.query(Odds).filter(
            Odds.created_at >= datetime.now() - timedelta(days=1)
        ).order_by(desc(Odds.created_at)).limit(50).all()

        if not odds:
            st.warning("📭 No odds data found")
            st.info("Run `python scripts/collect_data.py` to fetch odds")
            return

        # Group by match and market
        odds_data = []
        for odd in odds:
            odds_data.append({
                'Market': f"{odd.match_id} - {odd.market_type}",
                'Bookmaker': odd.bookmaker_display_name or odd.bookmaker,
                'Selection': odd.selection,
                'Price': odd.price,
                'Point': odd.point,
                'Updated': odd.created_at
            })

        df = pd.DataFrame(odds_data)

        st.dataframe(df, use_container_width=True)

        # Show best odds
        st.subheader("🏆 Best Available Odds")

        if not df.empty and 'Price' in df.columns:
            best_odds = df.loc[df.groupby('Market')['Price'].idxmax()]
            st.dataframe(best_odds[['Market', 'Bookmaker', 'Price']], use_container_width=True)

    except Exception as e:
        st.error(f"Error fetching odds: {e}")
    finally:
        session.close()


def render_historical_tab():
    """Render Historical Performance tab with REAL DATA"""
    st.header("📊 Historical Performance (REAL RESULTS)")

    session = get_fresh_session()

    if not session:
        st.error("❌ Cannot connect to database")
        return

    try:
        # Time period selector
        period = st.selectbox("Period", ["Last 7 Days", "Last 30 Days", "Last 90 Days", "All Time"])

        # Calculate date filter
        if period == "Last 7 Days":
            date_filter = datetime.now() - timedelta(days=7)
        elif period == "Last 30 Days":
            date_filter = datetime.now() - timedelta(days=30)
        elif period == "Last 90 Days":
            date_filter = datetime.now() - timedelta(days=90)
        else:
            date_filter = datetime.min

        # Get settled picks
        settled_picks = session.query(Pick).filter(
            and_(
                Pick.created_at >= date_filter,
                Pick.result.in_(['won', 'lost', 'push'])
            )
        ).all()

        if not settled_picks:
            st.warning("📭 No historical results found")
            st.info("""
            Results will appear here after:
            1. Picks are generated
            2. Events are completed
            3. Results are updated (run `python scripts/update_results.py`)
            """)
            return

        # Calculate metrics
        total_picks = len(settled_picks)
        won_picks = len([p for p in settled_picks if p.result == 'won'])
        lost_picks = len([p for p in settled_picks if p.result == 'lost'])
        push_picks = len([p for p in settled_picks if p.result == 'push'])

        win_rate = (won_picks / total_picks * 100) if total_picks > 0 else 0

        # Calculate P&L (assuming unit stakes)
        total_pnl = sum([
            (p.odds - 1) if p.result == 'won' else
            -1 if p.result == 'lost' else
            0
            for p in settled_picks
        ])

        roi = (total_pnl / total_picks * 100) if total_picks > 0 else 0

        # Metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Picks", total_picks)

        with col2:
            st.metric("ROI", f"{roi:.1f}%",
                     delta=f"{roi:.1f}%" if roi > 0 else None,
                     delta_color="normal")

        with col3:
            st.metric("Win Rate", f"{win_rate:.1f}%")

        with col4:
            st.metric("P&L (units)", f"{total_pnl:+.1f}")

        # Results breakdown
        st.subheader("📊 Results Breakdown")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Won", won_picks, delta_color="normal")
        with col2:
            st.metric("Lost", lost_picks, delta_color="inverse")
        with col3:
            st.metric("Push", push_picks, delta_color="off")

        # Performance by market
        st.subheader("📈 Performance by Market")

        market_stats = {}
        for pick in settled_picks:
            market = pick.market_type or 'Unknown'
            if market not in market_stats:
                market_stats[market] = {'won': 0, 'lost': 0, 'push': 0}

            market_stats[market][pick.result] += 1

        market_data = []
        for market, stats in market_stats.items():
            total = stats['won'] + stats['lost'] + stats['push']
            win_rate = (stats['won'] / total * 100) if total > 0 else 0

            market_data.append({
                'Market': market,
                'Picks': total,
                'Won': stats['won'],
                'Lost': stats['lost'],
                'Win Rate %': win_rate
            })

        if market_data:
            df_markets = pd.DataFrame(market_data)
            st.dataframe(df_markets, use_container_width=True)

    except Exception as e:
        st.error(f"Error fetching historical data: {e}")
    finally:
        session.close()


def render_config_tab():
    """Render Configuration tab"""
    st.header("⚙️ Configuration")

    st.info("""
    💡 **Risk settings are in the sidebar** (left side)

    Adjust:
    - Minimum EV threshold
    - Kelly fraction
    - Max stake per bet
    - Odds range
    """)

    # API Status
    st.subheader("🔌 API Status")

    col1, col2 = st.columns(2)

    with col1:
        api_key = os.getenv('THE_ODDS_API_KEY')
        if api_key and not api_key.startswith('${'):
            st.success("✅ The Odds API: Configured")
            st.code(f"Key: {api_key[:8]}...{api_key[-4:]}")
        else:
            st.error("❌ The Odds API: Not configured")
            st.info("Set THE_ODDS_API_KEY in .env file")

    with col2:
        session = get_fresh_session()
        if session:
            st.success("✅ Database: Connected")

            # Count records
            try:
                picks_count = session.query(Pick).count()
                matches_count = session.query(Match).count()

                st.metric("Total Picks in DB", picks_count)
                st.metric("Total Matches in DB", matches_count)

                session.close()
            except:
                pass
        else:
            st.error("❌ Database: Not connected")

    # Scripts to run
    st.subheader("🚀 Quick Actions")

    st.code("""
# Collect latest odds
python scripts/collect_data.py

# Generate predictions
python scripts/run_predictions.py

# Update results
python scripts/update_results.py

# Initialize database
python -c "from src.database import init_db; init_db()"
    """, language="bash")


def render_alerts_tab():
    """Render Alerts tab"""
    st.header("🚨 Alerts & Monitoring")

    st.warning("⚠️ Alert system not yet implemented")

    st.info("""
    **Planned features:**
    - Telegram notifications for high EV picks
    - Email alerts for line movements
    - Injury alerts
    - API rate limit warnings

    See: `QUE_FALTA_PARA_SER_PROFESIONAL.md` for implementation roadmap
    """)

    # API Status
    st.subheader("📊 Current Status")

    col1, col2, col3 = st.columns(3)

    with col1:
        api_key = os.getenv('THE_ODDS_API_KEY')
        if api_key:
            st.metric("The Odds API", "✅ Configured")
        else:
            st.metric("The Odds API", "❌ Not Set")

    with col2:
        st.metric("Last Dashboard Refresh", datetime.now().strftime("%H:%M:%S"))

    with col3:
        session = get_fresh_session()
        if session:
            st.metric("Database", "✅ Connected")
            session.close()
        else:
            st.metric("Database", "❌ Error")


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
        <p>Sports Props Intelligence Bot v2.0 (LIVE DATA) | ⚠️ For educational purposes only</p>
        <p>Gamble responsibly. This is not financial advice.</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
