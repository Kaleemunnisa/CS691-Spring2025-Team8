import mysql.connector

def get_db_connection():
    connection = mysql.connector.connect(
        host='localhost',        
        user='root',    
        password='sahi30',
        database='pacecart_data',
        port = 3300 
    )
    return connection
