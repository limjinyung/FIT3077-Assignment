from flask import render_template, url_for, flash, redirect, request, Blueprint, session
from decouple import config
from datetime import datetime
import requests
from .utils import get_contract_details
from online_matching_system.users.utils import login_required
from online_matching_system.users.utils import check_user_model

contracts = Blueprint('contracts', __name__)
api_key = config('FIT3077_API')

root_url = 'https://fit3077.com/api/v2'
contract_url = root_url + "/contract"


@contracts.route('/contract', methods=["GET"])
@login_required
@check_user_model
def contract_index():
    
    # get all the contract from API
    contract_list = requests.get(
        url = contract_url,
        headers={ 'Authorization': api_key },
    ).json()

    user_contract = []
    user_id = session["user_id"]

    for contract in contract_list:
        if (contract["firstParty"]["id"] == user_id) | (contract["secondParty"]["id"] == user_id):
            user_contract.append(contract)

    # print(contract)

    return render_template('contract.html', user_contract=user_contract)


@contracts.route('/contract_details/<contract_id>', methods=["GET"])
@login_required
@check_user_model
def contract_details(contract_id):

    contract_details = get_contract_details(contract_id)

    signed = True

    if contract_details['firstParty']['id'] == session['user_id']:
        if not contract_details['additionalInfo']['signInfo']['firstPartySignedDate']:
            signed = False
    elif contract_details['secondParty']['id'] == session['user_id']:
        if not contract_details['additionalInfo']['signInfo']['secondPartySignedDate']:
            signed = False
    else:
        flash("There's something wrong with this contract. Please contact the admin.", "danger")
        return redirect("/contract")

    return render_template('contract_details.html', contract_details=contract_details, signed=signed)


@contracts.route('/sign_contract/<contract_id>', methods=["POST"])
@login_required
@check_user_model
def sign_contract(contract_id):

    contract_details_url = contract_url + "/{}".format(contract_id)

    # get the specific contract
    contract_details = requests.get(
        url = contract_details_url,
        headers={ 'Authorization': api_key },
    ).json()

    if session['user_id'] == contract_details['firstParty']['id']:

        contract_details['additionalInfo']['signInfo']['firstPartySignedDate'] = str(datetime.now())
    elif session['user_id'] == contract_details['secondParty']['id']:
        contract_details['additionalInfo']['signInfo']['secondPartySignedDate'] = str(datetime.now())
    else:
        flash('user ID not match with any party ID. Please contact admin for help.', 'danger')
        return redirect('/contract')

    return_value = {"additionalInfo": contract_details['additionalInfo']}

    print(return_value)

    contract_update = requests.patch(
        url = contract_details_url,
        headers={ 'Authorization': api_key },
        json= return_value
    ).json()

    print(contract_update)

    return redirect('/contract')