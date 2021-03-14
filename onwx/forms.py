from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from flask_login import current_user
from wtforms import StringField,PasswordField,SubmitField,BooleanField,TextAreaField,DateTimeField,IntegerField,Form
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError,NumberRange
from onwx.models import User
import wtforms

class RegistrationForm(FlaskForm):
    username=StringField( 'Username',validators=[DataRequired(),Length(min=2, max=20)])
    email=StringField('Email', validators=[DataRequired(),Email()])                      
    password=PasswordField('Password', validators=[DataRequired()])
    confirm_password=PasswordField( 'Confirm Password',validators=[DataRequired(),EqualTo("password",message="this password must match the last one")])
    submit =SubmitField( 'Sign up')
    #this method checks if an user is already taken
    def validate_username(self, username):
        user=User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('this user is already taken')  
    #same method for the email
    def validate_email(self, email):
        email=User.query.filter_by(email=email.data).first()
        if email:
           raise ValidationError('this email is already taken')


class LoginForm(FlaskForm):
    email=StringField('Email', validators=[DataRequired(),Email()])                      
    password=PasswordField('Password', validators=[DataRequired()])
    remember=BooleanField('Remember me')
    submit=SubmitField('Log in')

class UpdateAccountForm(FlaskForm):
    username=StringField( 'Username',validators=[DataRequired(),Length(min=2, max=20)])
    email=StringField('Email', validators=[DataRequired(),Email()])
    picture=FileField("Update Profile Picture", validators=[FileAllowed(["jpg","png"])])                      
    submit =SubmitField( 'Update')
    
    #this method checks if an user is already taken
    def validate_username(self, username):
        if username.data != current_user.username:
           user=User.query.filter_by(username=username.data).first()
           if user:
                raise ValidationError('this user is already taken')      
    #same method for the email
    def validate_email(self, email):
        if email.data != current_user.email:
           user=User.query.filter_by(email=email.data).first()
           if user:
                raise ValidationError('this email is already taken')

    
class PostForm(FlaskForm):
    #name of the event
    title=StringField("Name of the event", validators=[DataRequired()])
    #event description
    content=TextAreaField("Description", validators=[DataRequired()])
    #starting date and hour of the event
    start_dh=DateTimeField("When your event it is gonna start",format='%Y-%m-%d %H:%M:%S',validators=[DataRequired()],render_kw={"placeholder":"year-month-day --:--:--"})
    #finish date of the event
    finish_dh=DateTimeField("When your event it is gonna finish",format='%Y-%m-%d %H:%M:%S',validators=[DataRequired()],render_kw={"placeholder":"year-month-day --:--:--"})
    #image required for each event
    image_file=FileField("Upload your flyer", validators=[FileAllowed(["jpg","png"])])
    #submit button form 
    submit_post=SubmitField("Create") 


class TicketForm(FlaskForm):
     #customized type/name of the ticket
    ticket_type=StringField("Name of the tickets", validators=[DataRequired()])
    #quantity of tickets for the given type
    ticket_quantity=IntegerField("Number of tickets", validators=[DataRequired()]) 
    #price of the tickets
    price_ticket=StringField("Price", validators=[DataRequired()]) 
    #starting date of the sales for that ticket  
    start_dh_tickets=DateTimeField("when are the tickets gonna start selling",format='%Y-%m-%d %H:%M:%S', validators=[DataRequired()],render_kw={"placeholder":"year-month-day --:--:--"})
    #closing ticket sales date 
    finish_dh_tickets=DateTimeField("when are the tickets gonna finish selling",format='%Y-%m-%d %H:%M:%S', validators=[DataRequired()],render_kw={"placeholder":"year-month-day --:--:--"})
    #submit button form 
    submit_ticket=SubmitField("Create")


class CustomerForm(FlaskForm):
    #name of the client
    name=StringField("Your name", validators=[DataRequired()])
    #email of the client
    customer_email=StringField('Email', validators=[DataRequired(),Email()])
    #credit card number
    card_number=IntegerField("Credit Card Number", validators=[DataRequired()])
    #number of tickets
    number_tickets=IntegerField("Number of tickets", validators=[NumberRange(min=1, max=2, message='2 tickets max')])
    #submit button form
    submit_customer=SubmitField("Buy")

#request th resetting your password form
class RequestResetForm(FlaskForm):
     email=StringField('Email', validators=[DataRequired(),Email()])  
     submit =SubmitField( 'Request password reset')    

     def validate_username(self, username):
        user=User.query.filter_by(username=username.data).first()
        if user is None:
            raise ValidationError('You must register first')
  
#reset you password
class ResetPasswordForm(FlaskForm):
    password=PasswordField('Password', validators=[DataRequired()])
    confirm_password=PasswordField( 'Confirm Password',validators=[DataRequired(),EqualTo("password",message="this password must match the last one")])
    submit =SubmitField('Reset password')

