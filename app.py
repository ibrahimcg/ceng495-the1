from flask import Flask, jsonify, render_template, redirect, url_for, flash, session, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity, create_access_token
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo.errors import ConnectionFailure
from bson.objectid import ObjectId
import database
import os
import datetime
from services.auth_service import AuthService
from services.rating_service import RatingService
from services.review_service import ReviewService
from services.admin_service import AdminService

app = Flask(__name__)
app.config.from_pyfile('config.py')
app.secret_key = app.config.get('JWT_SECRET_KEY')

CORS(app, resources={r"/api/*": {"origins": "*"}})

jwt = JWTManager(app)

# Initialize MongoDB connection
try:
    db = database.init_db(app)
    database.mongo_client.admin.command('ping')
    print("MongoDB connection successful")
except ConnectionFailure as e:
    print(f"Failed to connect to MongoDB: {e}")


auth_service = AuthService(db)
rating_service = RatingService(db)
review_service = ReviewService(db)
admin_service = AdminService(db)

@app.route('/')
def home():
    category = request.args.get('category')
    query = {'category': category} if category else {}
    items = list(db.items.find(query))
    
    for item in items:
        item['_id'] = str(item['_id'])
    
    return render_template('home.html', 
                           items=items, 
                           selected_category=category,
                           categories=["Vinyls", "Antique Furniture", "GPS Sport Watches", "Running Shoes"])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        success, session_data, message = auth_service.login_user(username, password)
        
        if success:
            session.update(session_data)
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash(message, 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('register.html')
        
        success, message = auth_service.create_user(username, password)
        
        if success:
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        else:
            flash(message, 'error')
            return render_template('register.html')
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    message = auth_service.logout_user()
    session.clear()
    flash(message, 'info')
    return redirect(url_for('home'))

@app.route('/item/<item_id>')
def item_detail(item_id):
    try:
        item = db.items.find_one({"_id": ObjectId(item_id)})
        if not item:
            flash('Item not found', 'error')
            return redirect(url_for('home'))
        
        item['_id'] = str(item['_id'])
        
        return render_template('item.html', item=item)
    except:
        flash('Invalid item ID', 'error')
        return redirect(url_for('home'))

@app.route('/item/<item_id>/rate', methods=['POST'])
def rate_item(item_id):
    if 'user_id' not in session:
        flash('Please log in to rate items', 'error')
        return redirect(url_for('login'))
    
    rating = int(request.form.get('rating', 0))
    user_id = session['user_id']
    username = session['username']
    
    success, message = rating_service.rate_item(item_id, user_id, username, rating)
    
    flash(message, 'success' if success else 'error')
    return redirect(url_for('item_detail', item_id=item_id))

@app.route('/item/<item_id>/review', methods=['POST'])
def review_item(item_id):
    if 'user_id' not in session:
        flash('Please log in to review items', 'error')
        return redirect(url_for('login'))
    
    content = request.form.get('content', '').strip()
    user_id = session['user_id']
    username = session['username']
    
    success, message = review_service.add_review(item_id, user_id, username, content)
    
    flash(message, 'success' if success else 'error')
    return redirect(url_for('item_detail', item_id=item_id))

@app.route('/item/<item_id>/revoke-rating', methods=['POST'])
def revoke_rating(item_id):
    if 'user_id' not in session:
        flash('Please log in to manage ratings', 'error')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    success, message = rating_service.revoke_rating(item_id, user_id)
    
    flash(message, 'success' if success else 'error')
    return redirect(url_for('item_detail', item_id=item_id))

@app.route('/item/<item_id>/revoke-review', methods=['POST'])
def revoke_review(item_id):
    if 'user_id' not in session:
        flash('Please log in to manage reviews', 'error')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    success, message = review_service.revoke_review(item_id, user_id)
    
    flash(message, 'success' if success else 'error')
    return redirect(url_for('item_detail', item_id=item_id))


@app.route('/profile')
def profile():
    if 'user_id' not in session:
        flash('Please log in to view your profile', 'error')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    user = db.users.find_one({"_id": ObjectId(user_id)})
    
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('home'))
    
    # Convert ObjectId to string
    user['_id'] = str(user['_id'])
    
    return render_template('user/profile.html', user=user)

@app.route('/admin')
def admin_dashboard():
    if 'user_id' not in session or not session.get('is_admin', False):
        flash('Admin access required', 'error')
        return redirect(url_for('home'))
    
    items = list(db.items.find())
    users = list(db.users.find())
    
    for item in items:
        item['_id'] = str(item['_id'])
    for user in users:
        user['_id'] = str(user['_id'])
    
    return render_template('admin/dashboard.html', items=items, users=users)

@app.route('/admin/items/add', methods=['GET', 'POST'])
def admin_add_item():
    if 'user_id' not in session or not session.get('is_admin', False):
        flash('Admin access required', 'error')
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        success, message = admin_service.add_item(request.form)
        flash(message, 'success' if success else 'error')
        if success:
            return redirect(url_for('admin_dashboard'))
    
    return render_template('admin/add_item.html')

@app.route('/admin/items/<item_id>/delete', methods=['POST'])
def admin_delete_item(item_id):
    if 'user_id' not in session or not session.get('is_admin', False):
        flash('Admin access required', 'error')
        return redirect(url_for('home'))
    
    success, message = admin_service.delete_item(item_id)
    flash(message, 'success' if success else 'error')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/users/add', methods=['GET', 'POST'])
def admin_add_user():
    if 'user_id' not in session or not session.get('is_admin', False):
        flash('Admin access required', 'error')
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        is_admin = request.form.get('is_admin') == 'on'
        
        success, message = admin_service.add_user(username, password, is_admin)
        flash(message, 'success' if success else 'error')
        if success:
            return redirect(url_for('admin_dashboard'))
    
    return render_template('admin/add_user.html')

@app.route('/admin/users/<user_id>/delete', methods=['POST'])
def admin_delete_user(user_id):
    if 'user_id' not in session or not session.get('is_admin', False):
        flash('Admin access required', 'error')
        return redirect(url_for('home'))
    
    success, message = admin_service.delete_user(user_id)
    flash(message, 'success' if success else 'error')
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    app.run(debug=app.config['DEBUG'])