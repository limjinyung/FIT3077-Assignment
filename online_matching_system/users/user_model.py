from abc import ABCMeta
from flask import session
import requests
from datetime import datetime
from decouple import config

api_key = config('FIT3077_API')
root_url = 'https://fit3077.com/api/v1/'

class UserModel():
    __metaclass__ = ABCMeta 

    def __init__(self):
        self.user_id = None
        self.initialized = False
        self.user_details = None
        self.user_competencies = None
        self.user_qualifications = None
        self.user_bids = None
        self.user_contracts = None
        self.is_student = None
        self.is_tutor = None

    def __str__(self):
        return "{}, {}".format(self.user_id ,self.initialized)
        
    def get_user_id(self):

        self.user_id = session.get('user_id',0)

    def get_user_details(self):
        """
        get user's details from API
        format: JSON
        """

        user_id_url = root_url + "/{}/{}".format("user", session['user_id'])

        user_details = requests.get(
            url=user_id_url,
            headers={ 'Authorization': api_key },
        ).json()

        self.user_details = user_details


    def get_user_competencies(self):
        """
        get user's competency from API
        format: a list of JSON 
        """

        user_id_url = root_url + "/{}/{}".format("user", session['user_id'])

        user_competencies = requests.get(
            url=user_id_url,
            headers={ 'Authorization': api_key },
            params={
                'fields':'competencies.subject'
            }
        ).json()
        
        self.user_competencies = user_competencies['competencies']


    def get_user_qualifications(self):
        """
        get user's qualification from API
        format: a list of JSON 
        """

        user_id_url = root_url + "/{}/{}".format("user", session['user_id'])

        user_qualifications = requests.get(
            url=user_id_url,
            headers={ 'Authorization': api_key },
            params={
                'fields':'qualifications'
            }
        ).json()

        self.user_qualifications = user_qualifications['qualifications']

    def get_user_role(self):
        """
        check isStudent and isTutor
        format: boolean
        """

        user_id_url = root_url + "/{}/{}".format("user", session['user_id'])

        user_info = requests.get(
            url=user_id_url,
            headers={ 'Authorization': api_key },
        ).json()

        self.isStudent = user_info['isStudent']
        self.isTutor = user_info['isTutor']


    def get_user_bids(self):
        """
        get user's bid from API
        format: a list of JSON
        """

        user_id_url = root_url + "/{}/{}".format("user", session['user_id'])

        user_bids = requests.get(
            url=user_id_url,
            headers={ 'Authorization': api_key },
            params={
                'fields':'initiatedBids'
            }
        ).json()

        self.user_bids = user_bids['initiatedBids']

    def check_initialized(self):

        return self.initialized


class StudentModel(UserModel):

    def __init__(self):
        UserModel.__init__(self)
        self.contract_number = 0

    def get_contract_number(self):
        """
        get the number of contract that a student have
        format: integer
        """

        user_contract = 0

        contracts = requests.get(
            url=root_url + "/{}".format("contract"),
            headers={ 'Authorization': api_key },
        ).json()

        for contract in contracts:
            expiry_date = datetime.strptime(contract['expiryDate'], "%Y-%m-%dT%H:%M:%S.%fZ")
            if (contract['firstParty'] == session['user_id']) & (datetime.now() < expiry_date):
                user_contract += 1
            elif (contract['secondParty'] == session['user_id']) & (datetime.now() < expiry_date):
                user_contract += 1

        self.contract_number = user_contract


class TutorModel(UserModel):

    def __init__(self):
        UserModel.__init__(self)
        self.bid_monitor_list = []


student = StudentModel()
tutor = TutorModel()