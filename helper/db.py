from flask import session
from database import db
from database.models import (
    UserProfile

)
from .perms import has_license


def get_user_profile_from_session():
    user = UserProfile.query.filter_by(
            user_id=session["user"]["id"]).first()
    if user: 
        return user
    else:
        return None 
    
def reload_user_permission(user: UserProfile):
            session["is_trainer"] = has_license(
            user, "Ausbilder")
            session["is_supporter"] = has_license(
            user, "Supporter")
            session["is_admin"] = has_license(
            user, "Leitung")

