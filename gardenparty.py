import streamlit as st
import sqlite3
import random
from datetime import datetime
from typing import List, Tuple, Optional
import json
import pandas as pd
from contextlib import contextmanager
import threading

# Page configuration
st.set_page_config(
    page_title="Garden Tic-Tac-Toe Auction",
    page_icon="🌸",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Constants
BOARD_SIZE = 5
WIN_LENGTH = 5
EMPTY = '.'
FLOWER = 'X'
BUTTERFLY = 'O'
BEE = 'B'
STARTING_COINS = 1000
MIN_BET = 10
MAX_BET = 500
AUCTION_INCREMENT = 5

# Thread-safe database connection pool
class DatabasePool:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance.local = threading.local()
        return cls._instance
    
    @contextmanager
    def get_connection(self):
        """Get thread-safe database connection"""
        if not hasattr(self.local, 'conn'):
            self.local.conn = sqlite3.connect('garden_tictactoe.db', 
                                             check_same_thread=False,
                                             timeout=30.0,
                                             isolation_level='DEFERRED')
            self.local.conn.execute('PRAGMA journal_mode=WAL')
            self.local.conn.execute('PRAGMA synchronous=NORMAL')
            self.local.conn.execute('PRAGMA cache_size=10000')
            self.local.conn.execute('PRAGMA temp_store=MEMORY')
        
        try:
            yield self.local.conn
        except Exception as e:
            self.local.conn.rollback()
            raise e

# Custom CSS with Charcoal/Black Board Theme
st.markdown("""
<style>
    .main {
        padding: 0.5rem;
        max-width: 600px;
        margin: 0 auto;
        background-color: #1a1a1a;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .game-header {
        background: linear-gradient(135deg, #2d2d2d 0%, #1a1a1a 100%);
        padding: 1.5rem;
        border-radius: 20px;
        text-align: center;
        color: #f5f5f5;
        margin-bottom: 1.5rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        border: 3px solid #333;
    }
    
    .game-title {
        font-size: 1.8rem;
        font-weight: bold;
        margin: 0;
        color: #f5f5f5;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
    }
    
    .game-subtitle {
        font-size: 0.9rem;
        opacity: 0.9;
        margin-top: 0.3rem;
        color: #cccccc;
    }
    
    .auction-card {
        background: linear-gradient(135deg, #333333 0%, #1a1a1a 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        margin-bottom: 1rem;
        box-shadow: 0 5px 20px rgba(0,0,0,0.4);
        border: 2px solid #444;
    }
    
    .coin-balance {
        font-size: 1.5rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 1rem;
        color: #FFD700;
    }
    
    .auction-display {
        background: rgba(50,50,50,0.5);
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border: 1px solid #555;
    }
    
    .game-board {
        background: #2b2b2b;
        padding: 1rem;
        border-radius: 15px;
        box-shadow: 0 5px 20px rgba(0,0,0,0.3);
        margin-bottom: 1rem;
        border: 3px solid #1a1a1a;
    }
    
    .stats-card {
        background: linear-gradient(135deg, #2d2d2d 0%, #1a1a1a 100%);
        padding: 1rem;
        border-radius: 15px;
        color: white;
        margin-bottom: 1rem;
        box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        border: 2px solid #333;
    }
    
    .info-card {
        background: linear-gradient(135deg, #333333 0%, #2d2d2d 100%);
        padding: 1rem;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 1rem;
        box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        border: 2px solid #444;
        color: #f5f5f5;
    }
    
    .auction-info {
        background: linear-gradient(135deg, #2d2d2d 0%, #1a1a1a 100%);
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        font-size: 0.9rem;
        border: 2px solid #444;
        color: #e0e0e0;
    }
    
    .winner-banner {
        background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
        padding: 2rem;
        border-radius: 20px;
        text-align: center;
        color: #1a1a1a;
        font-size: 1.5rem;
        font-weight: bold;
        animation: pulse 1s infinite;
        margin: 1rem 0;
        box-shadow: 0 10px 30px rgba(255,215,0,0.5);
        border: 3px solid #FFD700;
    }
    
    .win-amount {
        font-size: 2rem;
        color: #1a1a1a;
        text-shadow: 1px 1px 2px rgba(255,255,255,0.5);
        margin-top: 0.5rem;
    }
    
    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.05); }
    }
    
    /* Yellow Buttons for Players */
    div[data-testid="column"] > div > div > button {
        width: 100%;
        aspect-ratio: 1;
        font-size: 2.5rem;
        border-radius: 10px;
        border: 3px solid #1a1a1a;
        background: #FFD700 !important;
        color: #1a1a1a !important;
        transition: all 0.2s;
        min-height: 60px;
        font-weight: bold;
        box-shadow: 0 4px 8px rgba(0,0,0,0.3);
    }
    
    div[data-testid="column"] > div > div > button:hover {
        transform: scale(1.05);
        box-shadow: 0 6px 12px rgba(255,215,0,0.4);
        background: #FFA500 !important;
    }
    
    div[data-testid="column"] > div > div > button:disabled {
        background: #1a1a1a !important;
        color: #666 !important;
        opacity: 1 !important;
        border: 3px solid #333;
    }
    
    .auction-bid {
        background: #FFD700;
        color: #1a1a1a;
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        border: 3px solid #FFA500;
        box-shadow: 0 5px 15px rgba(255,215,0,0.3);
    }
    
    .current-bid {
        font-size: 2rem;
        font-weight: bold;
        text-align: center;
        color: #1a1a1a;
    }
    
    .stButton > button {
        background: #FFD700 !important;
        color: #1a1a1a !important;
        font-weight: bold !important;
        border: 2px solid #FFA500 !important;
    }
    
    .stButton > button:hover {
        background: #FFA500 !important;
        border-color: #FF8C00 !important;
    }
</style>
""", unsafe_allow_html=True)

# Database functions
def init_db():
    """Initialize SQLite database with auction betting tables"""
    db_pool = DatabasePool()
    with db_pool.get_connection() as conn:
        c = conn.cursor()
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS game_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                winner TEXT NOT NULL,
                difficulty TEXT NOT NULL,
                total_moves INTEGER NOT NULL,
                bee_interruptions INTEGER NOT NULL,
                bet_amount INTEGER DEFAULT 0,
                payout_amount INTEGER DEFAULT 0,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Migrate existing table to add auction columns
        try:
            c.execute("SELECT player_bid FROM game_stats LIMIT 1")
        except sqlite3.OperationalError:
            # Columns don't exist, add them
            try:
                c.execute("ALTER TABLE game_stats ADD COLUMN player_bid INTEGER DEFAULT 0")
            except sqlite3.OperationalError:
                pass
            try:
                c.execute("ALTER TABLE game_stats ADD COLUMN ai_bid INTEGER DEFAULT 0")
            except sqlite3.OperationalError:
                pass

def get_player_wallet():
    """Get player's current wallet balance"""
    db_pool = DatabasePool()
    with db_pool.get_connection() as conn:
        c = conn.cursor()
        c.execute('SELECT coins, total_wagered, total_won, games_played FROM player_wallet WHERE id = 1')
        result = c.fetchone()
        return {
            'coins': result[0],
            'total_wagered': result[1],
            'total_won': result[2],
            'games_played': result[3]
        }

def update_player_wallet(coin_change, wagered=0, won=0):
    """Update player's wallet after a game"""
    db_pool = DatabasePool()
    with db_pool.get_connection() as conn:
        c = conn.cursor()
        c.execute('''
            UPDATE player_wallet 
            SET coins = coins + ?,
                total_wagered = total_wagered + ?,
                total_won = total_won + ?,
                games_played = games_played + 1
            WHERE id = 1
        ''', (coin_change, wagered, won))
        conn.commit()

def save_game_result(winner, difficulty, total_moves, bee_interruptions, player_bid, ai_bid, bee_bid, payout, move_history):
    """Save game result with auction betting information"""
    db_pool = DatabasePool()
    with db_pool.get_connection() as conn:
        c = conn.cursor()
        c.execute('BEGIN TRANSACTION')
        try:
            c.execute('''
                INSERT INTO game_stats (winner, difficulty, total_moves, bee_interruptions, 
                                       player_bid, ai_bid, bee_bid, payout_amount)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (winner, difficulty, total_moves, bee_interruptions, player_bid, ai_bid, bee_bid, payout))
            c.execute('COMMIT')
        except Exception as e:
            c.execute('ROLLBACK')
            raise e

@st.cache_data(ttl=60)
def get_statistics():
    """Get game statistics with auction info"""
    db_pool = DatabasePool()
    with db_pool.get_connection() as conn:
        c = conn.cursor()
        c.execute('''
            SELECT 
                SUM(CASE WHEN winner = 'Flowers' THEN 1 ELSE 0 END) as flower_wins,
                SUM(CASE WHEN winner = 'Butterflies' THEN 1 ELSE 0 END) as butterfly_wins,
                SUM(CASE WHEN winner = 'Draw' THEN 1 ELSE 0 END) as draws,
                AVG(total_moves) as avg_moves,
                SUM(bee_interruptions) as total_bees,
                AVG(player_bid) as avg_player_bid,
                AVG(ai_bid) as avg_ai_bid,
                SUM(payout_amount) as total_payout
            FROM game_stats
        ''')
        result = c.fetchone()
        return {
            'flower_wins': result[0] or 0,
            'butterfly_wins': result[1] or 0,
            'draws': result[2] or 0,
            'avg_moves': result[3] or 0,
            'total_bees': result[4] or 0,
            'avg_player_bid': result[5] or 0,
            'avg_ai_bid': result[6] or 0,
            'total_payout': result[7] or 0
        }

# Game logic classes
class Move:
    __slots__ = ['row', 'col', 'score']
    
    def __init__(self, row=-1, col=-1, score=0):
        self.row = row
        self.col = col
        self.score = score

class GardenTicTacToe:
    def __init__(self, difficulty='Medium'):
        self.board = [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.difficulty = difficulty
        self.move_count = 0
        self.bee_interruptions = 0
        self.move_history = []
        self._lines_cache = None
        
    def is_valid_move(self, row, col):
        return 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE and self.board[row][col] == EMPTY
    
    def make_move(self, row, col, player):
        if not self.is_valid_move(row, col):
            return False
        self.board[row][col] = player
        self.move_count += 1
        self.move_history.append((player, row, col))
        return True
    
    def get_all_lines(self):
        if self._lines_cache is None:
            lines = []
            for i in range(BOARD_SIZE):
                lines.append([(i, j) for j in range(BOARD_SIZE)])
            for j in range(BOARD_SIZE):
                lines.append([(i, j) for i in range(BOARD_SIZE)])
            lines.append([(i, i) for i in range(BOARD_SIZE)])
            lines.append([(i, BOARD_SIZE-1-i) for i in range(BOARD_SIZE)])
            self._lines_cache = lines
        return self._lines_cache
    
    def evaluate_line(self, line, player, opponent):
        player_count = sum(1 for r, c in line if self.board[r][c] == player)
        opp_count = sum(1 for r, c in line if self.board[r][c] == opponent)
        empty_count = sum(1 for r, c in line if self.board[r][c] == EMPTY)
        bee_count = sum(1 for r, c in line if self.board[r][c] == BEE)
        
        if (player_count > 0 and opp_count > 0) or bee_count > 0:
            return 0
        
        if player_count == 5: return 100000
        if opp_count == 5: return -100000
        if player_count == 4 and empty_count == 1: return 10000
        if opp_count == 4 and empty_count == 1: return -10000
        if player_count == 3 and empty_count == 2: return 1000
        if opp_count == 3 and empty_count == 2: return -1000
        if player_count == 2 and empty_count == 3: return 100
        if opp_count == 2 and empty_count == 3: return -100
        if player_count == 1 and empty_count == 4: return 10
        
        return 0
    
    def evaluate_board(self, player, opponent):
        total_score = 0
        for line in self.get_all_lines():
            total_score += self.evaluate_line(line, player, opponent)
        return total_score
    
    def get_positional_bonus(self, row, col):
        if row == 2 and col == 2: return 50
        if abs(row - 2) <= 1 and abs(col - 2) <= 1: return 30
        if (row == 0 or row == 4) and (col == 0 or col == 4): return 20
        return 0
    
    def find_immediate_win(self, player):
        for i in range(BOARD_SIZE):
            for j in range(BOARD_SIZE):
                if self.board[i][j] == EMPTY:
                    self.board[i][j] = player
                    if self.check_win(player):
                        self.board[i][j] = EMPTY
                        return Move(i, j, 100000)
                    self.board[i][j] = EMPTY
        return Move()
    
    def count_winning_threats(self, player):
        threats = 0
        for line in self.get_all_lines():
            player_count = sum(1 for r, c in line if self.board[r][c] == player)
            empty_count = sum(1 for r, c in line if self.board[r][c] == EMPTY)
            if player_count == 4 and empty_count == 1:
                threats += 1
        return threats
    
    def find_fork_moves(self, player):
        fork_moves = []
        for i in range(BOARD_SIZE):
            for j in range(BOARD_SIZE):
                if self.board[i][j] == EMPTY:
                    self.board[i][j] = player
                    threats = self.count_winning_threats(player)
                    if threats >= 2:
                        fork_moves.append(Move(i, j, threats * 1000))
                    self.board[i][j] = EMPTY
        return sorted(fork_moves, key=lambda x: x.score, reverse=True)
    
    def get_ai_move(self, ai_player, human_player):
        win_move = self.find_immediate_win(ai_player)
        if win_move.row != -1:
            return win_move, "🎯 AI found winning move!"
        
        block_move = self.find_immediate_win(human_player)
        if block_move.row != -1:
            return block_move, "🛡️ AI blocking your winning move!"
        
        if self.difficulty in ['Medium', 'Hard']:
            fork_moves = self.find_fork_moves(ai_player)
            if fork_moves:
                return fork_moves[0], "🔱 AI creating a fork!"
            
            opp_forks = self.find_fork_moves(human_player)
            if opp_forks:
                return opp_forks[0], "🚫 AI blocking your fork!"
        
        best_score = float('-inf')
        best_move = Move()
        
        for i in range(BOARD_SIZE):
            for j in range(BOARD_SIZE):
                if self.board[i][j] == EMPTY:
                    self.board[i][j] = ai_player
                    score = self.evaluate_board(ai_player, human_player) + self.get_positional_bonus(i, j)
                    self.board[i][j] = EMPTY
                    
                    if score > best_score:
                        best_score = score
                        best_move = Move(i, j, score)
        
        return best_move, "🤖 AI is thinking..."
    
    def should_bee_interrupt(self):
        if self.move_count <= 4:
            return False
        
        bee_chance = {
            'Easy': 0.10,
            'Medium': 0.20,
            'Hard': 0.25
        }.get(self.difficulty, 0.15)
        
        return random.random() < bee_chance
    
    def get_strategic_bee_move(self, target_player):
        best_score = float('-inf')
        best_move = Move()
        
        for i in range(BOARD_SIZE):
            for j in range(BOARD_SIZE):
                if self.board[i][j] == EMPTY:
                    self.board[i][j] = target_player
                    disruption_score = 0
                    if self.check_win(target_player):
                        disruption_score = 10000
                    self.board[i][j] = EMPTY
                    
                    if disruption_score > best_score:
                        best_score = disruption_score
                        best_move = Move(i, j, disruption_score)
        
        if best_move.row == -1:
            empty_spaces = [(i, j) for i in range(BOARD_SIZE) for j in range(BOARD_SIZE) 
                          if self.board[i][j] == EMPTY]
            if empty_spaces:
                r, c = random.choice(empty_spaces)
                best_move = Move(r, c)
        
        return best_move
    
    def check_win(self, player):
        for line in self.get_all_lines():
            if all(self.board[r][c] == player for r, c in line):
                return True
        return False
    
    def is_board_full(self):
        return all(self.board[i][j] != EMPTY for i in range(BOARD_SIZE) for j in range(BOARD_SIZE))

# Initialize database
init_db()

# Initialize session state
def init_session_state():
    defaults = {
        'game': None,
        'current_player': FLOWER,
        'game_over': False,
        'winner': None,
        'player_is_flower': True,
        'ai_message': "",
        'show_stats': False,
        'difficulty': 'Medium',
        'player_first': 'You (🌺 Flowers)',
        'processing_move': False,
        'auction_phase': 'bidding',
        'player_bid': MIN_BET,
        'ai_bid': 0,
        'bee_bid': 0,
        'auction_complete': False,
        'total_pot': 0,
        'payout_amount': 0
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

def calculate_ai_bid(difficulty, player_bid):
    """AI determines its bid based on difficulty"""
    base_bid = {
        'Easy': int(player_bid * 0.6),
        'Medium': int(player_bid * 0.9),
        'Hard': int(player_bid * 1.2)
    }.get(difficulty, player_bid)
    
    # Add some randomness
    variation = random.randint(-10, 20)
    return max(MIN_BET, base_bid + variation)

def calculate_bee_bid():
    """Bees always bid a random amount"""
    return random.randint(MIN_BET, MIN_BET + 30)

def calculate_auction_payout(winner, player_bid, ai_bid, bee_bid, bee_interruptions):
    """Calculate payout based on auction winner-takes-all"""
    total_pot = player_bid + ai_bid + bee_bid
    
    if winner == 'Flowers':  # Player wins
        # Player gets the total pot minus their own bid (net gain)
        payout = total_pot
        return payout, total_pot
    
    elif winner == 'Butterflies':  # AI wins
        # Player loses their bid
        return 0, total_pot
    
    elif winner == 'Bees':  # Bees win (board full due to bees)
        # Bees take all, everyone loses
        return 0, total_pot
    
    else:  # Draw
        # Everyone gets their bid back
        return player_bid, total_pot

def reset_game():
    """Reset game"""
    difficulty = st.session_state.difficulty
    st.session_state.game = GardenTicTacToe(difficulty)
    st.session_state.current_player = FLOWER
    st.session_state.game_over = False
    st.session_state.winner = None
    st.session_state.ai_message = ""
    st.session_state.processing_move = False
    st.session_state.auction_phase = 'bidding'
    st.session_state.auction_complete = False
    st.session_state.player_bid = MIN_BET
    st.session_state.ai_bid = 0
    st.session_state.bee_bid = 0
    st.session_state.total_pot = 0
    st.session_state.payout_amount = 0

def get_cell_display(cell):
    if cell == FLOWER:
        return "🌺"
    elif cell == BUTTERFLY:
        return "🦋"
    elif cell == BEE:
        return "🐝"
    return "·"

def check_game_over():
    """Check game over and calculate auction payouts"""
    game = st.session_state.game
    
    if game.check_win(FLOWER):
        st.session_state.game_over = True
        st.session_state.winner = 'Flowers'
        payout, pot = calculate_auction_payout('Flowers', st.session_state.player_bid, 
                                               st.session_state.ai_bid, st.session_state.bee_bid,
                                               game.bee_interruptions)
        st.session_state.payout_amount = payout
        st.session_state.total_pot = pot
        coin_change = payout - st.session_state.player_bid
        update_player_wallet(coin_change, st.session_state.player_bid, payout)
        save_game_result('Flowers', game.difficulty, game.move_count, 
                        game.bee_interruptions, st.session_state.player_bid,
                        st.session_state.ai_bid, st.session_state.bee_bid,
                        payout, game.move_history)
        return True
    
    if game.check_win(BUTTERFLY):
        st.session_state.game_over = True
        st.session_state.winner = 'Butterflies'
        payout, pot = calculate_auction_payout('Butterflies', st.session_state.player_bid,
                                               st.session_state.ai_bid, st.session_state.bee_bid,
                                               game.bee_interruptions)
        st.session_state.payout_amount = payout
        st.session_state.total_pot = pot
        coin_change = payout - st.session_state.player_bid
        update_player_wallet(coin_change, st.session_state.player_bid, payout)
        save_game_result('Butterflies', game.difficulty, game.move_count,
                        game.bee_interruptions, st.session_state.player_bid,
                        st.session_state.ai_bid, st.session_state.bee_bid,
                        payout, game.move_history)
        return True
    
    if game.is_board_full():
        # Check if it's mostly bees that caused the draw
        bee_count = sum(1 for i in range(BOARD_SIZE) for j in range(BOARD_SIZE) 
                       if game.board[i][j] == BEE)
        
        if bee_count >= 5:  # Bees significantly disrupted
            st.session_state.game_over = True
            st.session_state.winner = 'Bees'
            payout, pot = calculate_auction_payout('Bees', st.session_state.player_bid,
                                                   st.session_state.ai_bid, st.session_state.bee_bid,
                                                   game.bee_interruptions)
        else:
            st.session_state.game_over = True
            st.session_state.winner = 'Draw'
            payout, pot = calculate_auction_payout('Draw', st.session_state.player_bid,
                                                   st.session_state.ai_bid, st.session_state.bee_bid,
                                                   game.bee_interruptions)
        
        st.session_state.payout_amount = payout
        st.session_state.total_pot = pot
        coin_change = payout - st.session_state.player_bid
        update_player_wallet(coin_change, st.session_state.player_bid, payout)
        save_game_result(st.session_state.winner, game.difficulty, game.move_count,
                        game.bee_interruptions, st.session_state.player_bid,
                        st.session_state.ai_bid, st.session_state.bee_bid,
                        payout, game.move_history)
        return True
    
    return False

def handle_cell_click(row, col):
    """Handle cell click"""
    if st.session_state.processing_move or not st.session_state.auction_complete:
        return
    
    st.session_state.processing_move = True
    game = st.session_state.game
    
    if st.session_state.game_over:
        st.session_state.processing_move = False
        return
    
    is_player_turn = (st.session_state.current_player == FLOWER and st.session_state.player_is_flower) or \
                     (st.session_state.current_player == BUTTERFLY and not st.session_state.player_is_flower)
    
    if not is_player_turn:
        st.session_state.processing_move = False
        return
    
    if not game.make_move(row, col, st.session_state.current_player):
        st.session_state.processing_move = False
        return
    
    if check_game_over():
        st.session_state.processing_move = False
        return
    
    if game.should_bee_interrupt():
        target_player = BUTTERFLY if st.session_state.player_is_flower else FLOWER
        bee_move = game.get_strategic_bee_move(target_player)
        if bee_move.row != -1:
            game.make_move(bee_move.row, bee_move.col, BEE)
            game.bee_interruptions += 1
            st.session_state.ai_message = f"🐝 BUZZ! Bee placed at ({bee_move.row}, {bee_move.col})"
            if check_game_over():
                st.session_state.processing_move = False
                return
    else:
        st.session_state.current_player = BUTTERFLY if st.session_state.current_player == FLOWER else FLOWER
        
        ai_player = st.session_state.current_player
        human_player = FLOWER if st.session_state.player_is_flower else BUTTERFLY
        ai_move, message = game.get_ai_move(ai_player, human_player)
        
        if ai_move.row != -1:
            game.make_move(ai_move.row, ai_move.col, ai_player)
            st.session_state.ai_message = message
            
            if check_game_over():
                st.session_state.processing_move = False
                return
            
            st.session_state.current_player = BUTTERFLY if st.session_state.current_player == FLOWER else FLOWER
    
    st.session_state.processing_move = False

# Main UI
st.markdown("""
<div class="game-header">
    <div class="game-title">🌸 Garden Auction Tic-Tac-Toe 🦋</div>
    <div class="game-subtitle">5×5 Board • AI Opponent • Bee Chaos • Auction Betting!</div>
</div>
""", unsafe_allow_html=True)

# Wallet display
wallet = get_player_wallet()

st.markdown(f"""
<div class="auction-card">
    <div class="coin-balance">💰 Balance: {wallet['coins']} coins</div>
    <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 0.5rem; text-align: center;">
        <div>
            <div style="font-size: 0.8rem; opacity: 0.8;">Games Played</div>
            <div style="font-size: 1.2rem; font-weight: bold;">{wallet['games_played']}</div>
        </div>
        <div>
            <div style="font-size: 0.8rem; opacity: 0.8;">Total Wagered</div>
            <div style="font-size: 1.2rem; font-weight: bold;">{wallet['total_wagered']}</div>
        </div>
        <div>
            <div style="font-size: 0.8rem; opacity: 0.8;">Total Won</div>
            <div style="font-size: 1.2rem; font-weight: bold;">{wallet['total_won']}</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Auction Bidding Phase
if not st.session_state.auction_complete and not st.session_state.game_over:
    st.markdown("""
    <div class="auction-info">
        <h4 style="margin-top: 0;">🏆 Auction Rules: Winner Takes All!</h4>
        <ul style="margin: 0.5rem 0;">
            <li><b>🌺 Player</b>, <b>🦋 AI</b>, and <b>🐝 Bees</b> each place bids</li>
            <li><b>Winner</b> takes the entire pot (all three bids combined)</li>
            <li><b>Loser</b> loses their entire bid</li>
            <li><b>Draw</b>: Everyone gets their bid back</li>
            <li><b>Bee Victory</b>: If bees disrupt too much (5+ bee placements), bees win the pot!</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 🎲 Place Your Auction Bid")
    
    max_bid_allowed = min(MAX_BET, wallet['coins'])
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.selectbox(
            "Difficulty",
            ['Easy', 'Medium', 'Hard'],
            index=1,
            key='difficulty'
        )
    
    with col2:
        st.radio(
            "Who starts?",
            ['You (🌺 Flowers)', 'AI (🦋 Butterflies)'],
            index=0,
            key='player_first'
        )
    
    player_bid = st.slider(
        "Your Bid (coins)",
        min_value=MIN_BET,
        max_value=max_bid_allowed,
        value=min(50, max_bid_allowed),
        step=AUCTION_INCREMENT,
        key='bid_slider'
    )
    
    if st.button("🎮 Place Bid & Start Auction", use_container_width=True, type="primary"):
        if wallet['coins'] >= player_bid:
            st.session_state.player_bid = player_bid
            st.session_state.ai_bid = calculate_ai_bid(st.session_state.difficulty, player_bid)
            st.session_state.bee_bid = calculate_bee_bid()
            st.session_state.total_pot = st.session_state.player_bid + st.session_state.ai_bid + st.session_state.bee_bid
            st.session_state.auction_complete = True
            st.session_state.game = GardenTicTacToe(st.session_state.difficulty)
            
            if st.session_state.player_first == 'AI (🦋 Butterflies)':
                st.session_state.player_is_flower = False
                st.session_state.current_player = BUTTERFLY
            else:
                st.session_state.player_is_flower = True
                st.session_state.current_player = FLOWER
            
            st.rerun()
        else:
            st.error("❌ Insufficient coins!")

# Show auction results after bidding
elif st.session_state.auction_complete and not st.session_state.game_over:
    st.markdown(f"""
    <div class="auction-bid">
        <h3 style="margin-top: 0; text-align: center;">🎰 Auction Complete!</h3>
        <div class="current-bid">Total Pot: {st.session_state.total_pot} coins</div>
        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1rem; margin-top: 1rem;">
            <div style="text-align: center; background: rgba(0,0,0,0.2); padding: 1rem; border-radius: 10px;">
                <div style="font-size: 1.5rem;">🌺</div>
                <div style="font-weight: bold;">You</div>
                <div style="font-size: 1.2rem;">{st.session_state.player_bid} coins</div>
            </div>
            <div style="text-align: center; background: rgba(0,0,0,0.2); padding: 1rem; border-radius: 10px;">
                <div style="font-size: 1.5rem;">🦋</div>
                <div style="font-weight: bold;">AI</div>
                <div style="font-size: 1.2rem;">{st.session_state.ai_bid} coins</div>
            </div>
            <div style="text-align: center; background: rgba(0,0,0,0.2); padding: 1rem; border-radius: 10px;">
                <div style="font-size: 1.5rem;">🐝</div>
                <div style="font-weight: bold;">Bees</div>
                <div style="font-size: 1.2rem;">{st.session_state.bee_bid} coins</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Game board
if st.session_state.auction_complete:
    game = st.session_state.game
    
    if st.session_state.ai_message:
        st.info(st.session_state.ai_message)
    
    st.markdown('<div class="game-board">', unsafe_allow_html=True)
    
    for i in range(BOARD_SIZE):
        cols = st.columns(BOARD_SIZE)
        for j in range(BOARD_SIZE):
            with cols[j]:
                cell = game.board[i][j]
                display = get_cell_display(cell)
                
                if st.button(
                    display,
                    key=f"cell_{i}_{j}",
                    disabled=st.session_state.game_over or cell != EMPTY or st.session_state.processing_move,
                    use_container_width=True
                ):
                    handle_cell_click(i, j)
                    st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Game info
    if not st.session_state.game_over:
        turn_display = "🌺 Your Turn" if (st.session_state.current_player == FLOWER and st.session_state.player_is_flower) or \
                                         (st.session_state.current_player == BUTTERFLY and not st.session_state.player_is_flower) else "🦋 AI's Turn"
        
        st.markdown(f"""
        <div class="info-card">
            <h3 style="margin: 0;">{turn_display}</h3>
            <p style="margin: 0.5rem 0 0 0;">Moves: {game.move_count} | Bee Interruptions: 🐝 {game.bee_interruptions}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Winner display
    if st.session_state.game_over:
        winner_emoji = {
            'Flowers': '🌺',
            'Butterflies': '🦋',
            'Bees': '🐝',
            'Draw': '🤝'
        }.get(st.session_state.winner, '🎮')
        
        winner_text = {
            'Flowers': 'YOU WIN!',
            'Butterflies': 'AI WINS!',
            'Bees': 'BEES WIN!',
            'Draw': "IT'S A DRAW!"
        }.get(st.session_state.winner, 'GAME OVER')
        
        st.markdown(f"""
        <div class="winner-banner">
            <div style="font-size: 3rem;">{winner_emoji}</div>
            <div>{winner_text}</div>
            <div class="win-amount">
                Pot: {st.session_state.total_pot} coins<br>
                You get: {st.session_state.payout_amount} coins
            </div>
            <div style="font-size: 0.9rem; margin-top: 1rem;">
                Net: {'+' if st.session_state.payout_amount - st.session_state.player_bid >= 0 else ''}{st.session_state.payout_amount - st.session_state.player_bid} coins
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Play Again", use_container_width=True):
                reset_game()
                st.rerun()
        
        with col2:
            if st.button("📊 View Statistics", use_container_width=True):
                st.session_state.show_stats = not st.session_state.show_stats

# Statistics
if st.session_state.show_stats:
    stats = get_statistics()
    
    st.markdown(f"""
    <div class="stats-card">
        <h3 style="margin-top: 0;">📊 Game Statistics</h3>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
            <div>
                <p><b>🌺 Player Wins:</b> {stats['flower_wins']}</p>
                <p><b>🦋 AI Wins:</b> {stats['butterfly_wins']}</p>
                <p><b>🤝 Draws:</b> {stats['draws']}</p>
            </div>
            <div>
                <p><b>📈 Avg Moves:</b> {stats['avg_moves']:.1f}</p>
                <p><b>🐝 Total Bees:</b> {stats['total_bees']}</p>
                <p><b>💰 Total Payout:</b> {stats['total_payout']}</p>
            </div>
        </div>
        <div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid rgba(255,255,255,0.2);">
            <p><b>💵 Avg Player Bid:</b> {stats['avg_player_bid']:.0f} coins</p>
            <p><b>🤖 Avg AI Bid:</b> {stats['avg_ai_bid']:.0f} coins</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
