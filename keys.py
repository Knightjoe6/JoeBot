from db import DatabaseConnection
from datetime import datetime

class GameKeyManager:

    def insert_game_key(self, name, description, game_key):
        with DatabaseConnection() as db:
            query = """INSERT INTO GameKeys (name, description, game_key) VALUES (%s, %s, %s)"""
            values = (name, description, game_key)
            return db.execute_query(query, values) is None

    def mark_as_redeemed(self, game_key):
        with DatabaseConnection() as db:
            query = """UPDATE GameKeys SET redeemed = TRUE, date_redeemed = %s WHERE game_key = %s AND redeemed = FALSE"""
            values = (datetime.now(), game_key)
            return db.execute_query(query, values) is None

    def get_random_unredeemed_keys(self, n):
        with DatabaseConnection() as db:
            query = "SELECT name, description, game_key FROM GameKeys WHERE redeemed = FALSE ORDER BY RAND() LIMIT %s"
            values = (n,)
            return self.db.execute_query(query, values)

    def get_key_list(self, hide_redeemed):
        with DatabaseConnection() as db:
            query = f"""SELECT name, description, redeemed, date_added, date_redeemed FROM GameKeys {"WHERE redeemed = 'No'" if hide_redeemed else ""}"""
            return db.execute_query(query)