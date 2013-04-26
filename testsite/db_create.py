#!/usr/bin/python
from app import db
from app.models import User
import os.path
db.create_all()
admin = User()
admin.username = 'admin'
db.session.add(admin)
db.session.commit()
