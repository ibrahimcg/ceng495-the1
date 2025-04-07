from bson.objectid import ObjectId
import datetime

class ReviewService:
    def __init__(self, db):
        self.db = db

    def add_review(self, item_id, user_id, username, content):
        try:
            if not content.strip():
                return False, "Review content cannot be empty"

            item = self.db.items.find_one({"_id": ObjectId(item_id)})
            if not item:
                return False, "Item not found"

            existing_review = next(
                (review for review in item.get('reviews', [])
                 if review.get('user_id') == user_id), None)

            if existing_review:
                self._update_existing_review(item_id, user_id, content)
                return True, "Review updated successfully"
            else:
                self._create_new_review(item_id, user_id, username, content, item['name'])
                return True, "Review submitted successfully"

        except Exception as e:
            return False, f"Error submitting review: {str(e)}"

    def revoke_review(self, item_id, user_id):
        item = self.db.items.find_one({
            "_id": ObjectId(item_id),
            "reviews": {
                "$elemMatch": {
                    "user_id": user_id,
                    "content": {"$exists": True},
                    "rating": {"$exists": False}
                }
            }
        })

        if item:
            self.db.items.update_one(
                {"_id": ObjectId(item_id)},
                {"$pull": {"reviews": {"user_id": user_id}}}
            )
            
            self.db.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$pull": {"reviews": {"item_id": str(item_id)}}}
            )
        else:
            self.db.items.update_one(
                {
                    "_id": ObjectId(item_id),
                    "reviews": {
                        "$elemMatch": {
                            "user_id": user_id,
                            "content": {"$exists": True}
                        }
                    }
                },
                {"$unset": {"reviews.$.content": ""}}
            )
            
            self.db.users.update_one(
                {
                    "_id": ObjectId(user_id),
                    "reviews": {
                        "$elemMatch": {
                            "item_id": str(item_id),
                            "content": {"$exists": True}
                        }
                    }
                },
                {"$unset": {"reviews.$.content": ""}}
            )
        
        return True, "Review successfully revoked"
        
    def _update_existing_review(self, item_id, user_id, content):
        self.db.items.update_one(
            {"_id": ObjectId(item_id), "reviews.user_id": user_id},
            {"$set": {"reviews.$.content": content}}
        )
        
        self.db.users.update_one(
            {"_id": ObjectId(user_id), "reviews.item_id": str(item_id)},
            {"$set": {"reviews.$.content": content}}
        )

    def _create_new_review(self, item_id, user_id, username, content, item_name):
        item_review = {
            "user_id": user_id,
            "username": username,
            "content": content,
            "date": datetime.datetime.now()
        }
        
        user_review = {
            "item_id": str(item_id),
            "item_name": item_name,
            "content": content,
            "date": datetime.datetime.now()
        }

        self.db.items.update_one(
            {"_id": ObjectId(item_id)},
            {"$push": {"reviews": item_review}}
        )
        
        self.db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$push": {"reviews": user_review}}
        )