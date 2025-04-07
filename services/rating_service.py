from bson.objectid import ObjectId
import datetime

class RatingService:
    def __init__(self, db):
        self.db = db

    def rate_item(self, item_id, user_id, username, rating):
        try:
            if rating < 1 or rating > 10:
                return False, "Rating must be between 1 and 10"

            item = self.db.items.find_one({"_id": ObjectId(item_id)})
            if not item:
                return False, "Item not found"

            existing_review = None
            for review in item.get('reviews', []):
                if review.get('user_id') == user_id:
                    existing_review = review
                    break

            if existing_review:
                self._update_existing_rating(item_id, user_id, rating)
            else:
                self._create_new_rating(item_id, user_id, username, rating, item['name'])

            self._update_item_rating_stats(item_id)
            self._update_user_rating_stats(user_id)

            return True, "Rating submitted successfully"

        except Exception as e:
            return False, f"Error submitting rating: {str(e)}"
    def revoke_rating(self, item_id, user_id):
        item = self.db.items.find_one({
            "_id": ObjectId(item_id),
            "reviews": {
                "$elemMatch": {
                    "user_id": user_id,
                    "rating": {"$exists": True},
                    "content": {"$exists": False}
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
                            "rating": {"$exists": True}
                        }
                    }
                },
                {"$unset": {"reviews.$.rating": ""}}
            )
            
            self.db.users.update_one(
                {
                    "_id": ObjectId(user_id),
                    "reviews": {
                        "$elemMatch": {
                            "item_id": str(item_id),
                            "rating": {"$exists": True}
                        }
                    }
                },
                {"$unset": {"reviews.$.rating": ""}}
            )
        
        self._update_item_rating_stats(item_id)
        self._update_user_rating_stats(user_id)
        
        return True, "Rating successfully revoked"
            
    def _update_existing_rating(self, item_id, user_id, rating):
        self.db.items.update_one(
            {"_id": ObjectId(item_id), "reviews.user_id": user_id},
            {"$set": {"reviews.$.rating": rating}}
        )
        
        self.db.users.update_one(
            {"_id": ObjectId(user_id), "reviews.item_id": str(item_id)},
            {"$set": {"reviews.$.rating": rating}}
        )

    def _create_new_rating(self, item_id, user_id, username, rating, item_name):
        item_review = {
            "user_id": user_id,
            "username": username,
            "rating": rating,
            "date": datetime.datetime.now()
        }
        
        user_review = {
            "item_id": str(item_id),
            "item_name": item_name,
            "rating": rating,
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

    def _update_item_rating_stats(self, item_id):
        item = self.db.items.find_one({"_id": ObjectId(item_id)})
        ratings = [r.get('rating', 0) for r in item.get('reviews', []) if 'rating' in r]
        
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
                {
                    "$set": {
                        "rating": 0,
                        "number_of_reviewers": 0
                    }
                }
            )

    def _update_user_rating_stats(self, user_id):
        user = self.db.users.find_one({"_id": ObjectId(user_id)})
        ratings = [r.get('rating', 0) for r in user.get('reviews', []) if 'rating' in r]
        
        if ratings:
            user_avg_rating = sum(ratings) / len(ratings)
            self.db.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"average_rating": round(user_avg_rating, 1)}}
            )
        
        else:
            self.db.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"average_rating": 0}}
            )