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

@app.route("/")
@app.route("/home")
def home():
    page=request.args.get("page",1, type=int)
    
    posts=Post.query.order_by(Post.date_posted.desc()).paginate(page=page,per_page=5)
    return render_template("home.html",posts=posts)


@app.route("/register", methods=["GET","POST"])
def register():
    #this redirects to home if the user is already logged in
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
        #flash message for succesful creation of users
        flash("account created","success")
        #redirects to the login page after the creation 
        return redirect(url_for("login")) 
    return render_template("register.html",title="Register", form=form)

@app.route("/login", methods=["GET","POST"])
def login():
    #this redirects to home if the user is already logged in
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    form= LoginForm()
    if form.validate_on_submit():
          #checking if the user exists
          user = User.query.filter_by(email=form.email.data).first()
          #checking if the user is correlated with the inserted password
          if user and bcrypt.check_password_hash(user.password,form.password.data):
             login_user(user,remember=form.remember.data)
             flash("logged in","success")
             return redirect(url_for("account"))
          else:   
              flash("failed log in", "danger" )   
    return render_template("login.html",title="Login", form=form)

@app.route("/logout")  
def logout():
    logout_user()
    return redirect(url_for("home"))

@app.route("/account",methods=["GET","POST"])
@login_required
def account():
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
     #form_picture.save(picture_path)
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

@app.route("/post/new",methods=["GET","POST"])  
@login_required
def new_post(): 
    #event forms
    post_form=PostForm()
    #valdiating the submission of those forms
    if post_form.validate_on_submit():
        if post_form.image_file.data:
            picture_file=save_picture(post_form.image_file.data)
        #loading to our database
        post=Post(title=post_form.title.data,content=post_form.content.data,start_dh=post_form.start_dh.data,
                   finish_dh=post_form.finish_dh.data,image_file=picture_file,author=current_user)                    
        db.session.add(post)
        db.session.commit()   
        flash("create your tickets now", "success")        
        return redirect(url_for("tickets", post_id=post.id))
    return render_template("create_post.html",title="new post",post_form=post_form,legend="New Event")

#create new tickets
@app.route("/ticket/<int:post_id>",methods=["GET","POST"])  
@login_required
def tickets(post_id):
    post=Post.query.get_or_404(post_id)
    ticket_form=TicketForm() 
    #this variable give us the id of the last post that this user posted
    post_relation=Post.query.filter_by(user_id=current_user.id).order_by(Post.date_posted.desc()).first()
    #submission

    if  ticket_form.validate_on_submit(): 
        tickets=Tickets(ticket_type=ticket_form.ticket_type.data,ticket_quantity=ticket_form.ticket_quantity.data,
                         price_ticket=ticket_form.price_ticket.data, start_dh_tickets=ticket_form.start_dh_tickets.data,
                         finish_dh_tickets=ticket_form.finish_dh_tickets.data,event=post_relation)  
        db.session.add(tickets)
        db.session.commit() 
        flash("your tickets have been created","success")
        return redirect(url_for("tickets",post_id=post.id))  
    tick=Tickets.query.order_by(Tickets.post_id)   
    return render_template("create_ticket.html",title="tickets",ticket_form=ticket_form,tick=tick,post_id=post.id)        
                
@app.route("/event")
def event():
    post_form=PostForm()
    ticket_form=TicketForm()
    return render_template("event.html", title="event", post_form=post_form,ticket_form=ticket_form)

@app.route("/postevent")
def post_event():
    flash("you just posted your event", "success")
    page=request.args.get("page",1, type=int)
    posts=Post.query.order_by(Post.date_posted.desc()).paginate(page=page,per_page=5)
    return render_template("home.html", posts=posts)

@app.route("/post/<int:post_id>",methods=["GET","POST"])
def post(post_id):
    post=Post.query.get_or_404(post_id)
    today=datetime.now()
    return render_template("post.html",title=post.title, post=post,today=today)

#update post info
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
   print "the name of the ticket is %s" % (str(name))
   ticket_form=TicketForm()
   #ticket=Tickets.query.filter_by(id=post_id).first()
   #quantity=Tickets.query.filter(Tickets.post_id==post_id).first()
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

#name of the ticket you want to update
@app.route("/post/<int:post_id>/name",methods=["GET","POST"])
@login_required
def name_update(post_id):
   post=Post.query.get_or_404(post_id)
   form= RegistrationForm()
   if request.method=="POST":
      unicode_name=request.form["nm"]
      name=unicode_name.encode('utf8')
      try:
         a=Tickets.query.filter(Tickets.post_id==post_id).filter(Tickets.ticket_type==name).first()
         if name==a.ticket_type:
             return redirect(url_for('update_tickets',post_id=post.id,name=name))
      except:
          flash("there is no ticket with that name","danger")
          return render_template("name_update.html")          
   else:        
      return render_template("name_update.html")
   

#delete    
@app.route("/post/<int:post_id>/delete",methods=["POST"])
@login_required
def delete_post(post_id):
    post=Post.query.get_or_404(post_id)
    ticket=Tickets.query.filter_by(id=post_id).first()
    if post.author != current_user:
       abort(403)
    db.session.delete(post)
    db.session.delete(ticket)
    db.session.commit()
    flash("your post has been deleted","success")
    return redirect(url_for("home"))

#create ticket route
@app.route("/ticket",methods=["POST"])
@login_required
def create_ticket():
    return redirect(url_for("ticket"))


@app.route("/post/<int:post_id>/customer",methods=["GET","POST"])
def customer(post_id):
    #getting the post for the given id
    post=Post.query.get_or_404(post_id)
    #accessing the postform
    postform=PostForm()
    #accessing the customer form
    customer=CustomerForm()
    #accessing the ticket form
    ticket=TicketForm()

    quantity=Tickets.query.filter(Tickets.start_dh_tickets<=datetime.now()).filter(Tickets.post_id==post_id).filter(datetime.now()<=Tickets.finish_dh_tickets).first()


    update=quantity.ticket_quantity
    #getting the tickets to subtract the purchased by the customer
    #we want to subtract the tickets that the customer bought and store the info in the customer db
    if update<=2:
        flash("only (%s) tickets left" % (update) , "danger")
    if  customer.validate_on_submit(): 
            #send email with qr code 
            purchase=Customer(name=customer.name.data,card_number=customer.card_number.data,customer_email=customer.customer_email.data,
                              number_tickets=customer.number_tickets.data,party=post)  
            db.session.add(purchase) 
            #actualization of the ticket database
            #getting the customer
            get_cust=Customer.query.get(post_id)
            #subtract the purchased tickets to the stock of the tickets
            subtract=update-get_cust.number_tickets
            #insert the subtract_tickets number to the Tickets db 
            quantity.ticket_quantity=subtract
            db.session.commit()    
            #variable with the qrcode
            #image="/Users/maverb/Documents/la.png"
            #qr code generator
            string="234"
            url=pyqrcode.create(string)
            url.png("/Users/maverb/Documents/la.jpg", scale=8)
            #user data
            EMAIL_ADDRESS= "onwaxcomm@gmail.com"
            EMAIL_PASSWORD="libernacus"
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
            msg["Subject"]=subject  #ver como formatear
            msg["From"]=formataddr((sender_name,address))     #ver como usar el formataddr
            msg["To"]=formataddr((reciver_name,reciver))
            msg.attach(MIMEText(body,"plain"))
            try:
                img=file("/Users/maverb/Documents/la.jpg")
                p=MIMEBase('image',"jpeg")
                p.set_payload(img.read())
                #encode file in ASCII characers to send by Email
                encoders.encode_base64(p)
                p.add_header('image',"img")
                msg.attach(p)
            except Exception as e:
                print "we did not found the photo"
            text=msg.as_string()

            try:
                EMAIL_ADDRESS= "onwaxcomm@gmail.com"
                EMAIL_PASSWORD="libernacus"
                smtp=smtplib.SMTP("smtp.gmail.com",587)
                smtp.ehlo() #check the email
                smtp.starttls() #encrypts our information
                smtp.ehlo() #reidentify our selves as encrypted connections
                smtp.login(address,EMAIL_PASSWORD)
                #msg= "Subject: {} \n\n {}" .format(subject,body)
                smtp.sendmail(EMAIL_ADDRESS, reciver, text)
                print "mail sended succesfully"
                smtp.close()
            except:
                print("mail not delivered")
            flash("successfuly bought your tickets, check your email","success")
            return redirect(url_for("home")) 
    return render_template("customer.html",postform=postform,customer=customer,ticket=ticket)   


def send_reset_email(user):
    token=user.get_reset_token()
    msg=Message("Password Reset Request", 
                 sender="onwaxcomm@gmail.com",
                 recipients=[user.email])
    msg.body=" Reset your password here (%s)" % {url_for("reset_token",token=token,_external=True)}             
    mail.send(msg)

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
        #flash message for succesful creation of users
        flash("your password has been updated","success")
        #redirects to the login page after the creation 
        return redirect(url_for("login")) 
    return render_template("reset_token.html",title="Reset Password",form=form)    
    
@app.route("/unloaded", methods=["GET","POST"])
def unloaded():
  print("unloaded tickets")
  get_postid=request.form
  print(rf)
  for key in get_postid.keys():
     postid=key
  print(data)
  postid_dic=json.loads(postid)
  print(postid_dic.keys())
  postid_data = data_dic["unloaded"]
 
     



        