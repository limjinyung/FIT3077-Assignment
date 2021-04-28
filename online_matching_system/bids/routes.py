from flask import render_template, url_for, flash, redirect, request, Blueprint
from decouple import config
from online_matching_system.users.utils import get_user_id, user_subject
from datetime import datetime
import requests
from .observer import BidObserver, BidObject

bids = Blueprint('bids', __name__)
api_key = config('FIT3077_API')

root_url = 'https://fit3077.com/api/v1'
bid_url = root_url + "/bid"

bid_observer = BidObserver()

@bids.route('/create_bid', methods=["POST"])
def create_bid():

    subject_id =''

    initiator_id = get_user_id()
    date_created = datetime.now()
    chosen_subject = request.form.get('subject')
    user_subjects_list = user_subject()
    for subject in user_subjects_list:
        if subject['name'] == chosen_subject:
            subject_id = subject['id']
    tutor_qualification = request.form.get('tutor_qualification')
    lesson_needed = request.form.get('lesson_needed')
    preferred_time = request.form.get('preferred_time')
    preferred_day = request.form.get('preferred_day')
    preferred_session_per_week = request.form.get('preferred_session_per_week')
    preferred_rate_choice = request.form.get('preferred_rate_choice')
    preferred_rate = request.form.get('preferred_rate')

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
    )

    response_value = response.json()
    print(response_value)

    bid_id = response_value["id"]
    bid_observer.attach(BidObject(bid_id))
    
    if response.status_code == 201:
        flash('Bid created successfully', 'success')
    else:
        flash("There's something wrong creating the bid", 'danger')

    return redirect('/profile')