import firebase_admin
import pyrebase
import json
from firebase_admin import credentials, auth
from flask import Flask, request,render_template,flash, redirect
import forms
from forms import LoginForm
# from flask_login import LoginManager


#App configuration
app = Flask(__name__)
# login = LoginManager(app)

app.config['SECRET_KEY'] = 'you-will-never-guess'

#Connect to firebase
cred = credentials.Certificate('fbadmin.json')
firebase = firebase_admin.initialize_app(cred)
pb = pyrebase.initialize_app(json.load(open('fbconfig.json')))

auth = pb.auth()

#Api route to get a new token for a valid user
@app.route('/', methods=['GET', 'POST'])
# def main():
#     return "works"
def login():
    form = LoginForm()
    if form.validate_on_submit():

        email = form.email.data
        password = form.password.data
        try:
            user = auth.sign_in_with_email_and_password(email, password)
            return redirect('/dashboard')
        except:
            return "Invalid Credentials. Please try again"

    return render_template('login.html', title='Sign In', form=form)

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard_home.html')

if __name__ == '__main__':
    app.run(debug=True)
