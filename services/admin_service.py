from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash
import datetime

class AdminService:
    def __init__(self, db):
        self.db = db

    def add_item(self, item_data):
        try:
            required_fields = ['name', 'description', 'price', 'category', 'seller', 'image']
            if not all(item_data.get(field) for field in required_fields):
                return False, "All required fields must be provided"

            new_item = {
                'name': item_data['name'],
                'description': item_data['description'],
                'price': float(item_data['price']),
                'category': item_data['category'],
                'seller': item_data['seller'],
                'image': item_data['image'],
                'rating': 0,
                'reviews': [],
                'number_of_reviewers': 0
            }

            if item_data['category'] == 'GPS Sport Watches' and 'battery_life' in item_data:
                new_item['battery_life'] = item_data['battery_life']
            
            if item_data['category'] in ['Antique Furniture', 'Vinyls'] and 'age' in item_data:
                new_item['age'] = item_data['age']
            
            if item_data['category'] in ['Antique Furniture', 'Running Shoes'] and 'material' in item_data:
                new_item['material'] = item_data['material']
            
            if item_data['category'] == 'Running Shoes' and 'size' in item_data:
                new_item['size'] = item_data['size']

            result = self.db.items.insert_one(new_item)
            if result.inserted_id:
                return True, "Item added successfully"
            return False, "Failed to add item"

        except Exception as e:
            return False, f"Error adding item: {str(e)}"

    def delete_item(self, item_id):
        try:
            item = self.db.items.find_one({"_id": ObjectId(item_id)})
            if not item:
                return False, "Item not found"

            if 'reviews' in item and item['reviews']:
                for review in item['reviews']:
                    if 'user_id' in review:
                        self._update_user_after_item_deletion(review['user_id'], item_id)

            self.db.items.delete_one({"_id": ObjectId(item_id)})
            return True, "Item deleted successfully"

        except Exception as e:
            return False, f"Error deleting item: {str(e)}"

    def add_user(self, username, password, is_admin=False):
        try:
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

            result = self.db.users.insert_one(user)
            if result.inserted_id:
                return True, "User added successfully"
            return False, "Failed to add user"

        except Exception as e:
            return False, f"Error adding user: {str(e)}"

    def delete_user(self, user_id):
        try:
            user = self.db.users.find_one({"_id": ObjectId(user_id)})
            if not user:
                return False, "User not found"

            if 'reviews' in user and user['reviews']:
                for review in user['reviews']:
                    if 'item_id' in review:
                        self._update_item_after_user_deletion(review['item_id'], user_id)

            self.db.users.delete_one({"_id": ObjectId(user_id)})
            return True, "User deleted successfully"

        except Exception as e:
            return False, f"Error deleting user: {str(e)}"

    def _update_user_after_item_deletion(self, user_id, item_id):
        self.db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$pull": {"reviews": {"item_id": item_id}}}
        )
        self._recalculate_user_rating(user_id)

    def _update_item_after_user_deletion(self, item_id, user_id):
        self.db.items.update_one(
            {"_id": ObjectId(item_id)},
            {"$pull": {"reviews": {"user_id": user_id}}}
        )
        self._recalculate_item_rating(item_id)

    def _recalculate_user_rating(self, user_id):
        user = self.db.users.find_one({"_id": ObjectId(user_id)})
        if user and 'reviews' in user and user['reviews']:
            ratings = [r.get('rating', 0) for r in user['reviews'] if 'rating' in r]
            avg_rating = sum(ratings) / len(ratings) if ratings else 0
            self.db.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"average_rating": round(avg_rating, 1)}}
            )

    def _recalculate_item_rating(self, item_id):
        item = self.db.items.find_one({"_id": ObjectId(item_id)})
        if item and 'reviews' in item and item['reviews']:
            ratings = [r.get('rating', 0) for r in item['reviews'] if 'rating' in r]
            if ratings:
                avg_rating = sum(ratings) / len(ratings)
                self.db.items.update_one(
                    {"_id": ObjectId(item_id)},
                    {
                        "$set": {
                            "rating": round(avg_rating, 1),
                            "number_of_reviewers": len(ratings)
                        }
                    }
                )
            else:
                self.db.items.update_one(
                    {"_id": ObjectId(item_id)},
                    {"$set": {"rating": 0, "number_of_reviewers": 0}}
                )