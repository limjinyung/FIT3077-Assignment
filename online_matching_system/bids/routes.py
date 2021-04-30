from flask import render_template, url_for, flash, redirect, request, Blueprint
from decouple import config
from online_matching_system.users.utils import get_user_id, user_subject
from datetime import datetime
import requests
from .observer import BidObserver, BidObject, bid_observer
from online_matching_system.users.utils import user_bids, user_info
from .utils import get_bid_details, check_valid_offer

bids = Blueprint('bids', __name__)
api_key = config('FIT3077_API')

root_url = 'https://fit3077.com/api/v1'
bid_url = root_url + "/bid"


@bids.route('/bid', methods=["GET"])
def bid_index():

    user_subjects = user_subject('name')
    preferred_time_list = ['08:00','08:30','09:00','09:30','10:00','10:30','11:00','11:30','12:00','12:30','13:00','13:30','14:00','14:30','15:00','15:30','16:00','16:30','17:00','17:30','18:00','18:30']
    preferred_hours_per_lesson = ['00:30', '01:00', '01:30', '02:00', '02:30', '03:00']
    preferred_day_list = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    preferred_rate_choice = ['per hour', 'per session']
    bid_type = ['Open', 'Close']

    ongoing_bids, closed_down_bids = user_bids()
    info = user_info()

    return render_template('bid.html', ongoing_bids=ongoing_bids, closed_down_bids=closed_down_bids, user_info=info,user_subjects=user_subjects, preferred_time_list=preferred_time_list, preferred_hours_per_lesson=preferred_hours_per_lesson, preferred_day_list=preferred_day_list, preferred_rate_choice=preferred_rate_choice, bid_type=bid_type)


@bids.route('/bid_details/<bid_id>', methods=["GET"])
def bid_details(bid_id):

    bid_details = get_bid_details(bid_id)

    return render_template('bid_details.html', bid_details=bid_details)


@bids.route('/create_bid', methods=["POST"])
def create_bid():

    subject_id =''

    initiator_id = get_user_id()
    date_created = datetime.now()
    bid_type = request.form.get('bid_type')
    # subject chosen by the requestor
    chosen_subject = request.form.get('subject')
    # get all the subject that the requestor has
    user_subjects_list = user_subject()
    # find the subject to get the subject ID
    for subject in user_subjects_list:
        if subject['name'] == chosen_subject:
            subject_id = subject['id']
    tutor_qualification = request.form.get('tutor_qualification')
    lesson_needed = request.form.get('lesson_needed')
    preferred_hours_per_lesson = request.form.get('preferred_hours_per_lesson')
    preferred_time = request.form.get('preferred_time')
    preferred_day = request.form.get('preferred_day')
    preferred_session_per_week = request.form.get('preferred_session_per_week')
    preferred_rate_choice = request.form.get('preferred_rate_choice')
    preferred_rate = request.form.get('preferred_rate')

    data = { 
        "type": bid_type,
        "initiatorId": initiator_id,
        "dateCreated": str(date_created),
        "subjectId": subject_id,
        "additionalInfo": {
            "initiatorBid": {
                "tutorQualification": tutor_qualification, 
                "lessonNeeded": lesson_needed, 
                "preferredHoursPerLesson": preferred_hours_per_lesson,
                "preferredTime": preferred_time, 
                "preferredDay": preferred_day, 
                "preferredSessionPerWeek": preferred_session_per_week, 
                "preferredRateChoice": preferred_rate_choice, 
                "preferredRate": preferred_rate
            },
            "bidderRequest": []
        }
    }

    response = requests.post(
        url=bid_url,
        headers={ 'Authorization': api_key },
        json = data,
    )

    response_value = response.json()

    bid_id = response_value["id"]
    bid_observer.attach(BidObject(bid_id))
    
    if response.status_code == 201:
        flash('Bid created successfully', 'success')
    else:
        flash("There's something wrong creating the bid", 'danger')

    return redirect('/bid')


@bids.route('/offer_bid', methods=["POST"])
def offer_bid():

    bidder = request.form.get('bidder')
    bidder_id = request.form.get('bidder_id')
    bid_id = request.form.get('bid_id')
    number_of_lesson_offered = request.form.get('number_of_lesson_offered')
    hours_per_lesson_offered = request.form.get('hours_per_lesson_offered')
    preferred_time_offered = request.form.get('preferred_time_offered')
    preferred_day_offered = request.form.get('preferred_day_offered')
    session_per_week_offered = request.form.get('session_per_week_offered')
    free_lesson = request.form.get('free_lesson')
    rate_choice_offered = request.form.get('rate_choice_offered')
    rate_request = request.form.get('rate_request')
    bid_chosen = False

    get_bid_url = bid_url + '/{}'.format(bid_id)

    response = requests.get(
        url=get_bid_url,
        headers={ 'Authorization': api_key },
    )

    response_value = response.json()

    # check if the user has made the offer already
    if check_valid_offer(response_value, bidder_id):

        response_additional = response_value['additionalInfo']

        response_additional['bidderRequest'].append({"bidder":bidder,"bidderId":bidder_id,"bidId":bid_id,"numberOfLessonOffered":number_of_lesson_offered,"hoursPerLessonOffered":hours_per_lesson_offered,"preferredTimeOffered":preferred_time_offered,"preferredDayOffered":preferred_day_offered,"sessionPerWeekOffered":session_per_week_offered,"freeLesson":free_lesson,"rateChoiceOffered":rate_choice_offered,"rateRequest":rate_request, "bid_chosen":bid_chosen})

        return_value = {'additionalInfo': response_additional}

        response = requests.patch(
            url=get_bid_url,
            headers={ 'Authorization': api_key },
            json = return_value,
        )

        if response.status_code == 200:
            flash('Offer submitted successfully', 'success')
        else:
            flash("There's something wrong submitting your offer. Please try again", 'danger')
     
    else:
         flash("You cannot offer a bid twice", 'danger')

    return redirect('/')


@bids.route('/buy_out/<bid_id>', methods=["GET"])
def buy_out(bid_id):

    bid_details_url = bid_url + "/{}".format(bid_id)

    user_info_list = user_info()

    bid_details = requests.get(
        url=bid_details_url,
        headers={ 'Authorization': api_key },
    ).json()

    # print(bid_details)

    bidder = user_info_list['userName']
    bidder_id = user_info_list['id']
    bid_id = bid_details['id']
    number_of_lesson_offered = bid_details['additionalInfo']['initiatorBid']['lessonNeeded']
    hours_per_lesson_offered = bid_details['additionalInfo']['initiatorBid']['preferredHoursPerLesson']
    preferred_time_offered = bid_details['additionalInfo']['initiatorBid']['preferredTime']
    preferred_day_offered = bid_details['additionalInfo']['initiatorBid']['preferredDay']
    session_per_week_offered = bid_details['additionalInfo']['initiatorBid']['preferredSessionPerWeek']
    free_lesson = "on"
    rate_choice_offered = bid_details['additionalInfo']['initiatorBid']['preferredRateChoice']
    rate_request = bid_details['additionalInfo']['initiatorBid']['preferredRate']
    bid_chosen = True

    response_additional = bid_details['additionalInfo']

    response_additional['bidderRequest'].append({"bidder":bidder,"bidderId":bidder_id,"bidId":bid_id,"numberOfLessonOffered":number_of_lesson_offered,"hoursPerLessonOffered":hours_per_lesson_offered,"preferredTimeOffered":preferred_time_offered,"preferredDayOffered":preferred_day_offered,"sessionPerWeekOffered":session_per_week_offered,"freeLesson":free_lesson,"rateChoiceOffered":rate_choice_offered,"rateRequest":rate_request, "bid_chosen":bid_chosen})

    return_value = {'additionalInfo': response_additional}

    response = requests.patch(
        url=bid_details_url,
        headers={ 'Authorization': api_key },
        json = return_value,
    )

    print(response.status_code)

    if (response.status_code == 200) | (response.status_code == 302):
        bid_observer.find_and_detach(bid_id)
        flash('Buy out successfully', 'success')
    else:
        flash("There's something wrong. Please try again", 'danger')

    return redirect('/')