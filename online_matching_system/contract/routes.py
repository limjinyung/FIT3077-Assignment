from flask import render_template, url_for, flash, redirect, request, Blueprint, session
from decouple import config
from datetime import datetime
import requests

contract = Blueprint('contract', __name__)
api_key = config('FIT3077')

root_url = 'https://fit3077.com/api/v1'
contract_url = root_url + "/contract"


@contract.route('/contract', methods=["GET"])
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

    return render_template('contract.html', user_contract=user_contract)


