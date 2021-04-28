from decouple import config
import requests
from datetime import datetime

api_key = config('FIT3077_API')

root_url = 'https://fit3077.com/api/v1'
bid_url = root_url + "/bid"

def close_bid(bid_id):

    close_bid_url = bid_url + '/{}/close-down'.format(bid_id)

    response = requests.post(
        url=close_bid_url,
        headers={ 'Authorization': api_key },
        data = {
            "dateClosedDown": datetime.now()
        }
    )

    print(response.content)

    return response.status_code