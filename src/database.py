"""Database models and setup for Sports Props Bot"""

from sqlalchemy import (
    create_engine, Column, Integer, String, Float, DateTime,
    Boolean, ForeignKey, Text, JSON
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

Base = declarative_base()


class Match(Base):
    """Match/Game information"""
    __tablename__ = 'matches'

    id = Column(Integer, primary_key=True)
    sport = Column(String(50), nullable=False)  # basketball, soccer, tennis
    league = Column(String(100), nullable=False)  # NBA, ACB, LaLiga, ATP, WTA
    home_team = Column(String(200))
    away_team = Column(String(200))
    player1 = Column(String(200))  # For tennis
    player2 = Column(String(200))  # For tennis
    match_date = Column(DateTime, nullable=False)
    venue = Column(String(200))
    external_id = Column(String(200), unique=True)  # ID from data source
    status = Column(String(50))  # scheduled, live, finished, postponed
    home_score = Column(Integer)
    away_score = Column(Integer)
    match_metadata = Column(JSON)  # Additional match info (renamed from 'metadata' to avoid SQLAlchemy conflict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    odds = relationship("Odds", back_populates="match")
    predictions = relationship("Prediction", back_populates="match")
    results = relationship("Result", back_populates="match")


class Odds(Base):
    """Odds data from bookmakers"""
    __tablename__ = 'odds'

    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey('matches.id'), nullable=False)
    bookmaker = Column(String(100), nullable=False)
    bookmaker_display_name = Column(String(200))  # Display name (e.g., "Bet365", "William Hill")
    bookmaker_url = Column(String(500))  # Direct URL to betting page
    market_type = Column(String(100), nullable=False)  # points, corners, aces, etc.
    player_name = Column(String(200))  # For player props
    line = Column(Float)  # Over/under line
    over_odds = Column(Float)
    under_odds = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    is_closing_line = Column(Boolean, default=False)

    # Relationships
    match = relationship("Match", back_populates="odds")


class Prediction(Base):
    """Model predictions"""
    __tablename__ = 'predictions'

    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey('matches.id'), nullable=False)
    market_type = Column(String(100), nullable=False)
    player_name = Column(String(200))
    model_name = Column(String(100), nullable=False)  # poisson, bayesian, etc.
    predicted_value = Column(Float)  # Expected value for the metric
    predicted_std = Column(Float)  # Standard deviation
    prob_over = Column(Float)  # Probability over the line
    prob_under = Column(Float)  # Probability under the line
    line = Column(Float)  # The line we're predicting against
    confidence = Column(Float)  # Model confidence 0-1
    features_used = Column(JSON)  # Feature snapshot
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    match = relationship("Match", back_populates="predictions")


class Pick(Base):
    """Recommended or executed picks"""
    __tablename__ = 'picks'

    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey('matches.id'), nullable=False)
    market_type = Column(String(100), nullable=False)
    player_name = Column(String(200))
    selection = Column(String(20), nullable=False)  # over, under
    line = Column(Float, nullable=False)
    odds = Column(Float, nullable=False)
    bookmaker = Column(String(100), nullable=False)
    bookmaker_display_name = Column(String(200))  # Display name
    betting_url = Column(String(500))  # Direct URL to place the bet

    # EV Calculations
    estimated_prob = Column(Float, nullable=False)
    expected_value = Column(Float, nullable=False)
    edge_percent = Column(Float, nullable=False)

    # Bet sizing
    recommended_stake = Column(Float)
    actual_stake = Column(Float)

    # Status
    status = Column(String(50))  # recommended, placed, won, lost, void
    result = Column(String(20))  # won, lost, push, pending
    profit_loss = Column(Float)

    # CLV tracking
    closing_odds = Column(Float)
    clv = Column(Float)  # Closing line value

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    placed_at = Column(DateTime)
    settled_at = Column(DateTime)

    # Metadata
    notes = Column(Text)


class Result(Base):
    """Actual match results for verification"""
    __tablename__ = 'results'

    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey('matches.id'), nullable=False)
    market_type = Column(String(100), nullable=False)
    player_name = Column(String(200))
    actual_value = Column(Float, nullable=False)  # Actual outcome
    source = Column(String(100))  # Data source for verification
    verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    match = relationship("Match", back_populates="results")


class PlayerStats(Base):
    """Player statistics history"""
    __tablename__ = 'player_stats'

    id = Column(Integer, primary_key=True)
    player_name = Column(String(200), nullable=False)
    sport = Column(String(50), nullable=False)
    league = Column(String(100), nullable=False)
    season = Column(String(20))
    game_date = Column(DateTime)
    opponent = Column(String(200))
    home_away = Column(String(10))

    # Basketball stats
    minutes = Column(Float)
    points = Column(Integer)
    rebounds = Column(Integer)
    assists = Column(Integer)
    steals = Column(Integer)
    blocks = Column(Integer)
    turnovers = Column(Integer)
    threes_made = Column(Integer)
    threes_attempted = Column(Integer)

    # Soccer stats
    shots = Column(Integer)
    shots_on_target = Column(Integer)
    goals = Column(Integer)
    key_passes = Column(Integer)
    dribbles = Column(Integer)
    tackles = Column(Integer)

    # Tennis stats
    aces = Column(Integer)
    double_faults = Column(Integer)
    first_serve_pct = Column(Float)
    service_points_won = Column(Integer)
    break_points_saved = Column(Integer)

    # Metadata
    stats_json = Column(JSON)  # Additional stats
    created_at = Column(DateTime, default=datetime.utcnow)


class TeamStats(Base):
    """Team statistics history"""
    __tablename__ = 'team_stats'

    id = Column(Integer, primary_key=True)
    team_name = Column(String(200), nullable=False)
    sport = Column(String(50), nullable=False)
    league = Column(String(100), nullable=False)
    season = Column(String(20))
    game_date = Column(DateTime)
    opponent = Column(String(200))
    home_away = Column(String(10))

    # Soccer team stats
    corners = Column(Integer)
    shots = Column(Integer)
    shots_on_target = Column(Integer)
    possession = Column(Float)
    fouls = Column(Integer)
    yellow_cards = Column(Integer)
    red_cards = Column(Integer)
    offsides = Column(Integer)

    # Basketball team stats
    pace = Column(Float)
    offensive_rating = Column(Float)
    defensive_rating = Column(Float)

    # Metadata
    stats_json = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)


def get_engine(database_url: str = None):
    """Create database engine"""
    if database_url is None:
        database_url = os.getenv("DATABASE_URL", "sqlite:///data/results/sports_bot.db")

    return create_engine(database_url, echo=False)


def init_db(database_url: str = None):
    """Initialize database with all tables"""
    engine = get_engine(database_url)
    Base.metadata.create_all(engine)
    return engine


def get_session(engine=None):
    """Get database session"""
    if engine is None:
        engine = get_engine()

    Session = sessionmaker(bind=engine)
    return Session()
