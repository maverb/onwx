import os
import random
from flask import render_template,url_for, redirect, flash,request,abort,jsonify,request 
from onwx import app,db,bcrypt,mail
from onwx.forms import (RegistrationForm,LoginForm,UpdateAccountForm,PostForm,TicketForm,
                        CustomerForm,DateTimeField,RequestResetForm,ResetPasswordForm)
from onwx.models import User,Post,Tickets,Customer
from flask_login import login_user,current_user,logout_user, login_required
from flask_mail import Message
import pyqrcode 
import smtplib
from PIL import Image
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.base import MIMEBase
from email import encoders
from email.utils import formataddr
from datetime import datetime
import json 

#a route to show all the available tickets created in the platform
@app.route("/")
def home():
    page=request.args.get("page",1, type=int)
    posts=Post.query.order_by(Post.date_posted.desc()).paginate(page=page,per_page=5)
    return render_template("home.html",posts=posts)

#just a regular register page 
@app.route("/register", methods=["GET","POST"])
def register():
    #this redirects to the homepage 
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    #validating the submission     
    form= RegistrationForm()
    if form.validate_on_submit():
        #encrypting the password
        hashed_password= bcrypt.generate_password_hash(form.password.data).decode("utf_8")
        #creating the general User instance
        user=User(username=form.username.data, email=form.email.data, password=hashed_password)        
        #adding the user to the database
        db.session.add(user)
        db.session.commit()
        flash("account created","success")
        #redirects to the log in page after the creation 
        return redirect(url_for("login")) 
    return render_template("register.html",title="Register", form=form)

#just a regular log in page 
@app.route("/login", methods=["GET","POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    form= LoginForm()
    if form.validate_on_submit():
          #checking if the user already exists
          user = User.query.filter_by(email=form.email.data).first()
          #checking if the user is correlated with the inserted password
          if user and bcrypt.check_password_hash(user.password,form.password.data):
             login_user(user,remember=form.remember.data)
             return redirect(url_for("account"))
          else:   
              flash("failed log in", "danger" )   
    return render_template("login.html",title="Login", form=form)

#just a regular log out route
@app.route("/logout")  
def logout():
    logout_user()
    return redirect(url_for("home"))

#route that permits you update the information of the user 
@app.route("/account",methods=["GET","POST"])
@login_required
def account():
    #validating the actualization of the data 
    form=UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file=save_picture(form.picture.data)
            image_file=picture_file
            current_user.username=form.username.data 
            current_user.email=form.email.data 
            db.session.commit()
            flash("your account has been updated","success")
            return redirect(url_for("account"))
    elif request.method == "GET":
           form.username.data=current_user.username
           form.email.data= current_user.email   
    
    posts=Post.query.filter_by(author=current_user).order_by(Post.date_posted.desc())
    return render_template("account.html",title="account", form=form, posts=posts)
    
#function that saves the picture
def save_picture(form_picture):
     random_hex= random.randint(1,100)
     f_name, f_ext= os.path.splitext(form_picture.filename)
     picture_fn = str(random_hex) + f_ext
     picture_path = os.path.join(app.root_path,"static/event_pics",picture_fn)
     output_size=(729,729)
     i=Image.open(form_picture)
     i.thumbnail(output_size)
     i.save(picture_path)
     return picture_fn

#route containing the update account form
@app.route("/update",methods=["GET","POST"])
@login_required
def update():
    form=UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file=save_picture(form.picture.data)
            image_file=picture_file
            current_user.username=form.username.data 
            current_user.email=form.email.data 
            current_user.picture=image_file
            db.session.commit()
            flash("your account has been updated","success")
            return redirect(url_for("account"))
    elif request.method == "GET":
        form.username.data=current_user.username
        form.email.data= current_user.email    
    image_file= url_for("static", filename ="profile_pics/" + current_user.image_file)
    return render_template("update.html",title="Update", image_file=image_file, form=form)
    

 #route for creating a new post 

#route that handles the creation of a new event
@app.route("/post/new",methods=["GET","POST"])  
@login_required
def new_post(): 
    post_form=PostForm()
    #valdating the submission of those forms
    if post_form.validate_on_submit():
        if post_form.image_file.data:
            picture_file=save_picture(post_form.image_file.data)
        #inserting and saving the data
        post=Post(title=post_form.title.data,content=post_form.content.data,start_dh=post_form.start_dh.data,
                   finish_dh=post_form.finish_dh.data,image_file=picture_file,author=current_user)                    
        db.session.add(post)
        db.session.commit()   
        flash("create your tickets now", "success")        
        return redirect(url_for("tickets", post_id=post.id))
    return render_template("create_post.html",title="new post",post_form=post_form,legend="New Event")

#route that handles the tickets creation of the new event(2 steps creation)
@app.route("/ticket/<int:post_id>",methods=["GET","POST"])  
@login_required
def tickets(post_id):
    post=Post.query.get_or_404(post_id)
    ticket_form=TicketForm() 
    #validating the submission of the tickets
    if  ticket_form.validate_on_submit(): 
        #insterting adn saving the new tickets
        tickets=Tickets(ticket_type=ticket_form.ticket_type.data,ticket_quantity=ticket_form.ticket_quantity.data,
                         price_ticket=ticket_form.price_ticket.data, start_dh_tickets=ticket_form.start_dh_tickets.data,
                         finish_dh_tickets=ticket_form.finish_dh_tickets.data,event=post)  
        db.session.add(tickets)
        db.session.commit() 
        flash("your tickets have been created","success")
        #it redirects to the tickets as the user could want to create more than one type of tickets
        return redirect(url_for("tickets",post_id=post.id))  
    tick=Tickets.query.order_by(Tickets.post_id)   
    return render_template("create_ticket.html",title="tickets",ticket_form=ticket_form,tick=tick,post_id=post.id)        


#route that handles the confirmation of the creation of the event and tickets
@app.route("/postevent")
def post_event():
    flash("you just posted your event", "success")
    page=request.args.get("page",1, type=int)
    posts=Post.query.order_by(Post.date_posted.desc()).paginate(page=page,per_page=5)
    return render_template("home.html", posts=posts)

#information and purchase option of the event 
@app.route("/post/<int:post_id>",methods=["GET","POST"])
def post(post_id):
    post=Post.query.get_or_404(post_id)
    #we pass the day to know if the tickets started selling already
    today=datetime.now()
    return render_template("post.html",title=post.title, post=post,today=today)

#route that let the user update the information of the created events
@app.route("/post/<int:post_id>/update",methods=["GET","POST"])
@login_required
def update_post(post_id):
   post=Post.query.get_or_404(post_id)
   #update and validate post 
   if post.author != current_user:
       abort(403)
   post_form = PostForm()   
   if post_form.validate_on_submit():
       if post_form.image_file.data:
            picture_file=save_picture(post_form.image_file.data)
            post.title=post_form.title.data
            post.content=post_form.content.data
            post.start_dh=post_form.start_dh.data
            post.finish_dh=post_form.finish_dh.data
            post.image_file=picture_file
            db.session.commit()    
            flash("Post updated","success")
            return redirect(url_for("post", post_id=post.id))
   elif request.method=="GET":    
       post_form.title.data=post.title
       post_form.content.data=post.content
       post_form.start_dh.data =post.start_dh
       post_form.finish_dh.data =post.finish_dh
   return render_template("create_post.html",title="update post",post_form=post_form, legend="Update Post")    

#update ticket info
@app.route("/post/<int:post_id>/name/<name>",methods=["GET","POST"])
@login_required
def update_tickets(post_id,name):
   post=Post.query.get_or_404(post_id)
   ticket_form=TicketForm()
   ticket=Tickets.query.filter(Tickets.post_id==post_id).filter(Tickets.ticket_type==str(name)).first()
   #update and validate tickets     
   if ticket_form.validate_on_submit():
       ticket.ticket_type=ticket_form.ticket_type.data
       ticket.ticket_quantity=ticket_form.ticket_quantity.data
       ticket.price_ticket=ticket_form.price_ticket.data
       ticket.start_dh_tickets=ticket_form.start_dh_tickets.data
       ticket.finish_dh_tickets=ticket_form.finish_dh_tickets.data
       db.session.commit()    
       flash("Post updated","success")
       return redirect(url_for("post", post_id=post.id))
   elif request.method=="GET":    
       ticket_form.ticket_type.data=ticket.ticket_type
       ticket_form.ticket_quantity.data=ticket.ticket_quantity
       ticket_form.price_ticket.data=ticket.price_ticket
       ticket_form.start_dh_tickets.data=ticket.start_dh_tickets
       ticket_form.finish_dh_tickets.data=ticket.finish_dh_tickets
   return render_template("update_ticket.html",title="update tickets",ticket_form=ticket_form, legend="Update Tickets") 

#view name of the ticket you want to update, we ask to the user which is the kind
#of ticket to be updated
@app.route("/post/<int:post_id>/name",methods=["GET","POST"])
@login_required
def name_update(post_id):
   post=Post.query.get_or_404(post_id)
   form=RegistrationForm()
   if request.method=="POST":
      name=request.form["nm"]
      try:
         ticket_check=Tickets.query.filter(Tickets.post_id==post_id).filter(Tickets.ticket_type==name).first()
         if name==ticket_check.ticket_type:
             return redirect(url_for('update_tickets',post_id=post.id,name=name))
      except:
          flash('there is no ticket with that name','danger')
          return render_template("name_update.html")          
   else:        
      return render_template("name_update.html")
   
#delete the posted event     
@app.route("/post/<int:post_id>/delete",methods=["POST"])
@login_required
def delete_post(post_id):
    post=Post.query.get_or_404(post_id)
    tickets=Tickets.query.filter_by(id=post_id).all()      
    for ticket in tickets:
        db.session.delete(ticket)    
    db.session.delete(post)
    db.session.commit()
    flash("your post has been deleted","success") 
    return redirect(url_for("home"))

#create ticket route
@app.route("/ticket",methods=["POST"])
@login_required
def create_ticket():
    return redirect(url_for("ticket"))

#this is the route that handle the purchase of the tickets
@app.route("/post/<int:post_id>/customer",methods=["GET","POST"])
def customer(post_id):
    #getting the post id
    post=Post.query.get_or_404(post_id)
    #accessing the needed forms 
    postform=PostForm()
    customer=CustomerForm()
    ticket=TicketForm()
    #querying the tickets that are available at that exact moment
    quantity=Tickets.query.filter(Tickets.start_dh_tickets<=datetime.now()).filter(Tickets.post_id==post_id).filter(datetime.now()<=Tickets.finish_dh_tickets).first()
    #update variable is the quantity of tickets that the customer wants to buy
    update=quantity.ticket_quantity
    #we want to subtract the tickets that the customer bought and store the info in the customer db
    if update<=2:
        flash("only (%s) tickets left" % (update) , "danger")
    if  customer.validate_on_submit(): 
            #addind and commiting the purchase to the database
            purchase=Customer(name=customer.name.data,card_number=customer.card_number.data,customer_email=customer.customer_email.data,
                                number_tickets=customer.number_tickets.data,party=post)  
            db.session.add(purchase) 
            db.session.commit() 
            #subtracting the purchased tickets to the stock of the tickets
            subtract=update-customer.number_tickets.data
            #updating the database
            quantity.ticket_quantity=subtract
            db.session.commit()    
            #qr code generator, it sends you the ticket via e-mail(not available in the github version)
            string="234"
            url=pyqrcode.create(string)
            url.png("/Users/maverb/Documents/qrcode/la.jpg", scale=8)
            #my e-mail data
            EMAIL_ADDRESS= "onwaxcomm@gmail.com"
            EMAIL_PASSWORD="lalala"
            #reciver data
            EMAIL_RECEIVER=customer.customer_email.data
            #cofigurating the email information
            address="onwaxcomm@gmail.com"
            reciver=customer.customer_email.data
            #sender and reciver mails for concatenation
            sender_name= "onwax"
            reciver_name= customer.name.data
            #this established a multipart and the other info of the email
            body="thanks for buying our tickets, have a nice party"
            subject="tickets"
            msg= MIMEMultipart()
            msg["Subject"]=subject 
            msg["From"]=formataddr((sender_name,address))    
            msg["To"]=formataddr((reciver_name,reciver))
            msg.attach(MIMEText(body,"plain"))
            #loading the generated qr code
            try:
                img="/Users/maverb/Documents/qrcode/la.jpg"
                read_img=open(img,"rb")
                p=MIMEBase("application",'octet-stream')
                p.set_payload((read_img).read())
                #encode file in ASCII characers to send by Email
                encoders.encode_base64(p)
                p.add_header('Content-Disposition','attachment',filename=img)
                msg.attach(p)
            except Exception as e:
                print("we did not found")
            text=msg.as_string()
            #sending the e-mail
            try:
                smtp=smtplib.SMTP("smtp.gmail.com",587)
                smtp.ehlo() #checks the email
                smtp.starttls() #encrypts our information
                smtp.ehlo() #reidentify our selves as encrypted connections
                smtp.login(address,EMAIL_PASSWORD)
                smtp.sendmail(EMAIL_ADDRESS, reciver, text)
                smtp.close()
            except:
                pass
            flash("successfuly bought your tickets, check your email ","success")
            return redirect(url_for("home")) 
    return render_template("customer.html",postform=postform,customer=customer,ticket=ticket)   

#sending the e-mail to reset the user information
def send_reset_email(user):
    token=user.get_reset_token()
    msg=Message("Password Reset Request", 
                 sender="onwaxcomm@gmail.com",
                 recipients=[user.email])
    msg.body=" Reset your password here (%s)" % {url_for("reset_token",token=token,_external=True)}             
    mail.send(msg)

#requesting the e-mail to reset the password
@app.route("/reset_password",methods=["GET","POST"])  
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    form=RequestResetForm()
    if form.validate_on_submit():
       user=User.query.filter_by(email=form.email.data).first()
       if user is None:
           flash("error,try again" , "danger")
       else:    
           send_reset_email(user)
           flash("An email has been sent with the instructions to reset your password", "info")
           return redirect(url_for("login"))   
    return render_template("reset_request.html",title="Reset Password",form=form)

#creating the token for resetting the password
@app.route("/reset_password/<token>",methods=["GET","POST"])  
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    user=User.verify_reset_token(token) 
    if user is None:
        flash("that is an expired token", "warning")   
        return redirect(url_for("reset_request"))
    form=ResetPasswordForm()
    if form.validate_on_submit():
        #encrypting the password
        hashed_password= bcrypt.generate_password_hash(form.password.data).decode('utf-8')      
        user.password=hashed_password
        db.session.commit()
        flash("your password has been updated","success")
        #redirects to the login page after the creation 
        return redirect(url_for("login")) 
    return render_template("reset_token.html",title="Reset Password",form=form)    
    
@app.route("/unloaded", methods=["GET","POST"])
def unloaded():
  get_postid=request.form
  for key in get_postid.keys():
     postid=key
  postid_dic=json.loads(postid)
  postid_data = data_dic["unloaded"]
 
     



        
