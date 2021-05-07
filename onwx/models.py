from datetime import datetime
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from onwx import db, login_manager, app
from flask_login import UserMixin

#getting the id decorator 
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

#user class declaration
class User(db.Model,UserMixin):
    #unique id for the user
    id = db.Column(db.Integer, primary_key=True)
    #unique username
    username= db.Column(db.String(20),unique=True, nullable=False)
    email= db.Column(db.String(120),unique=True, nullable=False)
    image_file= db.Column(db.String(20), nullable=False, default="default.jpg")
    password= db.Column(db.String(60), nullable=False)
    posts= db.relationship("Post",backref="author", lazy=True)
    #resetting the token if expired
    def get_reset_token(self,expires_sec=1800):
        s=Serializer(app.config["SECRET_KEY"], expires_sec)
        return s.dumps({"user_id": self.id}).decode('utf-8') 
    @staticmethod
    def verify_reset_token(token):
        s= Serializer(app.config["SECRET_KEY"])
        try:
            user_id= s.loads(token)["user_id"]
        except:
            return None   
        return User.query.get(user_id)     
    #this is a method that declares how our class is going to be printed out, for debbuging matters  
    def __repr__(self):
        return "user (%s,%s,%s) " % (self.username,self.email, self.image_file)

class Post(db.Model):
    #unique id for the user
    id= db.Column(db.Integer, primary_key=True)
    #name of the event
    title= db.Column(db.String(100), nullable=False)
    #when the event was posted 
    date_posted= db.Column(db.DateTime, nullable=False, default=datetime.now())
    #description of the event
    content= db.Column(db.Text, nullable=False)
    #start date and hour of the event 
    start_dh= db.Column(db.DateTime, nullable=False)
    #finish date and hour of the event 
    finish_dh= db.Column(db.DateTime, nullable=False)
    #image of the flyer for the post
    image_file= db.Column(db.String(20), nullable=False, default="default.jpg")
    #linking the  post table with the user
    user_id= db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    #relation with the ticket model
    ticket=db.relationship("Tickets", backref="event", lazy=True)
    #relation ship with the customer
    customer=db.relationship("Customer", backref="party", lazy=True)
    #this is a method that declares how our class is going to be printed out 
    def __repr__(self):
        return "%s,%s,%s,%s,%s" % (self.user_id,self.title,self.date_posted,self.content,self.image_file)

#data base for the tickets
class Tickets(db.Model):
    #unique id for the user
    id= db.Column(db.Integer, primary_key=True)
    #name or kind of the event, this is set by the creators
    ticket_type=db.Column(db.String(20), nullable=False)
    #initial stock of the ticket
    ticket_quantity=db.Column(db.Integer,nullable=False)
    #initial price of this kind of ticket
    price_ticket=db.Column(db.Integer, nullable=False)
    #start date and hour of the event 
    start_dh_tickets=db.Column(db.DateTime, nullable=False)
    #finish date and hour of the event 
    finish_dh_tickets=db.Column(db.DateTime, nullable=False)
    #id of the event we have a relationship with
    post_id= db.Column(db.Integer, db.ForeignKey("post.id"), nullable=True)
    #this is a method that declares how our class is going to be printed out 
    def __repr__(self):
        return "%s,%s,%s,%s,%s,%s,%s" % (self.id,self.post_id,self.ticket_type, self.ticket_quantity,self.price_ticket,self.start_dh_tickets,self.finish_dh_tickets)

#data base structure for the clients
class Customer(db.Model):
    id= db.Column(db.Integer, primary_key=True)
    #name of the client
    name= db.Column(db.String(40), nullable=False)
    #card number
    card_number= db.Column(db.Integer,nullable=False)
    #user email
    customer_email= db.Column(db.String(120),nullable=False)    
    #quantity of tickes bought by the customer
    number_tickets=db.Column(db.Integer,nullable=False)    
    #id of the kind ot ticket we have a relationship with
    post_id= db.Column(db.Integer, db.ForeignKey("post.id"), nullable=False)
    #this is a method that declares how our class is going to be printed out 
    def __repr__(self):
        return "%s,%s,%s" % (self.name,self.customer_email, self.number_tickets)
