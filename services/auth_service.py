from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token

class AuthService:
    def __init__(self, db):
        self.db = db

    def create_user(self, username, password, is_admin=False):
        if not username or not password:
            return False, "Username and password are required"

        if self.db.users.find_one({'username': username}):
            return False, "Username already exists"

        user = {
            'username': username,
            'password': generate_password_hash(password),
            'is_admin': is_admin,
            'reviews': [],
            'average_rating': 0
        }

        try:
            result = self.db.users.insert_one(user)
            if result.inserted_id:
                return True, "User created successfully"
            return False, "Failed to create user"
        except Exception as e:
            return False, f"Error creating user: {str(e)}"

    def login_user(self, username, password):
        if not username or not password:
            return False, None, "Username and password are required"

        user = self.db.users.find_one({'username': username})
        
        if user and check_password_hash(user['password'], password):
            session_data = {
                'user_id': str(user['_id']),
                'username': user['username'],
                'is_admin': user.get('is_admin', False),
                'access_token': create_access_token(identity=str(user['_id']))
            }
            return True, session_data, "Login successful"
        
        return False, None, "Invalid username or password"

    def logout_user(self):
        return "You have been logged out"