from decouple import config
import requests
from datetime import datetime
from online_matching_system.contract.utils import generate_contract
from online_matching_system.users.utils import get_user_competencies, users_url

api_key = config('FIT3077_API')

root_url = 'https://fit3077.com/api/v1'
bid_url = root_url + "/bid"
contract_url = root_url + "/contract"

def close_bid(bid_id):
    """
    Function to close a bid
    """
    close_bid_url = bid_url + '/{}/close-down'.format(bid_id)
    print("The bid being closed down"+str(bid_id))
    print("The bid url:"+str(close_bid_url))
    response = requests.post(
        url=close_bid_url,
        headers={ 'Authorization': api_key },
        data = {
            "dateClosedDown": datetime.now()
        }
    )
    # print(response.status_code)

    result = requests.get(
        url=bid_url+'/'+bid_id,
        headers={'Authorization': api_key},
        params={'jwt': 'true', 'fields': 'messages'}
    )
    # print(result.json)

    generate_contract(bid_id)

    return response.status_code


def get_bid_details(bid_id):
    """
    Function to get a bid's details using the bid_id
    """

    bid_details_url = bid_url + "/{}".format(bid_id)

    response = requests.get(
        url=bid_details_url,
        headers={ 'Authorization': api_key },
        params={'fields': 'messages'}
    ).json()

    bid_type = response['type'].lower()
    bid_date_created = response['dateCreated']
    bid_date_closed_down = response['dateClosedDown']
    bid_subject = response['subject']['name']
    initiator_bid = response['additionalInfo']['initiatorBid']
    bidder_request = response['additionalInfo']['bidderRequest']
    messages = response['messages']

    return {'bid_type':bid_type, 'bid_date_created':bid_date_created, 'bid_date_closed_down':bid_date_closed_down,
            'bid_subject':bid_subject, 'initiator_bid':initiator_bid, 'bidder_request':bidder_request, 'messages':messages}


def check_valid_offer(bid_info, bidder_id):
    """
    to check if the user submit the offer more than once
    """
    user_has_competencies = False
    first_bid = True

    bidder_requests = bid_info['additionalInfo']['bidderRequest']

    for bid_request in bidder_requests:
        if bid_request['bidderId'] == bidder_id:
            first_bid = False

    user_id_url = users_url + "/{}".format(bidder_id)

    user_competencies = requests.get(
        url=user_id_url,
        headers={ 'Authorization': api_key },
        params={
            'fields':'competencies.subject'
        }
    ).json()

    for competency in user_competencies["competencies"]:
        if competency["subject"]["id"] == bid_info["subject"]["id"]:
            user_has_competencies = True

    return (user_has_competencies and first_bid)


def filter_ongoing_bids(bid_list):
    """
    filter ongoing bids
    """

    result = []

    for bid in bid_list:
        # print(bid)
        if not bid['dateClosedDown']:
            result.append(bid)

    return result


def check_bid_status(bid_id):
    """
    check if there's any bidder offer their bid, if yes, choose the last bidder, if no, close the bid
    """

    bid_details_url = bid_url + "/{}".format(bid_id)

    response = requests.get(
        url=bid_details_url,
        headers={ 'Authorization': api_key },
    ).json()

    addtional_info = response['additionalInfo']

    if addtional_info['bidderRequest']:
        addtional_info['bidderRequest'][-1]['bid_chosen'] = True

        return_value = {'additionalInfo': addtional_info}

        response = requests.patch(
            url=bid_details_url,
            headers={ 'Authorization': api_key },
            json = return_value,
        ).json()

        # TODO: log this information
        # if response.status_code != 200:
        #     print(status)


def check_contract():

    user_contract = 0

    contracts = requests.get(
        url=contract_url,
        headers={ 'Authorization': api_key },
    ).json()

    for contract in contracts:
        if (contract['firstParty'] == session['user_id']) & (datetime.now() < contract['expiryDate']):
            user_contract += 1
        elif (contract['secondParty'] == session['user_id']) & (datetime.now() < contract['expiryDate']):
            user_contract += 1

    return user_contract < 5
