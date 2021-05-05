from flask import render_template, url_for, flash, redirect, request, Blueprint
from decouple import config
import requests
import time
from online_matching_system.users.utils import user_info, check_login
from online_matching_system.bids.utils import filter_ongoing_bids

api_key = config('FIT3077_API')
main = Blueprint('main', __name__)

root_url = 'https://fit3077.com/api/v1'
bid_url = root_url + "/bid"

@main.route('/', methods=['GET'])
def index():
    """
    Function for obtaining all bids for the home page
    """
    # results= requests.get(
    #     url=bid_url+'/5d953a80-0e59-4ebf-855e-70f28d3a1693',
    #     headers={'Authorization': api_key},
    #     params={'jwt': 'true', 'fields': 'messages'},
    # )
    # print(results.json())
    #
    # results = requests.delete(
    #     url=root_url+'/message/fc91512a-f5af-42d1-a537-4eed76a2ad27',
    #     headers={'Authorization': api_key},
    #     params={'jwt': 'true'}
    # )
    #
    # results = requests.delete(
    #     url=root_url+"/bid/6a057c68-0a2b-458e-8395-1674263a510a",
    #     headers = {'Authorization': api_key},
    #     params = {'jwt': 'true', 'fields': 'messages'},
    # )
    # print(results.status_code)

    preferred_time_list = ['08:00','08:30','09:00','09:30','10:00','10:30','11:00','11:30','12:00','12:30','13:00','13:30','14:00','14:30','15:00','15:30','16:00','16:30','17:00','17:30','18:00','18:30']
    hours_per_lesson_offered = ['00:30', '01:00', '01:30', '02:00', '02:30', '03:00']
    preferred_day_list = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    rate_choice_offered = ['per hour', 'per session']

    if check_login():
        result = requests.get(
            url=bid_url,
            headers={ 'Authorization': api_key },
            params={ 'jwt': 'true' }, 
        )

        bids = result.json()
        bids = filter_ongoing_bids(bids)
        open_bid = []

        user_info_list = user_info()

        if user_info_list['isTutor']:
            view_bid = ["open", "close"]
        else:
            view_bid = ["open"]

        for bid in bids:
            if bid["type"].lower() in view_bid:
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

                open_bid.append({'id': bid['id'], 'type':bid['type'].lower(), 'initiator': bid['initiator'], 'subject':bid['subject'], 'dateCreated': start_time_converted, 'dateClosedDown': end_time_converted, 'additionalInfo':bid['additionalInfo'] })
    else:
        flash("Please login first", "warning")
        return redirect("/login")

    return render_template('index.html', open_bid=open_bid, user_info=user_info_list, preferred_time_list=preferred_time_list, hours_per_lesson_offered=hours_per_lesson_offered, preferred_day_list=preferred_day_list, rate_choice_offered=rate_choice_offered)