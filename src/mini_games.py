import aiosqlite, random, ast


#tictactoe
async def load_ttt_board(user_id):
    async with aiosqlite.connect("database.db") as conn:
        cursor = await conn.cursor()
        await cursor.execute("SELECT board, count, opponent_id FROM tictactoe_board WHERE user_id=?", (user_id,))
        row = await cursor.fetchone()
        if row:
            board = ast.literal_eval(row[0])
            count = row[1]
            opponent_id = row[2]
        else:
            board = [i for i in range(1, 10)]
            count = 0
            opponent_id = None
            await cursor.execute("INSERT OR REPLACE INTO tictactoe_board (user_id, board, count, opponent_id) VALUES (?, ?, ?, ?)", (user_id, str(board), count, opponent_id))
            await conn.commit()
        return board, count, opponent_id


async def save_ttt_board(user_id, board, count, opponent_id=None):
    async with aiosqlite.connect("database.db") as conn:
        cursor = await conn.cursor()
        await cursor.execute("INSERT OR REPLACE INTO tictactoe_board (user_id, board, count, opponent_id) VALUES (?, ?, ?, ?)", (user_id, str(board), count, opponent_id))
        await conn.commit()


async def delete_ttt_board(user_id):
    async with aiosqlite.connect("database.db") as conn:
        cursor = await conn.cursor()
        await cursor.execute("DELETE FROM tictactoe_board WHERE user_id=?", (user_id,))
        await conn.commit()
        
        
def get_ttt_updated_board(board: list) -> str:
    def cell(char):
        return f" {char} "  

    row1 = f"{cell(board[0])}|{cell(board[1])}|{cell(board[2])}"
    row2 = f"{cell(board[3])}|{cell(board[4])}|{cell(board[5])}"
    row3 = f"{cell(board[6])}|{cell(board[7])}|{cell(board[8])}"
    sep = "--------" 
    
    return f"{row1}\n{sep}\n{row2}\n{sep}\n{row3}"




def get_ttt_player(turn: int) -> str:
    return "x" if turn % 2 == 0 else "o"


def get_ttt_winner(board: list) -> str:
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


def bot_ttt_num() -> int:
    num = random.randint(0,8)
    return num


def is_ttt_board_game_over(board):
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


#hangman

async def load_hangman(user_id):
    async with aiosqlite.connect("database.db") as conn:
        cursor = await conn.cursor()
        await cursor.execute("SELECT opponent_id, word, hg_word, failed_attempts, disabled_buttons, active FROM hangman WHERE user_id=?", (user_id,))
        row = await cursor.fetchone()
        if row:
            opponent_id, word, hg_word, failed_attempts, disabled_buttons, active = row
            if disabled_buttons:
                disabled_buttons = set(disabled_buttons.split(","))
            else:
                disabled_buttons = set()
        else:
            opponent_id = None
            word = ""
            hg_word = ""
            failed_attempts = 0
            disabled_buttons = set()
            active = 1
            await cursor.execute("INSERT OR REPLACE INTO hangman (user_id, opponent_id, word, hg_word, failed_attempts, disabled_buttons, active) VALUES (?, ?, ?, ?, ?, ?, ?)", (user_id, opponent_id, word, hg_word, failed_attempts, "", active))
            await conn.commit()
        
        return opponent_id, word, hg_word, failed_attempts, disabled_buttons, active


async def save_hangman(user_id, opponent_id, word, hg_word, failed_attempts, disabled_buttons, active=1):
    async with aiosqlite.connect("database.db") as conn:
        cursor = await conn.cursor()
        if isinstance(disabled_buttons, set):
            disabled_buttons_str = ",".join(disabled_buttons)
        else:
            disabled_buttons_str = disabled_buttons or ""
        await cursor.execute("INSERT OR REPLACE INTO hangman (user_id, opponent_id, word, hg_word, failed_attempts, disabled_buttons, active) VALUES (?, ?, ?, ?, ?, ?, ?)", (user_id, opponent_id, word, hg_word, failed_attempts, disabled_buttons_str, active))
        await conn.commit()


async def delete_hangman(user_id):
    async with aiosqlite.connect("database.db") as conn:
        cursor = await conn.cursor()
        await cursor.execute("DELETE FROM hangman WHERE user_id=?", (user_id,))
        await conn.commit()


async def deactivate_hangman(user_id):
    async with aiosqlite.connect("database.db") as conn:
        cursor = await conn.cursor()
        await cursor.execute("UPDATE hangman SET active=0 WHERE user_id=?", (user_id,))
        await conn.commit()


async def is_hangman_active(user_id):
    async with aiosqlite.connect("database.db") as conn:
        cursor = await conn.cursor()
        await cursor.execute("SELECT active FROM hangman WHERE user_id=?", (user_id,))
        row = await cursor.fetchone()
        return row and row[0] == 1


def get_hg_winner(word: str, hg_word: str) -> str:
    if word == hg_word:
        return "You won!"
    elif len(hg_word) == 0:
        return "You lost!"
    else:
        return "Game is still ongoing"


def is_hg_game_over(word: str, hg_word: str, failed_attempts: int) -> bool:
    if word == hg_word or "◻️" not in hg_word or failed_attempts >= 6:
        return True
    return False


async def get_disabled_buttons(user_id):
    async with aiosqlite.connect("database.db") as conn:
        cursor = await conn.cursor()
        await cursor.execute("SELECT disabled_buttons FROM hangman WHERE user_id=?", (user_id,))
        row = await cursor.fetchone()
        if row and row[0]:
            return set(row[0].split(","))
        return set()

async def set_disabled_buttons(user_id, disabled_buttons):
    async with aiosqlite.connect("database.db") as conn:
        cursor = await conn.cursor()
        await cursor.execute("UPDATE hangman SET disabled_buttons=? WHERE user_id=?", (",".join(disabled_buttons), user_id))
        await conn.commit()