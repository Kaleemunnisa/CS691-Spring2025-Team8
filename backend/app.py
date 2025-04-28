from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash  # For password hashing
from huspm_module.huspm import get_top_recommendations, purchases_df, browsing_history_df, products_df, product_popularity

app = Flask(__name__)
CORS(app)  # Allow frontend to call backend without CORS issues

# MySQL Database Configuration
app.config['MYSQL_HOST'] = 'localhost'  # MySQL Host
app.config['MYSQL_USER'] = 'root'       # MySQL Username
app.config['MYSQL_PASSWORD'] = 'sahi30'  # MySQL Password
app.config['MYSQL_PORT'] = 3300   # 
app.config['MYSQL_DB'] = 'pacecart'     # MySQL Database Name

# Initialize MySQL
mysql = MySQL(app)

@app.route('/')
def home():
    return jsonify({"message": "Welcome to PaceCart Recommendation System Backend!"})

@app.route('/recommendations', methods=['GET'])
def recommendations():
    try:
        user_id = request.args.get('user_id', type=int)
        if user_id is None:
            return jsonify({'error': 'user_id parameter is required'}), 400

        recommendations = get_top_recommendations(
            user_id=user_id,
            purchases_df=purchases_df,
            browsing_history_df=browsing_history_df,
            products_df=products_df,
            product_popularity=product_popularity
        )

        return jsonify(recommendations)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Signup Route
@app.route('/signup/', methods=['POST'])
def signup():
    data = request.get_json()

    # Extract user data from the request
    name = data.get('name')
    userid = data.get('userid')
    password = data.get('password')
    mobile = data.get('mobile')
    address = data.get('address')

    # Hash the password before storing it
    hashed_password = generate_password_hash(password)

    # Create a cursor object to interact with MySQL
    cur = mysql.connection.cursor()

    # Check if the user already exists
    cur.execute("SELECT * FROM users WHERE userid = %s", [userid])
    existing_user = cur.fetchone()

    if existing_user:
        return jsonify({'message': 'User already exists!'}), 400
    else:
        # Insert new user into the database
        cur.execute(
            "INSERT INTO users (name, userid, password, mobile, address) VALUES (%s, %s, %s, %s, %s)",
            (name, userid, hashed_password, mobile, address)
        )
        mysql.connection.commit()  # Commit the transaction
        return jsonify({'message': 'Signup successful!'}), 201

# Login Route
@app.route('/login/', methods=['POST'])
def login():
    data = request.get_json()

    # Extract login credentials from the request
    userid = data.get('userid')
    password = data.get('password')

    # Create a cursor object to interact with MySQL
    cur = mysql.connection.cursor()

    # Check if the user exists
    cur.execute("SELECT * FROM users WHERE userid = %s", [userid])
    user = cur.fetchone()

    if user and check_password_hash(user[2], password):  # user[2] contains the hashed password
        return jsonify({'message': 'Login successful!'}), 200
    else:
        return jsonify({'message': 'Invalid username or password!'}), 400

if __name__ == '__main__':
    app.run(debug=True)

