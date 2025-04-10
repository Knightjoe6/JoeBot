import os
import mysql.connector
from mysql.connector import Error

MYSQL_HOST = os.getenv('MYSQL_HOST')
MYSQL_USER = os.getenv('MYSQL_USER')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')
MYSQL_DATABASE = os.getenv('MYSQL_DATABASE')

print(MYSQL_DATABASE)

class DatabaseConnection:
    def __init__(self):
        self.connection = None

    def __enter__(self):
        try:
            self.connection = mysql.connector.connect(
                host=MYSQL_HOST,
                database=MYSQL_DATABASE,
                user=MYSQL_USER,
                password=MYSQL_PASSWORD
            )
            return self
        except Error as e:
            print(f"Error connecting to database: {e}")
            return None

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.connection and self.connection.is_connected():
            self.connection.close()

    def execute_query(self, query, values=None):
        if self.connection is None or not self.connection.is_connected():
            print("No active database connection.")
            return None
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(query, values)
            if query.strip().upper().startswith("SELECT"):
                result = cursor.fetchall()
            else:
                self.connection.commit()
                result = None
            cursor.close()
            return result
        except Error as e:
            print(f"Error executing query: {e}")
            return None
