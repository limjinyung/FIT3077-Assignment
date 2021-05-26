from flask import render_template, url_for, flash, redirect, request, Blueprint, session
#from decouple import config
from datetime import datetime, timedelta
import requests
from .utils import get_contract_details
from online_matching_system.users.utils import login_required
from online_matching_system.users.utils import check_user_model
from online_matching_system.models.contract_model import contract as contract_obj

contracts = Blueprint('contracts', __name__)
api_key = 't9zQjWjQpmf7h7qGQFNfQbrQ7tfjzn'

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

    # contract_details = get_contract_details(contract_id)

    contract_details = contract_obj.get_contract_details(contract_id)

    signed = True

    duration_choices = ['', '10 Seconds', '1 Months', '3 Months', '6 Months', '12 Months', '24 Months']

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

    return render_template('contract_details.html', contract_details=contract_details, signed=signed,
                           duration_choices=duration_choices)


@contracts.route('/sign_contract/<contract_id>', methods=["POST"])
@login_required
@check_user_model
def sign_contract(contract_id):

    contract_details_url = contract_url + "/{}".format(contract_id)

    sign_contract_url = contract_url + "/{}".format(contract_id) + "/sign"
    # get the specific contract
    # contract_details = requests.get(
    #     url = contract_details_url,
    #     headers={ 'Authorization': api_key },
    # ).json()

    contract_details = contract_obj.get_contract_details(contract_id)

    print(contract_details['additionalInfo']['duration'])
    contract_length = '6 Months'
    if contract_details['additionalInfo']['duration'] is None:
        contract_length = request.form.get('contract_duration_final')
        print("True"+contract_length)
        #set default as 6 Months if user did not select a duration
        if contract_length == '':
            contract_length = '6 Months'
        contract_details['additionalInfo']['duration'] = contract_length
    print("final"+contract_length)

    # try:
    print("testing yo")
    # print(session['user_id'])
    # print(contract_details['firstParty']['id'])
    # print(session['user_id'])
    # print(contract_details['secondParty']['id'])

    if session['user_id'] == contract_details['firstParty']['id']:
        print("first")
        contract_details['additionalInfo']['signInfo']['firstPartySignedDate'] = str(datetime.now())
    if session['user_id'] == contract_details['secondParty']['id']:
        print("second")
        contract_details['additionalInfo']['signInfo']['secondPartySignedDate'] = str(datetime.now())
    # else:
    #     flash('user ID not match with any party ID. Please contact admin for help.', 'danger')
    #     return redirect('/contract')

    # check that secondPartySignedDate is signed or not
    if (contract_details['additionalInfo']['signInfo']['firstPartySignedDate'] is not None) and (contract_details['additionalInfo']['signInfo']['secondPartySignedDate'] is not None):
        if contract_details['additionalInfo']['duration'] == '10 Seconds':
            contract_details['expiryDate'] = str(datetime.now() + timedelta(seconds=10))
        if contract_details['additionalInfo']['duration'] == '1 Months':
            contract_details['expiryDate'] = str(datetime.now() + timedelta(days=31))
        if contract_details['additionalInfo']['duration'] == '3 Months':
            contract_details['expiryDate'] = str(datetime.now() + timedelta(days=91.3106))
        if contract_details['additionalInfo']['duration'] == '6 Months':
            contract_details['expiryDate'] = str(datetime.now() + timedelta(days=182.6213))
        if contract_details['additionalInfo']['duration'] == '12 Months':
            contract_details['expiryDate'] = str(datetime.now() + timedelta(days=365))
        if contract_details['additionalInfo']['duration'] == '24 Months':
            contract_details['expiryDate'] = str(datetime.now() + timedelta(days=730))

    return_value = {"expiryDate": contract_details['expiryDate'], "additionalInfo": contract_details['additionalInfo']}
    print(contract_details['additionalInfo']['signInfo']['firstPartySignedDate'])
    print(contract_details['additionalInfo']['signInfo']['secondPartySignedDate'])

    contract_update = requests.patch(
        url=contract_details_url,
        headers={'Authorization': api_key},
        json=return_value
    ).json()

    if (contract_details['additionalInfo']['signInfo']['firstPartySignedDate'] is not None) and (contract_details['additionalInfo']['signInfo']['secondPartySignedDate'] is not None):
        signed_time = {"dateSigned": str(datetime.now())}
        contract_sign = requests.post(
            url=sign_contract_url,
            headers={'Authorization': api_key},
            json=signed_time
        )

    # except Exception as e:
    #     print('Exception caught in sign_contract: {}'.format(e))

    return redirect('/contract')