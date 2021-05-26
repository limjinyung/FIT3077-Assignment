from flask import render_template, url_for, flash, redirect, request, Blueprint, session
from decouple import config
from datetime import datetime, timedelta
import requests
from .utils import get_contract_details
from online_matching_system.users.utils import check_user_model, get_user_role, login_required
from online_matching_system.models.contract_model import contract as contract_obj
from online_matching_system.models.user_model import student
import operator

contracts = Blueprint('contracts', __name__)
api_key = config('FIT3077_API')

root_url = 'https://fit3077.com/api/v2'
contract_url = root_url + "/contract"


@contracts.route('/contract', methods=["GET"])
@login_required
@check_user_model
def contract_index():
    
    # get all the contract from API
    # contract_list = requests.get(
    #     url = contract_url,
    #     headers={ 'Authorization': api_key },
    # ).json()

    contract_list = contract_obj.get_contract_list()

    user_contract = []
    user_id = session["user_id"]

    for contract in contract_list:
        if (contract["firstParty"]["id"] == user_id) | (contract["secondParty"]["id"] == user_id):
            user_contract.append(contract)

    return render_template('contract.html', user_contract=user_contract)


@contracts.route('/contract_details/<contract_id>', methods=["GET"])
@login_required
@check_user_model
def contract_details(contract_id):

    preferred_time_list = ['08:00', '08:30', '09:00', '09:30', '10:00', '10:30', '11:00', '11:30', '12:00', '12:30','13:00', '13:30', '14:00', '14:30', '15:00', '15:30', '16:00', '16:30', '17:00', '17:30','18:00', '18:30']
    preferred_day_list = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    preferred_rate_choice = ['per hour', 'per session']
    preferred_hours_per_lesson = ['00:30', '01:00', '01:30', '02:00', '02:30', '03:00']

    # get the contract object
    contract_details = contract_obj.get_contract_details(contract_id)

    # check if the contract was expired
    contract_expired_date = datetime.strptime(contract_details['expiryDate'], "%Y-%m-%dT%H:%M:%S.%fZ")
    contract_expired = datetime.now() > contract_expired_date

    # check if the contract was signed
    signed = True

    try:
        if contract_details['firstParty']['id'] == session['user_id']:
            if not contract_details['additionalInfo']['signInfo']['firstPartySignedDate']:
                signed = False
        elif contract_details['secondParty']['id'] == session['user_id']:
            if not contract_details['additionalInfo']['signInfo']['secondPartySignedDate']:
                signed = False
        else:
            flash("There's something wrong with this contract. Please contact the admin.", "danger")
            return redirect("/contract")
    except Exception as e:
        print('Exception caught in contract_details: {}'.format(e))

    # get the five latest contract
    user_role = get_user_role()
    contract_reference_list = user_role.user_contracts[:4]

    # get user_info
    user_info = user_role.user_details

    return render_template('contract_details.html', contract_details=contract_details, signed=signed, contract_expired=contract_expired, user_info=user_info, contract_reference_list=contract_reference_list, preferred_time_list=preferred_time_list, preferred_day_list=preferred_day_list, preferred_rate_choice=preferred_rate_choice, preferred_hours_per_lesson=preferred_hours_per_lesson)


@contracts.route('/sign_contract/<contract_id>', methods=["POST"])
@login_required
@check_user_model
def sign_contract(contract_id):

    contract_details_url = contract_url + "/{}".format(contract_id)

    contract_details = contract_obj.get_contract_details(contract_id)

    try:
        if session['user_id'] == contract_details['firstParty']['id']:

            contract_details['additionalInfo']['signInfo']['firstPartySignedDate'] = str(datetime.now())
        elif session['user_id'] == contract_details['secondParty']['id']:
            contract_details['additionalInfo']['signInfo']['secondPartySignedDate'] = str(datetime.now())
        else:
            flash('user ID not match with any party ID. Please contact admin for help.', 'danger')
            return redirect('/contract')

        return_value = {"additionalInfo": contract_details['additionalInfo']}

        contract_update = requests.patch(
            url = contract_details_url,
            headers={ 'Authorization': api_key },
            json= return_value
        ).json()

        # update the contract model after PATCH
        contract_obj.update_contract_list()

        # check if both parties signed the contract
        check_both_parties_signed(contract_id)

    except Exception as e:
        print('Exception caught in sign_contract: {}'.format(e))

    return redirect('/contract')


def check_both_parties_signed(contract_id):

    contract_details = contract_obj.get_contract_details(contract_id)

    if (contract_details['additionalInfo']['signInfo']['firstPartySignedDate'] and contract_details['additionalInfo']['signInfo']['secondPartySignedDate']) and not contract_details['dateSigned']:
        
        sign_contract = requests.post(
            url = root_url + "/contract/{}/sign".format(contract_id),
            headers={ 'Authorization': api_key },
            data={"dateSigned":datetime.now()}
        ).json()

        # if sign_contract.status_code == 200:
        #     print('contract signed complete')
        # else:
        #     raise Exception("There's something wrong signing the contract")
        print(sign_contract)
    elif (contract_details['additionalInfo']['signInfo']['firstPartySignedDate'] and contract_details['additionalInfo']['signInfo']['secondPartySignedDate']) and contract_details['dateSigned']:
        raise Exception('Contract signed already')
    else:
        pass


@contracts.route('/reuse_contract', methods=["POST"])
@login_required
def reuse_contract():

    # declare variable
    student_subject_level = ''
    tutor_subject_level = ''

    # get data from form
    chosen_contract = request.form.get('chosen_contract')
    chosen_tutor = request.form.get('new_tutor')
    contract_id = request.form.get('contract_id')

    # get the contract that student choose to reuse
    chosen_contract = contract_obj.get_contract_details(chosen_contract)

    # if the tutor is the new tutor, check the tutor competency
    if chosen_tutor == 'new':
        tutor_id = request.form.get('new_tutor_id')
        contract_subject = chosen_contract['subject']['id']

        # get the competency list
        competencies_list = requests.get(
            url=root_url+'/competency',
            headers={ 'Authorization': api_key },
        ).json()

        # loop through the competency list and find student, tutor subject level
        for competency in competencies_list:
            if competency['subject']['id'] == contract_subject and competency['owner']['id'] == session['user_id']:
                student_subject_level = competency['level']
            if competency['subject']['id'] == contract_subject and competency['owner']['id'] == tutor_id:
                tutor_subject_level = competency['level']
        
        # check the competency level is valid
        if student_subject_level and tutor_subject_level:
            if (tutor_subject_level - student_subject_level) >= 2:
                pass
            else:
                flash('This tutor has not enough competency level in this subject', 'warning')
                return redirect('/contract_details/{}'.format(contract_id))
        else:
            # if can't find the tutor ID, return and flash error message
            if not tutor_subject_level:
                flash("Can't find tutor with this ID")
                return redirect('/contract_details/{}'.format(contract_id))
            else:
                raise Exception("Can't find either student level or tutor level in reuse_contract function.")
    else:
        tutor_id = request.form.get('current_tutor_id')

    # create the json to POST data
    contract_json = {
        "firstPartyId": chosen_contract['firstParty']['id'],
        "secondPartyId": chosen_contract['secondParty']['id'],
        "subjectId": chosen_contract['subject']['id'],
        "dateCreated": str(datetime.now()),
        "expiryDate": str(datetime.now() + timedelta(seconds=120)),
        "paymentInfo": {},
        "lessonInfo": {
            "bidderId":chosen_contract['lessonInfo']['bidderId'],
            "numberOfLesson":chosen_contract['lessonInfo']['numberOfLesson'],
            "hoursPerLesson":chosen_contract['lessonInfo']['hoursPerLesson'],
            "lessonTime":chosen_contract['lessonInfo']['lessonTime'],
            "lessonDay":chosen_contract['lessonInfo']['lessonDay'],
            "lessonPerWeek":chosen_contract['lessonInfo']['lessonPerWeek'],
            "freeLesson":chosen_contract['lessonInfo']['freeLesson'],
            "lessonRateChoice":chosen_contract['lessonInfo']['lessonRateChoice'],
            "lessonRate":chosen_contract['lessonInfo']['lessonRate'],
        },
        "additionalInfo": {
            "signInfo":{
                "firstPartySignedDate": None,
                "secondPartySignedDate": None,
            },
        }
    }

    # POST data
    post_contract = requests.post(
        url = contract_url,
        headers={ 'Authorization': api_key },
        json = contract_json
    ).json()

    return redirect('/contract')