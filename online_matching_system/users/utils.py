import requests
# from online_matching_system.routes import *
from flask_login import current_user
from flask import session
from decouple import config

root_url = 'https://fit3077.com/api/v1'
users_url = root_url + "/user"
users_login_url = users_url + "/login"
api_key = config('FIT3077')


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


def get_user_id():

    user_id_url = users_url + "/{}".format(session['user_id'])

    user_info = requests.get(
        url=user_id_url,
        headers={ 'Authorization': api_key },
    ).json()

    return user_info['id']


def user_info():

    user_id_url = users_url + "/{}".format(session['user_id'])

    user_info = requests.get(
        url=user_id_url,
        headers={ 'Authorization': api_key },
    ).json()

    return user_info


def user_subject(info=None):

    subject_list = []

    user_id_url = users_url + "/{}".format(session['user_id'])

    user_competencies = requests.get(
        url=user_id_url,
        headers={ 'Authorization': api_key },
        params={
            'fields':'competencies.subject'
        }
    ).json()

    if info != None:
        for subject in user_competencies['competencies']:
            subject_list.append(subject['subject'][str(info)])
    else:
        for subject in user_competencies['competencies']:
            subject_list.append(subject['subject'])

    return subject_list


def get_user_competencies():

    user_id_url = users_url + "/{}".format(session['user_id'])

    user_competencies = requests.get(
        url=user_id_url,
        headers={ 'Authorization': api_key },
        params={
            'fields':'competencies.subject'
        }
    ).json()
    
    return user_competencies


def get_user_qualifications():

    user_id_url = users_url + "/{}".format(session['user_id'])

    user_qualifications = requests.get(
        url=user_id_url,
        headers={ 'Authorization': api_key },
        params={
            'fields':'qualifications'
        }
    ).json()

    return user_qualifications


def get_user_bids():

    user_id_url = users_url + "/{}".format(session['user_id'])

    user_bids = requests.get(
        url=user_id_url,
        headers={ 'Authorization': api_key },
        params={
            'fields':'initiatedBids'
        }
    ).json()

    return user_bids

def user_profile_details():

    user_id_url = users_url + "/{}".format(session['user_id'])

    # TODO: merge all params in one requests
    user_details = requests.get(
        url=user_id_url,
        headers={ 'Authorization': api_key },
    ).json()

    # user_competencies = requests.get(
    #     url=user_id_url,
    #     headers={ 'Authorization': api_key },
    #     params={
    #         'fields':'competencies.subject'
    #     }
    # ).json()

    user_competencies = get_user_competencies()

    # user_qualifications = requests.get(
    #     url=user_id_url,
    #     headers={ 'Authorization': api_key },
    #     params={
    #         'fields':'qualifications'
    #     }
    # ).json()

    user_qualifications = get_user_qualifications()

    # user_bids = requests.get(
    #     url=user_id_url,
    #     headers={ 'Authorization': api_key },
    #     params={
    #         'fields':'initiatedBids'
    #     }
    # ).json()

    user_bids = get_user_bids()

    user_profile_info = {'user_details': user_details, 'user_competencies':user_competencies['competencies'], 'user_qualifications':user_qualifications['qualifications'], 'user_bids':user_bids['initiatedBids']}

    return user_profile_info


def user_index_bids():

    user_id_url = users_url + "/{}".format(session['user_id'])

    user_bids = requests.get(
        url=user_id_url,
        headers={ 'Authorization': api_key },
        params={
            'fields':'initiatedBids'
        }
    ).json()

    ongoing_bid = []
    closed_down_bid = []

    for bid in user_bids['initiatedBids']:

        if bid["dateClosedDown"] != None:
            closed_down_bid.append(bid)
        else:
            ongoing_bid.append(bid)

    return ongoing_bid, closed_down_bid