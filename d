[1mdiff --git a/blueprints/messaging.py b/blueprints/messaging.py[m
[1mindex b53f760..d644dce 100644[m
[1m--- a/blueprints/messaging.py[m
[1m+++ b/blueprints/messaging.py[m
[36m@@ -9,7 +9,7 @@[m [mfrom flask import ([m
 from database import db[m
 from database.models import MessagePreset, UserProfile, DataStorage, ActionQueue, DMMessage[m
 from dhooks import Webhook, Embed[m
[31m-from helper.perms import require_role_management[m
[32m+[m[32mfrom helper.perms import require_role_management, require_support_permission[m[41m[m
 from requests import HTTPError[m
 [m
 import json[m
[36m@@ -25,7 +25,7 @@[m [mmessaging_bp = Blueprint([m
 # PAGE[m
 # ---------------------------------------------------[m
 @messaging_bp.get("/")[m
[31m-@require_role_management[m
[32m+[m[32m@require_support_permission[m[41m[m
 def messaging_page():[m
     # Nutzerliste aus DB[m
     users = UserProfile.query.order_by(UserProfile.username).all()[m
[36m@@ -36,6 +36,7 @@[m [mdef messaging_page():[m
 [m
 [m
 @messaging_bp.get("/api/messages")[m
[32m+[m[32m@require_support_permission[m[41m[m
 def get_messages():[m
     msgs = DMMessage.query.all()[m
     return jsonify([x.as_dict() for x in msgs])[m
[36m@@ -44,14 +45,14 @@[m [mdef get_messages():[m
 # PRESETS – API[m
 # ---------------------------------------------------[m
 @messaging_bp.get("/api/presets")[m
[31m-@require_role_management[m
[32m+[m[32m@require_support_permission[m[41m[m
 def get_presets():[m
     p = MessagePreset.query.all()[m
     return jsonify([x.as_dict() for x in p])[m
 [m
 [m
 @messaging_bp.post("/api/presets")[m
[31m-@require_role_management[m
[32m+[m[32m@require_support_permission[m[41m[m
 def add_preset():[m
     data = request.json[m
     p = MessagePreset([m
[36m@@ -65,7 +66,7 @@[m [mdef add_preset():[m
 [m
 [m
 @messaging_bp.put("/api/presets/<int:id>")[m
[31m-@require_role_management[m
[32m+[m[32m@require_support_permission[m[41m[m
 def update_preset(id):[m
     p = MessagePreset.query.get(id)[m
     data = request.json[m
[36m@@ -79,7 +80,7 @@[m [mdef update_preset(id):[m
 [m
 [m
 @messaging_bp.delete("/api/presets/<int:id>")[m
[31m-@require_role_management[m
[32m+[m[32m@require_support_permission[m[41m[m
 def delete_preset(id):[m
     p = MessagePreset.query.get(id)[m
     db.session.delete(p)[m
[36m@@ -91,7 +92,7 @@[m [mdef delete_preset(id):[m
 # SENDEN – API[m
 # ---------------------------------------------------[m
 @messaging_bp.post("/api/send/announcement")[m
[31m-@require_role_management[m
[32m+[m[32m@require_support_permission[m[41m[m
 def send_announcement():[m
     text = request.json["text"][m
     user_announcement_hook_url = DataStorage.query.filter_by(key="hooks.announcement_hook_url").first()[m
[36m@@ -112,7 +113,7 @@[m [mdef send_announcement():[m
 [m
 [m
 @messaging_bp.post("/api/send/user")[m
[31m-@require_role_management[m
[32m+[m[32m@require_support_permission[m[41m[m
 def send_user():[m
 [m
     data = request.get_json() or {}[m
[1mdiff --git a/helper/perms.py b/helper/perms.py[m
[1mindex f521b10..a5efd5d 100644[m
[1m--- a/helper/perms.py[m
[1m+++ b/helper/perms.py[m
[36m@@ -41,3 +41,12 @@[m [mdef require_admin_permission(fn):[m
         return fn(*args, **kwargs)[m
     return wrapper[m
 [m
[32m+[m[32mdef require_support_permission(fn):[m[41m[m
[32m+[m[32m    @wraps(fn)[m[41m[m
[32m+[m[32m    def wrapper(*args, **kwargs):[m[41m[m
[32m+[m[32m        if not session.get("is_supporter", False):[m[41m[m
[32m+[m[41m[m
[32m+[m[32m            # return jsonify({"error": "Nicht autorisiert"}), 403[m[41m[m
[32m+[m[32m            return redirect(url_for("index"))[m[41m[m
[32m+[m[32m        return fn(*args, **kwargs)[m[41m[m
[32m+[m[32m    return wrapper[m[41m[m
