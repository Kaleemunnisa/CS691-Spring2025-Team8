import mysql.connector
from mysql.connector import Error

def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host='localhost',
            port=3300,
            user='root',
            password='sahi30',
            database='pacecart_data'
        )
        if connection.is_connected():
                 return connection
    except Error as e:
            print(f"Error connecting to MySQL: {e}")
            return None
    return None