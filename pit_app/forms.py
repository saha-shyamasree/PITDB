from flask import Flask
from wtforms import Form, TextField, PasswordField, SelectField, TextAreaField, SubmitField # BooleanField
from wtforms.validators import Required, Email, EqualTo
# from flask_wtf import Form
# from pit_app.models import User

# class LoginForm(Form):
#   email    = TextField('Email Address', [Email(), Required(message='Forgot your email address?')])
#   password = PasswordField('Password',  [ Required(message='Must provide a password.')])

# class SignupForm(Form):
#   fullname  = TextField("Full name",    [Required("Please enter your first name.")])
#   email     = TextField("Email",        [
#   	Required("Please enter your email address."), 
#   	Email("Please enter your email address.")
#   ])
#   password  = PasswordField('New Password', [
#     Required("Please enter a password."),
#     EqualTo('password2', message='Passwords must match')
#   ])
#   password2 = PasswordField('Repeat Password')
#   submit    = SubmitField("Create account")
 
#   def __init__(self, *args, **kwargs):
#     Form.__init__(self, *args, **kwargs)
 
#   def validate(self):
#     if not Form.validate(self):
#       return False
     
#     user = User.query.filter_by(email = self.email.data.lower()).first()

#     if user:
#       self.email.errors.append("That email is already taken")
#       return False
#     else:
#       return True

class SearchForm(Form):
  searchOptions = SelectField('searchOptions', [Required(message='You need to select a search field')])
  searchArea    = TextAreaField('searchArea',  [Required(message='You need to import a search value')])


