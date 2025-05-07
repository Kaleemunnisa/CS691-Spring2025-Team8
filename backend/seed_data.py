import mysql.connector
import random
from datetime import datetime, timedelta
import string

# Step 1: Connect to DB
conn = mysql.connector.connect(
    host="localhost",
    port=3300,
    user="root",
    password="sahi30",
    database="pacecart_data"
)
cursor = conn.cursor(dictionary=True)

print("🧹 Clearing existing data...")

cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
cursor.execute("TRUNCATE TABLE purchases;")
cursor.execute("TRUNCATE TABLE cart;")
cursor.execute("TRUNCATE TABLE browsing_history;")
cursor.execute("TRUNCATE TABLE recommendations;")
cursor.execute("TRUNCATE TABLE users;")
cursor.execute("ALTER TABLE users AUTO_INCREMENT = 1;")
cursor.execute("ALTER TABLE purchases AUTO_INCREMENT = 1;")
cursor.execute("ALTER TABLE cart AUTO_INCREMENT = 1;")
cursor.execute("ALTER TABLE browsing_history AUTO_INCREMENT = 1;")
cursor.execute("ALTER TABLE recommendations AUTO_INCREMENT = 1;")
cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

print("Tables cleared.")

# Step 2: Insert Indian users
names_list = [
    "Sahithya", "Sai", "Keerthi", "Narendra", "Meghana", "Saketh", "Kavya", "Rasagna", "Chaitu", "Amaira",
    "Arjun", "Jaya", "Narasimha", "Venkatesh", "Rahul", "Amar", "Siva", "Sujatha", "Punnarao", "Kushi",
    "Deekshi", "Mihira", "Niharika", "Rajani", "Kondal", "Swapna", "Teja", "Likitha", "Rani", "Varshi",
    "Chinnu", "Uday", "Ashok", "Koteswari"
]

print("Inserting users...")
for name in names_list:
    username = name.lower()
    email = f"{username}@gmail.com"
    password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    reg_date = datetime(2024, 1, 1) + timedelta(days=random.randint(0, 365))
    cursor.execute("""
        INSERT INTO users (username, password, email, registration_date)
        VALUES (%s, %s, %s, %s)
    """, (username, password, email, reg_date))
conn.commit()
print(f"Inserted {len(names_list)} users.")

# Step 3: Fetch IDs
cursor.execute("SELECT user_id FROM users")
user_ids = [row['user_id'] for row in cursor.fetchall()]

cursor.execute("SELECT product_id FROM products")
product_ids = [row['product_id'] for row in cursor.fetchall()]

# Step 4: Insert purchases for 30 active users
print("Inserting purchases for 30 users...")
active_users = random.sample(user_ids, 30)
purchase_count = 0

for uid in active_users:
    for _ in range(100):
        pid = random.choice(product_ids)
        quantity = random.randint(1, 4)
        total_price = round(quantity * random.uniform(3, 20), 2)
        date = datetime(2024, 1, 1) + timedelta(days=random.randint(0, 365))
        cursor.execute("""
            INSERT INTO purchases (user_id, product_id, purchase_date, quantity, total_price)
            VALUES (%s, %s, %s, %s, %s)
        """, (uid, pid, date, quantity, total_price))
        purchase_count += 1

print(f"Inserted {purchase_count} purchases.")

# Step 5: Browsing history for all users
print("Inserting browsing history...")
browsing_count = 0
for uid in user_ids:
    for _ in range(random.randint(5, 15)):
        pid = random.choice(product_ids)
        action = random.choice(["viewed", "clicked", "added_to_cart"])
        timestamp = datetime(2024, 1, 1) + timedelta(days=random.randint(0, 365))
        cursor.execute("""
            INSERT INTO browsing_history (user_id, product_id, timestamp, action)
            VALUES (%s, %s, %s, %s)
        """, (uid, pid, timestamp, action))
        browsing_count += 1

print(f"Inserted {browsing_count} browsing history records.")

# Step 6: Cart items (some users)
print("🛒 Inserting cart data...")
cart_count = 0
for uid in random.sample(user_ids, 20):
    for _ in range(random.randint(1, 5)):
        pid = random.choice(product_ids)
        quantity = random.randint(1, 3)
        added_date = datetime(2024, 1, 1) + timedelta(days=random.randint(0, 365))
        cursor.execute("""
            INSERT INTO cart (user_id, product_id, quantity, added_date)
            VALUES (%s, %s, %s, %s)
        """, (uid, pid, quantity, added_date))
        cart_count += 1

print(f"Inserted {cart_count} cart items.")

# Step 7: Recommendations
print("🤖 Inserting recommendations...")
reco_count = 0
for uid in active_users:
    recommended_products = random.sample(product_ids, 5)
    for pid in recommended_products:
        score = round(random.uniform(0.1, 1.0), 2)
        date = datetime(2024, 1, 1) + timedelta(days=random.randint(0, 365))
        cursor.execute("""
            INSERT INTO recommendations (user_id, product_id, recommendation_score, recommendation_date)
            VALUES (%s, %s, %s, %s)
        """, (uid, pid, score, date))
        reco_count += 1

conn.commit()
cursor.close()
conn.close()

print("All data inserted successfully!")
print(f"Users: {len(names_list)}")
print(f" Purchases: {purchase_count}")
print(f"Browsing history: {browsing_count}")
print(f"Cart items: {cart_count}")
print(f"Recommendations: {reco_count}")
