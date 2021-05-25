from flask import render_template, url_for, flash, redirect, request, Blueprint, session, jsonify
from decouple import config
from online_matching_system.users.utils import user_subject
from datetime import datetime
import requests
from .observer import BidObserver, BidObject, bid_observer, bid_monitor as monitor
from online_matching_system.users.utils import login_required, user_index_bids, get_user_role, check_user_model
from online_matching_system.models.user_model import student, tutor
from online_matching_system.models.bid_model import open_bids, close_bids
from .utils import get_bid_details, check_valid_offer, check_contract, search_bids, get_bid_type, all_bids

bids = Blueprint('bids', __name__)
api_key = config('FIT3077_API')

root_url = 'https://fit3077.com/api/v2'
bid_url = root_url + "/bid"
message_url = root_url + "/message"

@bids.route('/bid', methods=["GET"])
@login_required
@check_user_model
def bid_index():
    """
    Function to obtain ongoing and closed down bids to be displayed on the UI
    @return: a flask function to execute bid.html
    """

    user_subjects = user_subject('name')
    preferred_time_list = ['08:00','08:30','09:00','09:30','10:00','10:30','11:00','11:30','12:00','12:30','13:00','13:30','14:00','14:30','15:00','15:30','16:00','16:30','17:00','17:30','18:00','18:30']
    preferred_hours_per_lesson = ['00:30', '01:00', '01:30', '02:00', '02:30', '03:00']
    preferred_day_list = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    preferred_rate_choice = ['per hour', 'per session']
    bid_type = ['Open', 'Close']

    ongoing_bids, closed_down_bids = user_index_bids()

    user_role = get_user_role()
    info = user_role.user_details

    return render_template('bid.html', ongoing_bids=ongoing_bids, closed_down_bids=closed_down_bids, user_info=info,user_subjects=user_subjects, preferred_time_list=preferred_time_list, preferred_hours_per_lesson=preferred_hours_per_lesson, preferred_day_list=preferred_day_list, preferred_rate_choice=preferred_rate_choice, bid_type=bid_type)


@bids.route('/bid_details/<bid_id>', methods=["GET"])
@login_required
@check_user_model
def bid_details(bid_id):
    """
    Function to obtain the bid details based on the bid_id to be displayed on the UI
    @params
    """

    bid_details = get_bid_details(bid_id)
    return render_template('bid_details.html', bid_details=bid_details)


@bids.route('/bid_details_tutor/<bid_id>', methods=["GET"])
@login_required
@check_user_model
def bid_details_tutor(bid_id):
    """
    Function to obtain the bid details based on the bid_id to be displayed on the UI
    @params
    """

    bid_details = get_bid_details(bid_id)
    user_role = get_user_role()
    user_info_list = user_role.user_details
    return render_template('bid_details_tutor.html', bid_details=bid_details, user_info=user_info_list)


@bids.route('/create_bid', methods=["POST"])
@login_required
@check_user_model
def create_bid():
    """
    Function to create a new bid
    """
    subject_id =''

    # retrieve all the form data
    initiator_id = session['user_id']
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

    # turn data into JSON format
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

    # make POST request to API
    response = requests.post(
        url=bid_url,
        headers={ 'Authorization': api_key },
        json = data,
    )

    response_value = response.json()

    if response.status_code == 201:
        flash('Bid created successfully', 'success')

        # get the newly created bid's id and attach to bid observer
        bid_id = response_value["id"]
        bid_observer.attach(BidObject(bid_id), bid_type.lower())

        # call bid model to retrieve new data
        bid_type = get_bid_type(response)
        bid_type.get_bid_list()

    else:
        flash("There's something wrong creating the bid", 'danger')

    return redirect('/bid')


@bids.route('/offer_bid', methods=["POST"])
@login_required
@check_user_model
def offer_bid():
    """
    Function to offer a bid to an existing request
    """

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

    # search the bid with bid id
    target_bid = search_bids(bid_id)

    response_value = target_bid

    # check if the user is valid to make offer
    if check_valid_offer(response_value, bidder_id):

        response_additional = response_value['additionalInfo']

        # add the bidder's request into bidderRequest list
        response_additional['bidderRequest'].append({"bidder":bidder,"bidderId":bidder_id,"bidId":bid_id,"numberOfLessonOffered":number_of_lesson_offered,"hoursPerLessonOffered":hours_per_lesson_offered,"preferredTimeOffered":preferred_time_offered,"preferredDayOffered":preferred_day_offered,"sessionPerWeekOffered":session_per_week_offered,"freeLesson":free_lesson,"rateChoiceOffered":rate_choice_offered,"rateRequest":rate_request, "bid_chosen":bid_chosen})

        return_value = {'additionalInfo': response_additional}

        # partially update with PATCH request to API
        response = requests.patch(
            url=get_bid_url,
            headers={ 'Authorization': api_key },
            json = return_value,
        )

        if response.status_code == 200:
            flash('Offer submitted successfully', 'success')

            # call bid model to retrieve new data
            bid_type = get_bid_type(response)
            bid_type.get_bid_list()
        else:
            flash("There's something wrong submitting your offer. Please try again", 'danger')

    else:
         flash("You have already offered the bid or you dont have competency offer this bid.", 'danger')

    return redirect('/')


@bids.route('/choose_offer/<bid_id>/<bidder_id>', methods=["GET","POST"])
@login_required
@check_user_model
def choose_offer(bid_id, bidder_id):
    """
    Function to choose an offer from all offers of the bid
    """

    bid_details_url = bid_url + "/{}".format(bid_id)

    target_bid = search_bids(bid_id)

    # get the bid and update the bid_chosen boolean field
    bid_additional_info = target_bid['additionalInfo']

    for bidder_request in bid_additional_info['bidderRequest']:
        if bidder_request['bidderId'] == bidder_id:
            bidder_request['bid_chosen'] = True

    # convert data into JSON format
    return_value = {'additionalInfo': bid_additional_info}

    # PATCH the return value to partially update the API
    response = requests.patch(
        url=bid_details_url,
        headers={ 'Authorization': api_key },
        json = return_value,
    )

    # return the response status
    if (response.status_code == 200) | (response.status_code == 302):
        bid_observer.find_and_detach(bid_id)

        # call bid model to retrieve new data
        bid_type = get_bid_type(response)
        bid_type.get_bid_list()

        flash('Deal accept successfully', 'success')
    else:
        flash("There's something wrong. Please try again", 'danger')

    return redirect('/bid')


@bids.route('/buy_out/<bid_id>', methods=["GET"])
@login_required
@check_user_model
def buy_out(bid_id):
    """
    Function to buy out a bid for the bidder
    """

    bid_details_url = bid_url + "/{}".format(bid_id)

    bid_details = search_bids(bid_id)

    user_role = get_user_role()
    user_info_list = user_role.user_details

    # buying ouy the bid means that the tutor agrees with all the condition
    # get all the condition that the requestor requested and add it into bidder's request
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

    # check if the user is valid to make offer
    if check_valid_offer(bid_details, bidder_id):

        # add the bidder request into the bidderRequest field
        response_additional = bid_details['additionalInfo']

        response_additional['bidderRequest'].append({"bidder":bidder,"bidderId":bidder_id,"bidId":bid_id,"numberOfLessonOffered":number_of_lesson_offered,"hoursPerLessonOffered":hours_per_lesson_offered,"preferredTimeOffered":preferred_time_offered,"preferredDayOffered":preferred_day_offered,"sessionPerWeekOffered":session_per_week_offered,"freeLesson":free_lesson,"rateChoiceOffered":rate_choice_offered,"rateRequest":rate_request, "bid_chosen":bid_chosen})

        # convert the data into JSON format
        return_value = {'additionalInfo': response_additional}

        # PATCH the return value to partially update the API
        response = requests.patch(
            url=bid_details_url,
            headers={ 'Authorization': api_key },
            json = return_value,
        )

        if (response.status_code == 200) | (response.status_code == 302):
            bid_observer.find_and_detach(bid_id)

            # call bid model to retrieve new data
            bid_type = get_bid_type(response)
            bid_type.get_bid_list()

            flash('Buy out successfully', 'success')
        else:
            flash("There's something wrong. Please try again", 'danger')
    else:
        flash("You have already offered the bid or you dont have competency offer this bid.", 'danger')

    return redirect('/')


@bids.route('/bid_details_close/<string:bid_id>', methods=["GET", "POST"])
@login_required
@check_user_model
def bid_messages(bid_id):
    """
    Function to get and post bid details for close
    """
    the_bid=''
    if request.method == 'GET':
        preferred_time_list = ['08:00', '08:30', '09:00', '09:30', '10:00', '10:30', '11:00', '11:30', '12:00', '12:30',
                               '13:00', '13:30', '14:00', '14:30', '15:00', '15:30', '16:00', '16:30', '17:00', '17:30',
                               '18:00', '18:30']
        preferred_day_list = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        preferred_rate_choice = ['per hour', 'per session']
        preferred_hours_per_lesson = ['00:30', '01:00', '01:30', '02:00', '02:30', '03:00']

        bids = all_bids()

        for bid in bids:
            if bid['id'] == bid_id:
                the_bid = bid
                break

        print(the_bid)

        user_role = get_user_role()

        profile_details = user_role.user_details
        reverse_msgs = the_bid['messages'][::-1]

        print(profile_details)

        return render_template('bid_details_close.html', reverse_msgs=reverse_msgs, profile_details=profile_details,
                               the_bid=the_bid, preferred_time_list=preferred_time_list,
                               preferred_day_list=preferred_day_list, preferred_hours_per_lesson=preferred_hours_per_lesson,
                               preferred_rate_choice=preferred_rate_choice)

    if request.method == 'POST':
        date_posted = datetime.now()
        content = request.form.get('content')
        data = {}

        bids = all_bids()

        for bid in bids:
            if bid['id'] == bid_id:
                the_bid = bid
                break

        user_role = get_user_role()
        user_details = user_role.user_details

        if user_details['id'] != the_bid['initiator']['id']:
            lesson_needed = request.form.get('number_of_lesson_offered')
            preferred_hours = request.form.get('hours_per_lesson_offered')
            preferred_time = request.form.get('preferred_time')
            preferred_day = request.form.get('preferred_day')
            preferred_session_per_week = request.form.get('session_per_week_offered')
            free_lesson = request.form.get('free_lesson')
            preferred_rate_choice = request.form.get('preferred_rate_choice')
            preferred_rate = request.form.get('preferred_rate')
            data={
                "bidId": bid_id,
                "posterId": session['user_id'],
                "datePosted": str(date_posted),
                "content": content,
                "additionalInfo": {"lessonNeeded": lesson_needed,"preferredHours": preferred_hours,
                                   "preferredTime": preferred_time, "preferredDay": preferred_day,
                                   "preferredSessionPerWeek": preferred_session_per_week, 'freeLesson': free_lesson,
                                   "preferredRateChoice": preferred_rate_choice,
                                   "preferredRate": preferred_rate, "contentFrom": user_details['id'],
                                   "contentTo": the_bid['initiator']['id'], "initialBid": True, "bid_chosen": False}
            }

        # TODO: message model
        
        results = requests.post(
            url=message_url,
            headers={'Authorization': api_key},
            json=data
        )

    return redirect('/bid_details_close/'+bid_id)


@bids.route('/reply_messages/<string:bid_id>/<string:message_id>', methods=["POST"])
@login_required
@check_user_model
def reply_messages(bid_id, message_id):
    """
    Function to reply to close bid messages
    """
    date_posted = datetime.now()
    content = request.form.get('content')

    # TODO: message model

    results = requests.get(
        url=message_url+'/'+message_id,
        headers={'Authorization': api_key},
        params={'jwt': 'true'}
    )
    the_msg = results.json()

    data = {
        "bidId": bid_id,
        "posterId": session['user_id'],
        "datePosted": str(date_posted),
        "content": content,
        "additionalInfo": {"contentFrom": session['user_id'], "contentTo": the_msg["poster"]["id"]}
    }

    # TODO: message model

    results = requests.post(
        url=message_url,
        headers={'Authorization': api_key},
        json=data
    )

    print("Sending reply response code:"+str(results.status_code))
    return redirect('/bid_details_close/'+bid_id)


@bids.route('/choose_offer_close/<bid_id>/<message_id>', methods=["GET","POST"])
@login_required
@check_user_model
def choose_offer_close_bid(bid_id, message_id):

    the_bid = search_bids(bid_id)

    # TODO: message model
    
    results = requests.get(
        url=message_url+'/'+message_id,
        headers={'Authorization': api_key},
        params={'jwt': 'true'}
    )
    the_msg = results.json()
    the_msg['additionalInfo']['bid_chosen'] = True


    finalized_msg = {"content": the_msg['content'], "additionalInfo": the_msg['additionalInfo']}

    response = requests.patch(
        url=message_url+'/'+message_id,
        headers={'Authorization': api_key},
        json=finalized_msg
    )

    if (response.status_code == 200) | (response.status_code == 302):
        print("The bid before being detached: "+str(the_bid))
        # bid_observer.attach(BidObject(bid_id), 'close')
        bid_observer.find_and_detach(the_bid['id'])

        flash('Deal accept successfully', 'success')
    else:
        flash("There's something wrong. Please try again", 'danger')

    return redirect('/bid')


@bids.route('/bid_monitor', methods=["GET","POST"])
@login_required
@check_user_model
def bid_monitor_index():

    return render_template('bid_monitor.html')


@bids.route('/monitor_list', methods=["GET"])
@login_required
@check_user_model
def get_monitor_list():

    return jsonify(monitor.get_monitor_list())


@bids.route('/monitor_bid_details/<bid_id>', methods=["GET"])
@login_required
@check_user_model
def monitor_bid_details(bid_id):

    print(bid_id)
    return render_template('bid_monitor_details.html', bid_id=bid_id)


@bids.route('/get_monitor_bid/<bid_id>', methods=["GET"])
@login_required
@check_user_model
def get_monitor_bid(bid_id):

    return jsonify(monitor.get_monitor_bid(bid_id))


@bids.route('/add_bid_to_monitor/<bid_id>', methods=["GET","POST"])
@login_required
@check_user_model
def add_bid_to_monitor(bid_id):

    try:
        bid = search_bids(bid_id)
        status = monitor.add_bid(bid_id)

        if status:
            flash('Bid sucessfully added to monitor list.', 'sucess')
        else:
            flash('Bid added into monitor list already', 'danger')
    except Exception as e:
        print('Exception occur in add_bid: {}'.formate(e))

    return render_template('bid_monitor.html')