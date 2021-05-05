from datetime import datetime, timedelta
from decouple import config
import requests

api_key = config('FIT3077_API')

root_url = 'https://fit3077.com/api/v1'
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
    print("The bid details url: "+str(bid_details_url))
    bid_details = requests.get(
        url=bid_details_url,
        headers={ 'Authorization': api_key },
        params={'fields':'messages'}
    ).json()
    print(bid_details_url)

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
            }
        }
    }

    post_contract = requests.post(
        url = contract_url,
        headers={ 'Authorization': api_key },
        json = contract_json
    ).json()

    return post_contract
