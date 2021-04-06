from flask import render_template, url_for, redirect, request, make_response
from online_matching_system import app
import requests
import jwt
import os
from decouple import config

from online_matching_system.forms import LoginForm

# API key from https://fit3077.com/home
api_key = config('FIT3077_API')

# A list of URLs
root_url = 'https://fit3077.com/api/v1'
users_url = root_url + "/user"
subjects_url = root_url + "/subject"
users_login_url = users_url + "/login"
verify_token_url = users_url + "/verify-token"

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        # get data from form
        username = form.username.data
        password = form.password.data

        # get response from API
        result = requests.post(
            url=users_login_url,
            headers={ 'Authorization': api_key },
            params={ 'jwt': 'true' }, 
            data={
                'userName': username,
                'password': password
            }
        )

        # status code
        print('Status code is: {} {}'.format(result.status_code, result.reason))

        # retreive the JWT from the response
        json_data = result.json()
        jwt = json_data['jwt']

        # print(decode_jwt(jwt))

        # redirect to another and save the JWT in cookies
        response = make_response(redirect('/'))
        response.set_cookie('acess_token', jwt, httponly=True)
        return response

    return render_template('login.html', title='Login', form=form)


def verify_token(token):

    result = requests.post(
        url=verify_token_url,
        headers={ 'Authorization': api_key },
        data={
            'jwt': token,
        }
    )

    print('Status code is: {} {}'.format(result.status_code, result.reason))


def decode_jwt(encoded_jwt):

    return jwt.decode(encoded_jwt, api_key, algorithms="HS256")


@app.route('/', methods=['GET', 'POST'])
def index():

    return render_template('index.html')