from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Simulated in-memory token-role map (for demo)
TOKENS = {}  # token -> role

def get_db_connection():
    conn = sqlite3.connect('gym_products.db')
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            description TEXT,
            price REAL,
            category TEXT,
            image_url TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data['username']
    password = data['password']
    role = 'admin' if username == 'admin' else 'user'  # simple logic

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, password, role))
        conn.commit()
    except sqlite3.IntegrityError:
        return jsonify({"message": "Username already exists"}), 400
    conn.close()
    return jsonify({"message": "User registered successfully", "role": role})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data['username']
    password = data['password']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()
    conn.close()

    if user:
        token = f"token-{username}"
        TOKENS[token] = user['role']
        return jsonify({"access_token": token, "role": user['role']})
    return jsonify({"message": "Invalid credentials"}), 401

def verify_admin_token():
    auth = request.headers.get('Authorization')
    if not auth or not auth.startswith("Bearer "):
        return False
    token = auth.split(" ")[1]
    return TOKENS.get(token) == 'admin'

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
        VALUES (?, ?, ?, ?, ?)
    ''', (name, description, float(price), category, filepath))
    conn.commit()
    conn.close()

    return jsonify({"message": "Product added successfully!"})

@app.route('/products', methods=['GET'])
def get_products():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    conn.close()
    return jsonify([dict(row) for row in products])

@app.route('/categories', methods=['GET'])
def get_categories():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM categories")
    categories = cursor.fetchall()
    conn.close()
    return jsonify([dict(row) for row in categories])

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
        cursor.execute("INSERT INTO categories (name) VALUES (?)", (name,))
        conn.commit()
    except sqlite3.IntegrityError:
        return jsonify({"message": "Category already exists"}), 400
    conn.close()
    return jsonify({"message": "Category added successfully"})

@app.route('/categories/<int:cat_id>', methods=['DELETE'])
def delete_category(cat_id):
    if not verify_admin_token():
        return jsonify({"message": "Unauthorized"}), 403
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM categories WHERE id = ?", (cat_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Category deleted"})

if __name__ == '__main__':
    create_tables()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
