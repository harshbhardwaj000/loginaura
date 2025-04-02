from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from pymongo import MongoClient
import datetime

app = Flask(__name__)
CORS(app)
bcrypt = Bcrypt(app)

# Setup the Flask-JWT-Extended extension
app.config["JWT_SECRET_KEY"] = "3ab5aa4099d25fe2057c7fe0af5d1f01d3dc5d54f93124154fc3b88bfc1a242dcabffaf04acabb696774ddefca2f234a4257666e13d6c8245bb7693dce01c6c0"  # Change this in production!
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = datetime.timedelta(hours=5)
jwt = JWTManager(app)

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['auth_system']
users_collection = db['users']

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # Check if user already exists
    existing_user = users_collection.find_one({'email': data['email']})
    if existing_user:
        return jsonify({'message': 'User already exists'}), 409
    
    # Hash the password
    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    
    # Store new user
    new_user = {
        'name': data['name'],
        'email': data['email'],
        'password': hashed_password,
        'created_at': datetime.datetime.utcnow()
    }
    
    users_collection.insert_one(new_user)
    
    return jsonify({'message': 'User created successfully'}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    
    # Find user by email
    user = users_collection.find_one({'email': data['email']})
    
    if not user or not bcrypt.check_password_hash(user['password'], data['password']):
        return jsonify({'message': 'Invalid credentials'}), 401
    
    # Create access token
    access_token = create_access_token(identity=str(user['_id']))
    
    return jsonify({
        'message': 'Login successful',
        'access_token': access_token,
        'user': {
            'name': user['name'],
            'email': user['email']
        }
    }), 200

@app.route('/api/protected', methods=['GET'])
@jwt_required()
def protected():
    # Access the identity of the current user with get_jwt_identity
    current_user_id = get_jwt_identity()
    user = users_collection.find_one({'_id': current_user_id})
    
    return jsonify({'message': f'Hello, {user["name"]}!'}), 200

if __name__ == '__main__':
    app.run(debug=True)