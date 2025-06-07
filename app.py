from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
import psycopg2
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# PostgreSQL connection
def get_db_connection():
    return psycopg2.connect(
        host=os.environ['DB_HOST'],
        dbname=os.environ['DB_NAME'],
        user=os.environ['DB_USER'],
        password=os.environ['DB_PASSWORD'],
        port=os.environ.get("DB_PORT", 5432)
    )

# Create tables if they don't exist
def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT,
            email TEXT,
            phone TEXT,
            full_name TEXT,
            age INTEGER,
            gender TEXT,
            role TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id SERIAL PRIMARY KEY,
            name TEXT UNIQUE
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            name TEXT,
            description TEXT,
            price NUMERIC,
            category TEXT,
            image_url TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Simulated token storage
TOKENS = {}

# Routes for rendering HTML pages
@app.route('/')
def home():
    return render_template("index.html")

@app.route("/login")
def login_page():
    return render_template("login.html")

@app.route("/register")
def register_page():
    return render_template("register.html")

# Register API
@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json()
    required = ['username', 'password', 'email', 'phone', 'full_name', 'age', 'gender']
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"message": f"Missing fields: {', '.join(missing)}"}), 400

    username = data['username']
    password = data['password']
    email = data['email']
    phone = data['phone']
    full_name = data['full_name']
    age = int(data['age'])
    gender = data['gender']
    role = 'admin' if username == 'admin' else 'user'

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO users (username, password, email, phone, full_name, age, gender, role)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (username, password, email, phone, full_name, age, gender, role))
        conn.commit()
    except:
        conn.rollback()
        return jsonify({"message": "Username already exists"}), 400
    finally:
        conn.close()

    return jsonify({"message": "Registered", "role": role}), 200

# Login API
@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data['username']
    password = data['password']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
    user = cursor.fetchone()
    conn.close()

    if user:
        token = f"token-{username}"
        TOKENS[token] = user[-1]  # Save role
        return jsonify({"access_token": token, "role": user[-1]})
    return jsonify({"message": "Invalid credentials"}), 401

# Token check helper
def verify_admin_token():
    auth = request.headers.get('Authorization')
    if not auth or not auth.startswith("Bearer "):
        return False
    token = auth.split(" ")[1]
    return TOKENS.get(token) == 'admin'

# Add product API
@app.route('/add-product', methods=['POST'])
def add_product():
    if not verify_admin_token():
        return jsonify({"message": "Unauthorized"}), 403

    name = request.form['name']
    description = request.form['description']
    price = request.form['price']
    category = request.form['category']
    file = request.files['image']
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO products (name, description, price, category, image_url)
        VALUES (%s, %s, %s, %s, %s)
    ''', (name, description, float(price), category, filepath))
    conn.commit()
    conn.close()

    return jsonify({"message": "Product added successfully"})

# Get products
@app.route('/products', methods=['GET'])
def get_products():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products")
    rows = cursor.fetchall()
    conn.close()
    keys = ['id', 'name', 'description', 'price', 'category', 'image_url']
    return jsonify([dict(zip(keys, row)) for row in rows])

# Get categories
@app.route('/categories', methods=['GET'])
def get_categories():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM categories")
    rows = cursor.fetchall()
    conn.close()
    return jsonify([{"id": row[0], "name": row[1]} for row in rows])

# Add category
@app.route('/categories', methods=['POST'])
def add_category():
    if not verify_admin_token():
        return jsonify({"message": "Unauthorized"}), 403

    name = request.json.get("name")
    if not name:
        return jsonify({"message": "Missing category name"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO categories (name) VALUES (%s)", (name,))
        conn.commit()
    except:
        conn.rollback()
        return jsonify({"message": "Category already exists"}), 400
    finally:
        conn.close()

    return jsonify({"message": "Category added successfully"})

# Delete category
@app.route('/categories/<int:cat_id>', methods=['DELETE'])
def delete_category(cat_id):
    if not verify_admin_token():
        return jsonify({"message": "Unauthorized"}), 403

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM categories WHERE id = %s", (cat_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Category deleted"})

if __name__ == '__main__':
    create_tables()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
