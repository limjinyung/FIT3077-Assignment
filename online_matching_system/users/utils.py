import requests
# from online_matching_system.routes import *
#from flask_login import current_user
from flask import session, flash, redirect, render_template, url_for, request
from functools import wraps
#from decouple import config
from online_matching_system.models.user_model import student, tutor

root_url = 'https://fit3077.com/api/v2'
users_url = root_url + "/user"
users_login_url = users_url + "/login"
api_key = 't9zQjWjQpmf7h7qGQFNfQbrQ7tfjzn'


def check_login():

    try:
        if session['user_id']:
            return True
    except KeyError:
        return False


def create_user_model():
    """
    initialized the user model
    format: boolean
    """

    user_id_url = root_url + "/{}/{}".format("user", session['user_id'])

    user_info = requests.get(
        url=user_id_url,
        headers={ 'Authorization': api_key },
    ).json()

    if user_info['isStudent']:
        session['user_role'] = 'student'
        student.get_user_id()
        student.get_user_details()
        student.get_user_bids()
        student.get_user_competencies()
        student.get_user_qualifications()
        student.get_contract_number()
        student.initialized = True
    elif user_info['isTutor']:
        session['user_role'] = 'tutor'
        tutor.get_user_id()
        tutor.get_user_details()
        tutor.get_user_bids()
        tutor.get_user_competencies()
        tutor.get_user_qualifications()
        tutor.initialized = True
    else:
        raise Exception("user is not student and tutor. What is the user role?")

    print(student, tutor)

    return student, tutor


def login_required(f):
    """
    to ask user login first before perform any action
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            if session['user_id']:
                pass
        except KeyError:
            return redirect(url_for('users.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def check_user_model(f):
    """
    initialized the user model if it is not yet initialized. 
    when Flask restart stat, class data will de reset and data will be lost. Hence, we'll need to check if the user model is initalized already before we perform any action
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if student.check_initialized() or tutor.check_initialized():
            pass
        else:
            create_user_model()
            return redirect(str(request.url))
        return f(*args, **kwargs)
    return decorated_function


def login_user(username, password):

    # get response from API
    response = requests.post(
        url=users_login_url,
        headers={ 'Authorization': api_key },
        params={ 'jwt': 'true' }, 
        data={
            'userName': username,
            'password': password
        }
    )

    # if user exist
    if response.status_code == 200:

        # retrieve jwt returned from API
        json_data = response.json()
        jwt = json_data['jwt']

        # retrieve user's id for profile purposes
        users_list = requests.get(
            url=users_url,
            headers={ 'Authorization': api_key },
            params={ 'jwt': 'true' }, 
        ).json()

        # filter the list and find the user
        for user in users_list:
            if user['userName'] == username:
                # store the user's ID in session
                session['user_id'] = user["id"]

        create_user_model()
    
    return response

def logout_manual():
    # clear session keys
    for key in list(session.keys()):
        session.pop(key)

    return None


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

    encoded_jwt = encoded_jwt.split(".")
    message = base64.b64decode(encoded_jwt[1])
    print('message: ' + str(message))


def user_subject(info=None):

    subject_list = []

    user_role = get_user_role()

    user_competencies = user_role.user_competencies

    if info != None:
        for subject in user_competencies:
            subject_list.append(subject['subject'][str(info)])
    else:
        for subject in user_competencies:
            subject_list.append(subject['subject'])

    return subject_list

def get_user_role():
    """
    to check user's role
    @return: student object or tutor object, if not raise exception
    """

    if session['user_role'] == 'student':
        return student
    elif session['user_role'] == 'tutor':
        return tutor
    else:
        raise Exception("User is not student or tutor. Who is user?")

def user_profile_details():
    """
    to get user's details and display in profile html
    """

    user_role = get_user_role()
    
    user_details = user_role.user_details
    user_competencies = user_role.user_competencies
    user_qualifications = user_role.user_qualifications
    user_bids = user_role.user_bids

    user_profile_info = {'user_details': user_details, 'user_competencies':user_competencies, 'user_qualifications':user_qualifications, 'user_bids':user_bids}

    return user_profile_info


def user_index_bids():

    # get user role
    user_role = get_user_role()
    # update bid data from API
    user_role.get_user_bids()

    ongoing_bid = []
    closed_down_bid = []

    # use for loop to separate ongoing bid and closed down bid
    for bid in user_role.user_bids:

        if bid["dateClosedDown"] != None:
            closed_down_bid.append(bid)
        else:
            ongoing_bid.append(bid)

    return ongoing_bid, closed_down_bid