import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt 
from flask_login import LoginManager
from flask_mail import Mail

app= Flask(__name__)
app.config["SECRET_KEY"]= "87489890agf"
#CONFIGURATION OF THE SQL DATA BASE 
app.config["SQLALCHEMY_DATABASE_URI"]="sqlite:///site.db"
#sqlalchemy instance
db = SQLAlchemy(app)
#encryption
bcrypt=Bcrypt(app)
#log in manager 
login_manager=LoginManager(app)
#
login_manager.login_message_category= "info"
#
app.config["MAIL_SERVER"]="smtp.googlemail.com"
app.config["MAIL_PORT"]=587
app.config["MAIL_USE_TLS"]=True
app.config["MAIL_USERNAME"]="onwaxcomm@gmail.com"
app.config["MAIL_PASSWORD"]="libernacus"
mail=Mail(app)

import routes