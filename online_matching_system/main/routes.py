from flask import render_template, url_for, flash, redirect, request, Blueprint
from decouple import config
import requests
import time
from online_matching_system.users.utils import user_info

api_key = config('FIT3077_API')
main = Blueprint('main', __name__)

root_url = 'https://fit3077.com/api/v1'
bid_url = root_url + "/bid"

@main.route('/', methods=['GET', 'POST'])
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

                open_bid.append({'initiator': bid['initiator'], 'subject':bid['subject'], 'dateCreated': start_time_converted, 'dateClosedDown': end_time_converted, 'additionalInfo':bid['additionalInfo'] })
    
    print(open_bid)
    user_info_list = user_info()

    return render_template('index.html', open_bid=open_bid, user_info=user_info_list)