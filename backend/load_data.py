import mysql.connector
import random
import uuid
from datetime import datetime, timedelta

# MySQL setup
MYSQL_HOST = 'localhost'
MYSQL_PORT = 3300
MYSQL_USER = 'root'
MYSQL_PASSWORD = 'sahi30'
MYSQL_DB = 'pacecart_data'

random.seed(42)

# Define categories and sample product names
categories = {
    'Snacks': ['Potato Chips', 'Tortilla Chips', 'Pretzels', 'Popcorn', 'Cheese Puffs'],
    'Beverages': ['Bottled Water', 'Cola', 'Orange Juice', 'Iced Tea', 'Energy Drink'],
    'Dairy': ['Cheddar Cheese', 'Whole Milk', 'Yogurt', 'Butter', 'Cream Cheese'],
    'Fruits': ['Apples', 'Bananas', 'Oranges', 'Strawberries', 'Blueberries'],
    'Vegetables': ['Carrots', 'Broccoli', 'Spinach', 'Tomatoes', 'Cucumbers']
}

def connect_db():
    return mysql.connector.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB
    )

def generate_product_name(base_name, category):
    brand_prefixes = ['Fresh', 'Organic', 'Golden', 'Pure', 'Nature', '']
    suffixes = ['Pack', 'Premium', 'Classic', '', 'Select']
    brand = random.choice(brand_prefixes).strip()
    suffix = random.choice(suffixes).strip()
    if category in ['Snacks', 'Beverages', 'Dairy']:
        return f"{brand} {base_name} {suffix}".strip()
    else:
        return f"{brand} {base_name}".strip()

def fetch_ids(table_name, id_column):
    connection = connect_db()
    cursor = connection.cursor()
    cursor.execute(f"SELECT {id_column} FROM {table_name}")
    ids = [row[0] for row in cursor.fetchall()]
    cursor.close()
    connection.close()
    return ids

def generate_products():
    connection = connect_db()
    cursor = connection.cursor()

    for category in categories:
        num_products = 200
        for _ in range(num_products):
            base_name = random.choice(categories[category])
            product_name = generate_product_name(base_name, category)
            stock = random.randint(0, 100)
            price = round(random.uniform(1.0, 100.0), 2)
            rating = round(random.uniform(1.0, 5.0), 1)
            clicks = random.randint(0, 500)

            cursor.execute("""
                INSERT INTO products (product_name, category, image_url, stock, price, rating, clicks)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (product_name, category, '', stock, price, rating, clicks))

    connection.commit()
    cursor.close()
    connection.close()

def generate_users():
    connection = connect_db()
    cursor = connection.cursor()

    names_list = [
        'sahithya', 'keerthi', 'meghana','sai','jaya', 'saketh', 'arjun', 'sujatha', 'venkatesh', 'amaira' ,'mihira' ,'ananya', 'ravi', 'sneha',
        'vishal', 'deepa', 'kiran', 'priya', 'rahul', 'aishwarya', 'madhav', 'shruti', 'swapna' , 'deekshi','narendra', 'varshi' , 'kushi' , 'sume'
    ]

    for _ in range(500):
        username = random.choice(names_list) + str(random.randint(1, 1000))  # example: sahithya845
        password_hash = uuid.uuid4().hex
        email = f"{username}@example.com"
        registration_date = random_timestamp_2024()

        cursor.execute("""
            INSERT INTO users (username, password_hash, email, registration_date)
            VALUES (%s, %s, %s, %s)
        """, (username, password_hash, email, registration_date))

    connection.commit()
    cursor.close()
    connection.close()


def generate_purchases():
    connection = connect_db()
    cursor = connection.cursor()

    user_ids = fetch_ids('users', 'user_id')
    product_ids = fetch_ids('products', 'product_id')

    for _ in range(1500):
        user_id = random.choice(user_ids)
        product_id = random.choice(product_ids)
        purchase_date = random_date_2024()
        quantity = random.randint(1, 5)
        total_price = quantity * random.uniform(1.0, 100.0)

        cursor.execute("""
            INSERT INTO purchases (user_id, product_id, purchase_date, quantity, total_price)
            VALUES (%s, %s, %s, %s, %s)
        """, (user_id, product_id, purchase_date, quantity, round(total_price, 2)))

    connection.commit()
    cursor.close()
    connection.close()

def generate_browsing_history():
    connection = connect_db()
    cursor = connection.cursor()

    user_ids = fetch_ids('users', 'user_id')
    product_ids = fetch_ids('products', 'product_id')

    for _ in range(2000):
        user_id = random.choice(user_ids)
        product_id = random.choice(product_ids)
        timestamp = random_timestamp_2024()
        action_type = random.choice(['viewed', 'added_to_cart', 'clicked'])

        cursor.execute("""
            INSERT INTO browsing_history (user_id, product_id, timestamp, action)
            VALUES (%s, %s, %s, %s)
        """, (user_id, product_id, timestamp, action_type))

    connection.commit()
    cursor.close()
    connection.close()

def generate_cart():
    connection = connect_db()
    cursor = connection.cursor()

    user_ids = fetch_ids('users', 'user_id')
    product_ids = fetch_ids('products', 'product_id')

    for _ in range(2000):
        user_id = random.choice(user_ids)
        product_id = random.choice(product_ids)
        quantity = random.randint(1, 5)
        added_date = random_timestamp_2024()

        cursor.execute("""
            INSERT INTO cart (user_id, product_id, quantity, added_date)
            VALUES (%s, %s, %s, %s)
        """, (user_id, product_id, quantity, added_date))

    connection.commit()
    cursor.close()
    connection.close()

def random_date_2024():
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 12, 31)
    delta = end_date - start_date
    random_days = random.randint(0, delta.days)
    return (start_date + timedelta(days=random_days)).strftime('%Y-%m-%d')

def random_timestamp_2024():
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 12, 31)
    delta = end_date - start_date
    random_seconds = random.randint(0, delta.days * 24 * 60 * 60)
    return (start_date + timedelta(seconds=random_seconds)).strftime('%Y-%m-%d %H:%M:%S')

def update_existing_usernames():
    connection = connect_db()
    cursor = connection.cursor()

    # list of realistic names
    names_list = [
        'sahithya', 'keerthi', 'meghana', 'saketh', 'arjun', 'ananya', 'ravi', 'sneha',
        'vishal', 'deepa', 'kiran', 'priya', 'rahul', 'aishwarya', 'siddharth', 'isha',
        'tanvi', 'omkar', 'madhav', 'shruti'
    ]

    cursor.execute("SELECT user_id FROM users")
    user_ids = [row[0] for row in cursor.fetchall()]

    print(f"Found {len(user_ids)} users. Updating...")

    for user_id in user_ids:
        username = random.choice(names_list) + str(random.randint(1, 1000))
        email = f"{username}@example.com"

        cursor.execute("""
            UPDATE users
            SET username = %s, email = %s
            WHERE user_id = %s
        """, (username, email, user_id))

    connection.commit()
    print("✅ Updated all users.")
    cursor.close()
    connection.close()

if __name__ == '__main__':
    update_existing_usernames()

def main():
    generate_users()
    generate_products()
    generate_purchases()
    generate_browsing_history()
    generate_cart()



if __name__ == '__main__':
    main()
