import streamlit as st
import sqlite3
import random
from datetime import datetime
from typing import List, Tuple, Optional
import json
import pandas as pd

# Page configuration
st.set_page_config(
    page_title="Garden Tic-Tac-Toe",
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

# Custom CSS for mobile-friendly design
st.markdown("""
<style>
    /* Main container */
    .main {
        padding: 0.5rem;
        max-width: 600px;
        margin: 0 auto;
    }
    
    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Custom header */
    .game-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 20px;
        text-align: center;
        color: white;
        margin-bottom: 1.5rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }
    
    .game-title {
        font-size: 1.8rem;
        font-weight: bold;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .game-subtitle {
        font-size: 0.9rem;
        opacity: 0.9;
        margin-top: 0.3rem;
    }
    
    /* Game board */
    .game-board {
        background: white;
        padding: 1rem;
        border-radius: 15px;
        box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    
    /* Stats card */
    .stats-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 1rem;
        border-radius: 15px;
        color: white;
        margin-bottom: 1rem;
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    }
    
    .stat-item {
        display: flex;
        justify-content: space-between;
        padding: 0.5rem 0;
        border-bottom: 1px solid rgba(255,255,255,0.2);
    }
    
    .stat-item:last-child {
        border-bottom: none;
    }
    
    /* Info card */
    .info-card {
        background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%);
        padding: 1rem;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 1rem;
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    }
    
    /* Button styling */
    .stButton > button {
        width: 100%;
        border-radius: 10px;
        height: 3rem;
        font-weight: bold;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
        transition: transform 0.2s;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 15px rgba(0,0,0,0.3);
    }
    
    /* Cell button styling */
    div[data-testid="column"] > div > div > button {
        width: 100%;
        aspect-ratio: 1;
        font-size: 2.5rem;
        border-radius: 10px;
        border: 2px solid #555;
        background: #2b2b2b !important;
        color: white !important;
        transition: all 0.2s;
        min-height: 60px;
    }
    
    div[data-testid="column"] > div > div > button:hover {
        transform: scale(1.05);
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
        background: #3a3a3a !important;
    }
    
    div[data-testid="column"] > div > div > button:disabled {
        background: #1a1a1a !important;
        opacity: 1 !important;
    }
    
    /* Winner animation */
    .winner-banner {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 2rem;
        border-radius: 20px;
        text-align: center;
        color: white;
        font-size: 1.5rem;
        font-weight: bold;
        animation: pulse 1s infinite;
        margin: 1rem 0;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    }
    
    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.05); }
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .game-title {
            font-size: 1.5rem;
        }
        
        div[data-testid="column"] > div > div > button {
            font-size: 1.5rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# Database functions
def init_db():
    """Initialize SQLite database"""
    conn = sqlite3.connect('garden_tictactoe.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS game_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            winner TEXT,
            difficulty TEXT,
            total_moves INTEGER,
            bee_interruptions INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS game_moves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id INTEGER,
            move_number INTEGER,
            player TEXT,
            row INTEGER,
            col INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (game_id) REFERENCES game_stats(id)
        )
    ''')
    conn.commit()
    return conn

def save_game_result(conn, winner, difficulty, total_moves, bee_interruptions, move_history):
    """Save game result and move history to database"""
    c = conn.cursor()
    c.execute('''
        INSERT INTO game_stats (winner, difficulty, total_moves, bee_interruptions)
        VALUES (?, ?, ?, ?)
    ''', (winner, difficulty, total_moves, bee_interruptions))
    game_id = c.lastrowid
    
    for move_num, (player, row, col) in enumerate(move_history, 1):
        c.execute('''
            INSERT INTO game_moves (game_id, move_number, player, row, col)
            VALUES (?, ?, ?, ?, ?)
        ''', (game_id, move_num, player, row, col))
    
    conn.commit()

def get_statistics(conn):
    """Get game statistics from database"""
    c = conn.cursor()
    c.execute('SELECT winner, COUNT(*) FROM game_stats GROUP BY winner')
    wins = dict(c.fetchall())
    
    c.execute('SELECT AVG(total_moves) FROM game_stats')
    avg_moves = c.fetchone()[0] or 0
    
    c.execute('SELECT SUM(bee_interruptions) FROM game_stats')
    total_bees = c.fetchone()[0] or 0
    
    return {
        'flower_wins': wins.get('Flowers', 0),
        'butterfly_wins': wins.get('Butterflies', 0),
        'draws': wins.get('Draw', 0),
        'avg_moves': avg_moves,
        'total_bees': total_bees
    }

# Game logic classes
class Move:
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
        lines = []
        # Rows
        for i in range(BOARD_SIZE):
            lines.append([(i, j) for j in range(BOARD_SIZE)])
        # Columns
        for j in range(BOARD_SIZE):
            lines.append([(i, j) for i in range(BOARD_SIZE)])
        # Diagonals
        lines.append([(i, i) for i in range(BOARD_SIZE)])
        lines.append([(i, BOARD_SIZE-1-i) for i in range(BOARD_SIZE)])
        return lines
    
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
        # Win immediately
        win_move = self.find_immediate_win(ai_player)
        if win_move.row != -1:
            return win_move, "🎯 AI found winning move!"
        
        # Block opponent
        block_move = self.find_immediate_win(human_player)
        if block_move.row != -1:
            return block_move, "🛡️ AI blocking your winning move!"
        
        if self.difficulty in ['Medium', 'Hard']:
            # Create fork
            fork_moves = self.find_fork_moves(ai_player)
            if fork_moves:
                return fork_moves[0], "🔱 AI creating a fork!"
            
            # Block opponent's fork
            opp_forks = self.find_fork_moves(human_player)
            if opp_forks:
                return opp_forks[0], "🚫 AI blocking your fork!"
        
        # Strategic positioning
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

# Initialize session state
if 'db_conn' not in st.session_state:
    st.session_state.db_conn = init_db()

if 'game' not in st.session_state:
    st.session_state.game = None
    st.session_state.current_player = FLOWER
    st.session_state.game_over = False
    st.session_state.winner = None
    st.session_state.player_is_flower = True
    st.session_state.ai_message = ""
    st.session_state.show_stats = False
    st.session_state.show_moves = False

def reset_game():
    difficulty = st.session_state.get('difficulty', 'Medium')
    st.session_state.game = GardenTicTacToe(difficulty)
    st.session_state.current_player = FLOWER
    st.session_state.game_over = False
    st.session_state.winner = None
    st.session_state.ai_message = ""

def get_cell_display(cell):
    if cell == FLOWER:
        return "🌺"
    elif cell == BUTTERFLY:
        return "🦋"
    elif cell == BEE:
        return "🐝"
    return "·"

def check_game_over():
    game = st.session_state.game
    
    if game.check_win(FLOWER):
        st.session_state.game_over = True
        st.session_state.winner = 'Flowers'
        save_game_result(st.session_state.db_conn, 'Flowers', game.difficulty, 
                        game.move_count, game.bee_interruptions, game.move_history)
        return True
    
    if game.check_win(BUTTERFLY):
        st.session_state.game_over = True
        st.session_state.winner = 'Butterflies'
        save_game_result(st.session_state.db_conn, 'Butterflies', game.difficulty,
                        game.move_count, game.bee_interruptions, game.move_history)
        return True
    
    if game.is_board_full():
        st.session_state.game_over = True
        st.session_state.winner = 'Draw'
        save_game_result(st.session_state.db_conn, 'Draw', game.difficulty,
                        game.move_count, game.bee_interruptions, game.move_history)
        return True
    
    return False

def handle_cell_click(row, col):
    game = st.session_state.game
    
    if st.session_state.game_over:
        return
    
    # Player's turn
    is_player_turn = (st.session_state.current_player == FLOWER and st.session_state.player_is_flower) or \
                     (st.session_state.current_player == BUTTERFLY and not st.session_state.player_is_flower)
    
    if not is_player_turn:
        return
    
    if not game.make_move(row, col, st.session_state.current_player):
        return
    
    if check_game_over():
        return
    
    # Check for bee interruption
    if game.should_bee_interrupt():
        target_player = BUTTERFLY if st.session_state.player_is_flower else FLOWER
        bee_move = game.get_strategic_bee_move(target_player)
        if bee_move.row != -1:
            game.make_move(bee_move.row, bee_move.col, BEE)
            game.bee_interruptions += 1
            st.session_state.ai_message = f"🐝 BUZZ! Bee placed at ({bee_move.row}, {bee_move.col})"
            if check_game_over():
                return
    else:
        # Switch player for AI turn
        st.session_state.current_player = BUTTERFLY if st.session_state.current_player == FLOWER else FLOWER
        
        # AI's turn
        ai_player = st.session_state.current_player
        human_player = FLOWER if st.session_state.player_is_flower else BUTTERFLY
        ai_move, message = game.get_ai_move(ai_player, human_player)
        
        if ai_move.row != -1:
            game.make_move(ai_move.row, ai_move.col, ai_player)
            st.session_state.ai_message = message
            
            if check_game_over():
                return
            
            # Switch back to player
            st.session_state.current_player = BUTTERFLY if st.session_state.current_player == FLOWER else FLOWER

# Main UI
st.markdown("""
<div class="game-header">
    <div class="game-title">🌸 Garden Party Tic-Tac-Toe 🦋</div>
    <div class="game-subtitle">5×5 Board • AI Opponent • Bee Surprises!</div>
</div>
""", unsafe_allow_html=True)

# Sidebar for settings
with st.sidebar:
    st.title("⚙️ Settings")
    
    difficulty = st.selectbox(
        "Difficulty Level",
        ['Easy', 'Medium', 'Hard'],
        index=1,
        key='difficulty'
    )
    
    player_first = st.radio(
        "Who starts?",
        ['You (🌺 Flowers)', 'AI (🦋 Butterflies)'],
        index=0
    )
    st.session_state.player_is_flower = (player_first == 'You (🌺 Flowers)')
    
    if st.button("🎮 New Game", use_container_width=True):
        reset_game()
        st.rerun()
    
    st.divider()
    
    if st.button("📊 View Statistics", use_container_width=True):
        st.session_state.show_stats = not st.session_state.show_stats
    
    if st.button("📜 View Move History", use_container_width=True):
        st.session_state.show_moves = not st.session_state.show_moves

# Initialize game if needed
if st.session_state.game is None:
    reset_game()

# Display statistics
if st.session_state.show_stats:
    stats = get_statistics(st.session_state.db_conn)
    st.markdown("""
    <div class="stats-card">
        <h3 style="margin-top:0; text-align:center;">📊 Game Statistics</h3>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🌺 Flower Wins", stats['flower_wins'])
    with col2:
        st.metric("🦋 Butterfly Wins", stats['butterfly_wins'])
    with col3:
        st.metric("🤝 Draws", stats['draws'])
    
    col4, col5 = st.columns(2)
    with col4:
        st.metric("📊 Avg Moves", f"{stats['avg_moves']:.1f}")
    with col5:
        st.metric("🐝 Total Bees", stats['total_bees'])
    
    st.divider()

# Display move history
if st.session_state.show_moves and st.session_state.game:
    st.markdown("""
    <div class="stats-card">
        <h3 style="margin-top:0; text-align:center;">📜 Current Game Moves</h3>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.game.move_history:
        move_data = []
        for idx, (player, row, col) in enumerate(st.session_state.game.move_history, 1):
            player_icon = "🌺" if player == FLOWER else ("🦋" if player == BUTTERFLY else "🐝")
            player_name = "Flowers" if player == FLOWER else ("Butterflies" if player == BUTTERFLY else "Bee")
            move_data.append({
                "Move #": idx,
                "Player": f"{player_icon} {player_name}",
                "Position": f"({row}, {col})"
            })
        
        df = pd.DataFrame(move_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No moves yet. Start playing!")
    
    st.divider()

# Game info
if not st.session_state.game_over:
    current_symbol = "🌺" if st.session_state.current_player == FLOWER else "🦋"
    current_name = "Flowers" if st.session_state.current_player == FLOWER else "Butterflies"
    
    is_player_turn = (st.session_state.current_player == FLOWER and st.session_state.player_is_flower) or \
                     (st.session_state.current_player == BUTTERFLY and not st.session_state.player_is_flower)
    
    turn_text = "Your Turn" if is_player_turn else "AI's Turn"
    
    st.markdown(f"""
    <div class="info-card">
        <h3 style="margin:0;">{current_symbol} {turn_text} - {current_name}</h3>
        <p style="margin:0.5rem 0 0 0; font-size:0.9rem;">Move {st.session_state.game.move_count} • Difficulty: {st.session_state.game.difficulty}</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.ai_message:
        st.info(st.session_state.ai_message)

# Winner banner
if st.session_state.game_over and st.session_state.winner:
    if st.session_state.winner == 'Draw':
        st.markdown("""
        <div class="winner-banner">
            🤝 It's a DRAW! The garden is full!
        </div>
        """, unsafe_allow_html=True)
    else:
        symbol = "🌺" if st.session_state.winner == 'Flowers' else "🦋"
        st.markdown(f"""
        <div class="winner-banner">
            🎉 {symbol} {st.session_state.winner.upper()} WIN! {symbol}
        </div>
        """, unsafe_allow_html=True)

# Game board
st.markdown('<div class="game-board">', unsafe_allow_html=True)

game = st.session_state.game
for i in range(BOARD_SIZE):
    cols = st.columns(BOARD_SIZE)
    for j in range(BOARD_SIZE):
        with cols[j]:
            cell_content = get_cell_display(game.board[i][j])
            if st.button(
                cell_content,
                key=f"cell_{i}_{j}",
                disabled=st.session_state.game_over or game.board[i][j] != EMPTY,
                use_container_width=True
            ):
                handle_cell_click(i, j)
                st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# Legend
st.markdown("""
<div style="text-align:center; padding:1rem; background:#f8f9fa; border-radius:10px; margin-top:1rem;">
    <small><b>Legend:</b> 🌺 Flowers (X) • 🦋 Butterflies (O) • 🐝 Busy Bee</small>
</div>
""", unsafe_allow_html=True)

# Action buttons
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("🔄 Reset Game", use_container_width=True):
        reset_game()
        st.rerun()

with col2:
    if st.button("📊 Stats", use_container_width=True):
        st.session_state.show_stats = not st.session_state.show_stats
        st.rerun()

with col3:
    if st.button("📜 Moves", use_container_width=True):
        st.session_state.show_moves = not st.session_state.show_moves
        st.rerun()
