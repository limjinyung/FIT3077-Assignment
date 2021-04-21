from flask import render_template, url_for, redirect, request, make_response, flash, session, jsonify
from flask_login import current_user
from online_matching_system import app
from decouple import config
from datetime import datetime
import requests, jwt, os, base64, time
from .user import user
import json

from online_matching_system.forms import LoginForm, CreateBidForm

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

# user = UserFunction()

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
        
    user_info = user.user_info()

    return render_template('index.html', open_bid=open_bid, user_info=user_info)


@app.route('/profile', methods=['GET'])
def profile():

    user_subjects = user.user_subject('name')
    preferred_time_list = ['08:00','08:30','09:00','09:30','10:00','10:30','11:00','11:30','12:00','12:30','13:00','13:30','14:00','14:30','15:00','15:30','16:00','16:30','17:00','17:30','18:00','18:30']
    preferred_day_list = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    preferred_rate_choice = ['per hour', 'per session']

    if request.method == 'GET':
        profile_details = user.user_profile_details()

    return render_template('profile.html', profile_details=profile_details, user_subjects=user_subjects, preferred_time_list=preferred_time_list, preferred_day_list=preferred_day_list, preferred_rate_choice=preferred_rate_choice)


@app.route('/create_bid', methods=["POST"])
def create_bid():

    subject_id =''

    initiator_id = user.get_user_id()
    date_created = datetime.now()
    subject = request.form.get('subject')
    user_subjects = user.user_subject()
    for user_subject in user_subjects:
        if user_subject['name'] == subject:
            subject_id = user_subject['id']
    tutor_qualification = request.form.get('tutor_qualification')
    lesson_needed = request.form.get('lesson_needed')
    preferred_time = request.form.get('preferred_time')
    preferred_day = request.form.get('preferred_day')
    preferred_session_per_week = request.form.get('preferred_session_per_week')
    preferred_rate_choice = request.form.get('preferred_rate_choice')
    preferred_rate = request.form.get('preferred_rate')

    print(initiator_id)
    print(date_created)
    print(subject_id)
    print(tutor_qualification)
    print(lesson_needed)
    print(preferred_time)
    print(preferred_day)
    print(preferred_session_per_week)
    print(preferred_rate_choice)
    print(preferred_rate)

    # additional_info = {}
    # additional_info['tutorQualification']= str(tutor_qualification)
    # additional_info['lessonNeeded']= str(lesson_needed)
    # additional_info['preferredTime']= str(preferred_time)
    # additional_info['preferredDay']= str(preferred_day)
    # additional_info['preferredSessionPerWeek']= str(preferred_session_per_week)
    # additional_info['preferredRateChoice']= str(preferred_rate_choice)
    # additional_info['preferredRate']= str(preferred_rate)
    # print(additional_info_json, type(additional_info_json))

    # additional_info_json = dict(
    #     tutorQualification= tutor_qualification, 
    #     lessonNeeded= lesson_needed, 
    #     preferredTime= preferred_time, 
    #     preferredDay= preferred_day, 
    #     preferredSessionPerWeek= preferred_session_per_week, 
    #     preferredRateChoice= preferred_rate_choice, 
    #     preferredRate= preferred_rate
    # )

    # additional_info = '{{"tutorQualification":"{tutor_qualification}","lessonNeeded":"{lesson_needed}","preferredTime":"{preferred_time}","preferredDay":"{preferred_day}","preferredSessionPerWeek":"{preferred_session_per_week}","preferredRateChoice":"{preferred_rate_choice}","preferredRate":"{preferred_rate}"}}'.format(tutor_qualification=tutor_qualification,lesson_needed=lesson_needed,preferred_time=preferred_time,preferred_day=preferred_day,preferred_session_per_week=preferred_session_per_week,preferred_rate_choice=preferred_rate_choice,preferred_rate=preferred_rate)
    # additional_info = {"tutorQualification": tutor_qualification, "lessonNeeded": lesson_needed, "preferredTime": preferred_time, "preferredDay": preferred_day, "preferredSessionPerWeek": preferred_session_per_week, "preferredRateChoice": preferred_rate_choice, "preferredRate": preferred_rate}
    # additional_info_json = json.dumps(additional_info, default=json_util.default)
    # print(additional_info, type(additional_info))

    data = { 
        "type": "open",
        "initiatorId": initiator_id,
        "dateCreated": str(date_created),
        "subjectId": subject_id,
        "additionalInfo": {"tutorQualification": tutor_qualification, "lessonNeeded": lesson_needed, "preferredTime": preferred_time, "preferredDay": preferred_day, "preferredSessionPerWeek": preferred_session_per_week, "preferredRateChoice": preferred_rate_choice, "preferredRate": preferred_rate},
    }

    response = requests.post(
        url=bid_url,
        headers={ 'Authorization': api_key },
        json = data,
        # data={ 
        #     "type": "open",
        #     "initiatorId": initiator_id,
        #     "dateCreated": date_created,
        #     "subjectId": subject_id,
        #     "additionalInfo": {"tutorQualification": tutor_qualification, "lessonNeeded": lesson_needed, "preferredTime": preferred_time, "preferredDay": preferred_day, "preferredSessionPerWeek": preferred_session_per_week, "preferredRateChoice": preferred_rate_choice, "preferredRate": preferred_rate},
        #     # "addtionalInfo": {"tutorQualification": tutor_qualification, "lessonNeeded": lesson_needed, "preferredTime": preferred_time, "preferredDay": preferred_day, "preferredSessionPerWeek": preferred_session_per_week, "preferredRateChoice": preferred_rate_choice, "preferredRate": preferred_rate}
        # }, 
    )

    print(response.request.body)
    print(response.json())

    print('Status code is: {} {}'.format(response.status_code, response.reason))

    if response.status_code == 201:
        flash('Bid created successfully', 'success')
    else:
        flash("There's something wrong creating the bid", 'danger')

    return redirect('/profile')
