from datetime import datetime, timedelta
from decouple import config
import requests

api_key = config('FIT3077')

root_url = 'https://fit3077.com/api/v1'
bid_url = root_url + "/bid"
contract_url = root_url + "/contract"

def generate_contract(bid_id):

    bid_details_url = bid_url + "/{}".format(bid_id)

    bid_details = requests.get(
        url=bid_details_url,
        headers={ 'Authorization': api_key },
    ).json()

    requestor_id = bid_details['initiator']['id']
    subject_id = bid_details['subject']['id']

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
            "signInfo":{}
        }
    }

    post_contract = requests.post(
        url = contract_url,
        headers={ 'Authorization': api_key },
        json = contract_json
    ).json()

    print(post_contract)

    # if post_contract.status_code == 201:
    #     print("contract generate successfully")
    # else:
    #     print("there's something wrong generating the contract. Please try again.")

    return post_contract
