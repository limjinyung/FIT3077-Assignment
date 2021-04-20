from flask import render_template, url_for, redirect, request, make_response, flash, session
from flask_login import current_user
from online_matching_system import app
from decouple import config
from datetime import datetime
import requests, jwt, os, base64, time
from .user import UserFunction

from online_matching_system.forms import LoginForm

# API key from https://fit3077.com/home
api_key = config('FIT3077_API')

# A list of URLs
root_url = 'https://fit3077.com/api/v1'
users_url = root_url + "/user"
subjects_url = root_url + "/subject"
users_login_url = users_url + "/login"
verify_token_url = users_url + "/verify-token"
bid_url = root_url + "/bid"

date_format = "%Y-%m-%dT%H:%M:%S.%fZ"

user = UserFunction()

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
       
        # get data from form
        username = form.username.data
        password = form.password.data
        # log in user
        result = user.login(username, password)

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


@app.route('/logout', methods=['GET'])
def logout():
    user.logout()
    return redirect('/login')


@app.route('/', methods=['GET', 'POST'])
def index():

    if request.method == 'GET':
        result = requests.get(
            url=bid_url,
            headers={ 'Authorization': api_key },
            params={ 'jwt': 'true' }, 
        )

        bids = result.json()
        open_bid = []

        for bid in bids:
            if bid["type"] == "open":
                try:
                    start_time = time.strptime(bid['dateCreated'][:19], "%Y-%m-%dT%H:%M:%S")
                    start_time_converted = time.strftime("%d/%m/%Y %H:%M:%S", start_time)
                except TypeError:
                    start_time_converted = None

                try:
                    end_time = time.strptime(bid['dateClosedDown'][:19], "%Y-%m-%dT%H:%M:%S")
                    end_time_converted = time.strftime("%d/%m/%Y %H:%M:%S", end_time)
                except TypeError:
                    end_time_converted = None

                open_bid.append({'initiator': bid['initiator'], 'subject':bid['subject'], 'dateCreated': start_time_converted, 'dateCloseDown': end_time_converted })

    return render_template('index.html', open_bid=open_bid)


@app.route('/profile', methods=['GET', 'POST'])
def profile():

    if request.method == 'GET':
        profile_details = user.user_details()
        print(profile_details)

    return render_template('profile.html', profile_details=profile_details)