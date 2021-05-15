from flask import render_template, url_for, flash, redirect, request, Blueprint, make_response
from .utils import login_user, logout_manual, user_subject, user_profile_details, check_login, login_required, check_user_model
from flask_login import current_user
from flask import session
from decouple import config
import requests
from online_matching_system.forms import LoginForm

users = Blueprint('users', __name__)

root_url = 'https://fit3077.com/api/v1'
users_url = root_url + "/user"
subjects_url = root_url + "/subject"
users_login_url = users_url + "/login"
verify_token_url = users_url + "/verify-token"

@users.route('/login', methods=['GET', 'POST'])
def login():
    """
    Function to handle the login credentials of the user
    """
    form = LoginForm()

    if form.validate_on_submit():
       
        # get data from form
        username = form.username.data
        password = form.password.data
        # log in user
        result = login_user(username, password)

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
    """
    Function to logout of the system
    """
    logout_manual()
    return redirect('/login')


@users.route('/profile', methods=['GET'])
@login_required
@check_user_model
def profile():
    """
    Function to get the user's profile details
    """
    profile_details = user_profile_details()

    return render_template('profile.html', profile_details=profile_details)