import sqlite3, random, ast


def load_tictactoe_board(user_id):
    with sqlite3.connect("database.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT board, count, opponent_id FROM tictactoe_board WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if row:
            board = ast.literal_eval(row[0])
            count = row[1]
            opponent_id = row[2]
        else:
            board = [i for i in range(1, 10)]
            count = 0
            opponent_id = None
            cursor.execute(
                "INSERT OR REPLACE INTO tictactoe_board (user_id, board, count, opponent_id) VALUES (?, ?, ?, ?)",
                (user_id, str(board), count, opponent_id)
            )
            conn.commit()
        return board, count, opponent_id


def save_tictactoe_board(user_id, board, count, opponent_id=None):
    with sqlite3.connect("database.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO tictactoe_board (user_id, board, count, opponent_id) VALUES (?, ?, ?, ?)",
            (user_id, str(board), count, opponent_id)
        )
        conn.commit()


def delete_tictactoe_board(user_id):
    with sqlite3.connect("database.db") as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tictactoe_board WHERE user_id = ?", (user_id,))
        conn.commit()
        
        
def get_updated_board(board: list) -> str:
    def cell(char):
        return f" {char} "  

    row1 = f"{cell(board[0])}|{cell(board[1])}|{cell(board[2])}"
    row2 = f"{cell(board[3])}|{cell(board[4])}|{cell(board[5])}"
    row3 = f"{cell(board[6])}|{cell(board[7])}|{cell(board[8])}"
    sep = "--------" 
    
    return f"{row1}\n{sep}\n{row2}\n{sep}\n{row3}"




def get_player(turn: int) -> str:
    return "x" if turn % 2 == 0 else "o"


def start_game(response: str) -> bool:
    return response in ["yes", "Yes", "ja", "Ja"]


def get_winner(board: list) -> str:

    for i in range(0, 9, 3):
        if isinstance(board[i], str) and board[i] == board[i+1] == board[i+2]:
            return board[i]

    for i in range(3):
        if isinstance(board[i], str) and board[i] == board[i+3] == board[i+6]:
            return board[i]

    if isinstance(board[0], str) and board[0] == board[4] == board[8]:
        return board[0]
    
    if isinstance(board[2], str) and board[2] == board[4] == board[6]:
        return board[2]

    if all(isinstance(i, str) for i in board):
        return "Draw"
    
    return None


def bot_num() -> int:
    num = random.randint(0,8)
    return num


def is_board_game_over(board):
    win_combos = [
        [0,1,2], [3,4,5], [6,7,8], 
        [0,3,6], [1,4,7], [2,5,8], 
        [0,4,8], [2,4,6]           
    ]
    
    for combo in win_combos:
        a, b, c = combo
        if isinstance(board[a], str) and board[a] == board[b] == board[c]:
            return True
    if all(isinstance(x, str) for x in board):
        return True
    return False