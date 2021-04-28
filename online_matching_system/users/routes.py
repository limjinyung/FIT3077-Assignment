from flask import render_template, url_for, flash, redirect, request, Blueprint
from .utils import login, logout, user_subject, user_profile_details
from flask_login import current_user
from flask import session
from decouple import config
import requests

users = Blueprint('users', __name__)

root_url = 'https://fit3077.com/api/v1'
users_url = root_url + "/user"
subjects_url = root_url + "/subject"
users_login_url = users_url + "/login"
verify_token_url = users_url + "/verify-token"

@users.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
       
        # get data from form
        username = form.username.data
        password = form.password.data
        # log in user
        result = login(username, password)

        if result.status_code == 200:

            json_data = result.json()
            jwt = json_data['jwt']

            # redirect to another and save the JWT in cookies
            response = make_response(redirect('/'))
            session['jwt'] = jwt
            # response.set_cookie('access_token', jwt, httponly=True)
            return response

        else:
            # flash error message
            flash('Login Unsuccessful. Please check email and password', 'danger')

    return render_template('login.html', title='Login', form=form)


@users.route('/logout', methods=['GET'])
def logout():
    logout()
    return redirect('/login')


@users.route('/profile', methods=['GET'])
def profile():

    user_subjects = user_subject('name')
    preferred_time_list = ['08:00','08:30','09:00','09:30','10:00','10:30','11:00','11:30','12:00','12:30','13:00','13:30','14:00','14:30','15:00','15:30','16:00','16:30','17:00','17:30','18:00','18:30']
    preferred_day_list = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    preferred_rate_choice = ['per hour', 'per session']

    if request.method == 'GET':
        profile_details = user_profile_details()

    return render_template('profile.html', profile_details=profile_details, user_subjects=user_subjects, preferred_time_list=preferred_time_list, preferred_day_list=preferred_day_list, preferred_rate_choice=preferred_rate_choice)