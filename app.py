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
    conn.commit()
    conn.close()

TOKENS = {}

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/api/login', methods=["POST"])
def login_page():
    return render_template("login.html")

@app.route("/api/register", methods=["POST"])
def register_page():
    return render_template("register.html")

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    required = ['username', 'password', 'email', 'phone', 'full_name', 'age', 'gender']
    if not all(data.get(f) for f in required):
        return jsonify({"message": "Missing required fields"}), 400

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
        return jsonify({"message": "Username already exists"}), 400
    conn.close()
    return jsonify({"message": "Registered", "role": role})



@app.route('/api/login', methods=['POST'])
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
        TOKENS[token] = 'admin' if username == 'admin' else 'user'
        return jsonify({"access_token": token, "role": TOKENS[token]})
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
        VALUES (%s, %s, %s, %s, %s)
    ''', (name, description, float(price), category, filepath))
    conn.commit()
    conn.close()
    return jsonify({"message": "Product added successfully"})

@app.route('/products', methods=['GET'])
def get_products():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products")
    rows = cursor.fetchall()
    conn.close()
    keys = ['id', 'name', 'description', 'price', 'category', 'image_url']
    return jsonify([dict(zip(keys, row)) for row in rows])

@app.route('/categories', methods=['GET'])
def get_categories():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM categories")
    rows = cursor.fetchall()
    conn.close()
    return jsonify([{"id": row[0], "name": row[1]} for row in rows])

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
        return jsonify({"message": "Category already exists"}), 400
    conn.close()
    return jsonify({"message": "Category added successfully"})

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
