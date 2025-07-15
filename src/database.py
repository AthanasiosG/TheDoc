import aiosqlite, os

class DatabaseManager:
    
    @staticmethod
    async def init_database():
        async with aiosqlite.connect("database.db") as conn:
            cursor = await conn.cursor()

            await cursor.execute("""CREATE TABLE IF NOT EXISTS role_setup(
                guild_id INTEGER NOT NULL,
                role_name TEXT NOT NULL,
                emoji TEXT NOT NULL,
                PRIMARY KEY (guild_id, role_name)
                )
            """)

            await cursor.execute("""CREATE TABLE IF NOT EXISTS violation(
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL
                )
            """)

            await cursor.execute("""CREATE TABLE IF NOT EXISTS violation_limit(
                guild_id INTEGER NOT NULL,
                amount INTEGER NOT NULL DEFAULT 3,
                PRIMARY KEY (guild_id)
                )
            """)

            await cursor.execute("""CREATE TABLE IF NOT EXISTS sup_setup(
                guild_id INTEGER NOT NULL,
                sup_category TEXT NOT NULL,
                sup_ch_name TEXT NOT NULL,
                sup_team_ch_name TEXT NOT NULL,
                sup_role TEXT NOT NULL
                )
            """)

            await cursor.execute("""CREATE TABLE IF NOT EXISTS blacklist(
                guild_id INTEGER NOT NULL,
                word TEXT NOT NULL
                )
            """)

            await cursor.execute("""CREATE TABLE IF NOT EXISTS server_kicked(
                user_id INTEGER NOT NULL
                )
            """)

            await cursor.execute("""CREATE TABLE IF NOT EXISTS tictactoe_board(
                user_id INTEGER NOT NULL,
                opponent_id INTEGER,
                board TEXT NOT NULL,
                count INTEGER NOT NULL,
                PRIMARY KEY (user_id)
                )
            """)

            await cursor.execute("""CREATE TABLE IF NOT EXISTS hangman(
                user_id INTEGER NOT NULL,
                opponent_id INTEGER,
                word TEXT NOT NULL,
                hg_word TEXT,
                failed_attempts INTEGER NOT NULL,
                disabled_buttons TEXT,
                active INTEGER NOT NULL DEFAULT 1,
                PRIMARY KEY (user_id)
                )
            """)

            await cursor.execute("""CREATE TABLE IF NOT EXISTS bot_messages(
                user_id INTEGER NOT NULL,
                channel_id INTEGER,
                message_id INTEGER,
                type TEXT,
                PRIMARY KEY (user_id, type)
                )
            """)

            await cursor.execute("""CREATE TABLE IF NOT EXISTS doc_coins(
                user_id INTEGER NOT NULL,
                user_name TEXT NOT NULL,
                points INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (user_id)
                )
            """)

            await cursor.execute("""CREATE TABLE IF NOT EXISTS auto_vc_control(
                guild_id INTEGER NOT NULL,
                active INTEGER NOT NULL DEFAULT 0,
                primary key (guild_id)
                )
            """)
            
            await cursor.execute("""CREATE TABLE IF NOT EXISTS notes(
                user_id INTEGER NOT NULL,
                text TEXT NOT NULL 
                )
            """)

            await conn.commit()

    @staticmethod            
    async def add_column_to_table(db_path, table_name, column_name, column_type="TEXT", default_value=None):
        """
        Fügt eine neue Spalte zu einer bestehenden SQLite-Tabelle hinzu.
        
        Args:
            db_path (str): Pfad zur SQLite-Datenbankdatei
            table_name (str): Name der Tabelle
            column_name (str): Name der neuen Spalte
            column_type (str): Datentyp der Spalte (TEXT, INTEGER, REAL, BLOB)
            default_value: Standardwert für die neue Spalte (optional)
        
        Returns:
            bool: True wenn erfolgreich, False bei Fehler
        """
        
        # Prüfen ob Datenbankdatei existiert
        if not os.path.exists(db_path):
            print(f"Fehler: Datenbankdatei '{db_path}' nicht gefunden.")
            return False
        
        try:
            # Verbindung zur Datenbank herstellen
            async with aiosqlite.connect(db_path) as conn:
                cursor = await conn.cursor()
                
                # Prüfen ob Tabelle existiert
                await cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name=?
                """, (table_name,))
                
                if not await cursor.fetchone():
                    print(f"Fehler: Tabelle '{table_name}' existiert nicht.")
                    await conn.close()
                    return False
                
                # Prüfen ob Spalte bereits existiert
                await cursor.execute(f"PRAGMA table_info({table_name})")
                columns = [column[1] for column in await cursor.fetchall()]
                
                if column_name in columns:
                    print(f"Spalte '{column_name}' existiert bereits in Tabelle '{table_name}'.")
                    await conn.close()
                    return False
                
                # ALTER TABLE Statement zusammenbauen
                alter_query = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
                
                if default_value is not None:
                    if isinstance(default_value, str):
                        alter_query += f" DEFAULT '{default_value}'"
                    else:
                        alter_query += f" DEFAULT {default_value}"
                
                # Spalte hinzufügen
                await cursor.execute(alter_query)
                await conn.commit()
                
                print(f"Spalte '{column_name}' erfolgreich zu Tabelle '{table_name}' hinzugefügt.")
                
                # Tabellenschema anzeigen zur Bestätigung
                await cursor.execute(f"PRAGMA table_info({table_name})")
                columns_info = await cursor.fetchall()
                print("\nAktuelles Tabellenschema:")
                for col in columns_info:
                    print(f"  {col[1]} ({col[2]})")
                
                conn.close()
                return True
        
        except aiosqlite.Error as e:
            print(f"SQLite-Fehler: {e}")
        
            if 'conn' in locals():
                await conn.close()
        
            return False
        
        except Exception as e:
            print(f"Unerwarteter Fehler: {e}")
        
            if 'conn' in locals():
                await conn.close()
        
            return False    