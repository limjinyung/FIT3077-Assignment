from flask import flash
from datetime import datetime, timedelta
#from decouple import config
import requests
from online_matching_system.models.bid_model import search_bids

api_key = 't9zQjWjQpmf7h7qGQFNfQbrQ7tfjzn'

root_url = 'https://fit3077.com/api/v2'
bid_url = root_url + "/bid"
contract_url = root_url + "/contract"

def get_contract_details(contract_id):
    """
    params: contract_id: a contract ID string 
    to get the specific contract details from API
    return a JSON format of contract details
    """

    contract_details_url = contract_url + "/{}".format(contract_id)

    contract_details = requests.get(
        url=contract_details_url,
        headers={ 'Authorization': api_key },
    ).json()

    return contract_details

def generate_contract(bid_id):
    """
    params: bid_id: a bid ID string
    to generate a contract based on the bid_id given. The contract details will be obtained from the bid_id. An additionalInfo will be added to indicate first and second party sign date
    return: the response of POST request to the API
    """

    bid_details_url = bid_url + "/{}".format(bid_id)
    # bid_details = requests.get(
    #     url=bid_details_url,
    #     headers={ 'Authorization': api_key },
    #     params={'fields':'messages'}
    # ).json()

    bid_details = search_bids(bid_id)

    requestor_id = bid_details['initiator']['id']
    subject_id = bid_details['subject']['id']

    if bid_details['type'] == 'Open':
        if not bid_details['additionalInfo']['bidderRequest']:
            print("There are no offer in this bid. No contract will be generated.")
            return None

        # loop and find the bidder that wins the bid
        for bidder in bid_details['additionalInfo']['bidderRequest']:
            if bidder['bid_chosen']:
                bidder_id = bidder['bidderId']
                number_of_lesson = bidder['numberOfLessonOffered']
                hours_per_lesson = bidder['hoursPerLessonOffered']
                lesson_time = bidder['preferredTimeOffered']
                lesson_day = bidder['preferredDayOffered']
                lesson_per_week = bidder['sessionPerWeekOffered']
                free_lesson = bidder['freeLesson']
                lesson_rate_choice = bidder['rateChoiceOffered']
                lesson_rate = bidder['rateRequest']

    if bid_details['type'] == 'Close':
        if len(bid_details['messages']) == 0:
            print("There are no offer in this bid. No contract will be generated.")
            return None

        for bids in bid_details['messages']:
            if bids['additionalInfo']['bid_chosen']:
                bidder_id = bids['poster']['id']
                number_of_lesson = bids['additionalInfo']['lessonNeeded']
                hours_per_lesson = bids['additionalInfo']['preferredHours']
                lesson_time = bids['additionalInfo']['preferredTime']
                lesson_day = bids['additionalInfo']['preferredDay']
                lesson_per_week = bids['additionalInfo']['preferredSessionPerWeek']
                free_lesson = bids['additionalInfo']['freeLesson']
                lesson_rate_choice = bids['additionalInfo']['preferredRateChoice']
                lesson_rate = bids['additionalInfo']['preferredRate']
                break

    contract_json = {
        "firstPartyId": requestor_id,
        "secondPartyId": bidder_id,
        "subjectId": subject_id,
        "dateCreated": str(datetime.now()),
        "expiryDate": str(datetime.now() + timedelta(days=365)),
        "paymentInfo": {},
        "lessonInfo": {
            "bidderId":bidder_id,
            "numberOfLesson":number_of_lesson,
            "hoursPerLesson":hours_per_lesson,
            "lessonTime":lesson_time,
            "lessonDay":lesson_day,
            "lessonPerWeek":lesson_per_week,
            "freeLesson":free_lesson,
            "lessonRateChoice":lesson_rate_choice,
            "lessonRate":lesson_rate,
        },
        "additionalInfo": {
            "signInfo":{
                "firstPartySignedDate": None,
                "secondPartySignedDate": None,
            },
            "expired": False,
            "duration": None
        }
    }

    post_contract = requests.post(
        url = contract_url,
        headers={ 'Authorization': api_key },
        json = contract_json
    ).json()

    return post_contract


def check_expired(all_contracts):
    print(all_contracts)
    for contracts in all_contracts:
        if contracts['dateSigned'] is not None and contracts['terminationDate'] is None:
            expiry_date = datetime.strptime(contracts['expiryDate'][:19], "%Y-%m-%dT%H:%M:%S")
            current_time = datetime.now()
            difference = expiry_date - current_time
            days = divmod(difference.days, 86400)
            # check if the time remaining is one month left
            print(days)
            if (days[1] <= 31) and (days[1] > 0):
                flash("Contract for subject " + contracts['subject']['name'] + " with "
                      + contracts['secondParty']['familyName'] + " " + contracts['secondParty']['givenName']
                      + " has less than 1 month remaining!", "warning")
            if days[0] < 0:
                contracts['additionalInfo']['expired'] = True
                update_contract_url = contract_url + "/{}".format(contracts['id'])
                print(update_contract_url)
                updated_info = {"additionalInfo": contracts['additionalInfo']}
                print(updated_info)
                update_contract = requests.patch(
                    url=update_contract_url,
                    headers={'Authorization': api_key},
                    json=updated_info
                )
                print(update_contract.status_code)
                flash("Contract for subject " + contracts['subject']['name'] + " with "
                      + contracts['secondParty']['familyName'] + " " + contracts['secondParty']['givenName']
                      + " has expired", "warning")
