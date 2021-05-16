import time
from datetime import datetime
import threading, queue
from flask import redirect, url_for, make_response
from .utils import close_bid, check_bid_status


class BidObserver(object):

    def __init__(self,*args,**kwargs):
        self.observer_list = []

    def attach(self, bid_object, bid_type):
        """
        params: bid_object, type of BidObject
        params: bid_type, a string either 'open' or 'close'
        return: -
        """
        
        self.observer_list.append(bid_object)
        print("The observer list: "+str(self.observer_list))
        print(self.observer_list)
        if bid_type.lower() == "open":
            BidTimer(bid_object, 60)
        elif bid_type.lower() == "close":
            BidTimer(bid_object, 604800)
        else:
            raise ValueError(bid_type)

    def detach(self, bid_object):
        """
        params: bid_object, type of BidObject
        To remove the bid from the observer_list and call the close_bid function to close down the bid
        return: -
        """

        if not bid_object.bought:
            bid_object.bought = True

        try:
            self.observer_list.remove(bid_object)
        except:
            pass

        status = close_bid(bid_object.id)
        
        # TODO: log the close bid information
        if (status != 200) | (status != 204):
            print(status)

    def find_and_detach(self, bid_id):
        """
        params: bid_id, a string if bid ID
        This method is for function that have only bid_id info that wants to detach the bid
        """
        # print("List before detaching: "+str(self.observer_list))
        for bid in self.observer_list:
            # print(bid.id)
            if bid.id == bid_id:
                # bid.timer = 0
                self.detach(bid)


class BidTimer():

    def __init__(self, bid_object, time):
        self.bid_object = bid_object
        self.timer = time
        self.thread = threading.Thread(target=self.count_down, args=())
        self.thread.start()

    def count_down(self):
        """
        This count down method will be called once the BidTimer is initialized with attached with the BidObject. Once the timer has reach 0, it will detach the bid
        """

        while True:
            time.sleep(1)
            self.timer -= 1
            if self.timer == 0:
                if not self.bid_object.bought:
                    # make the last bidder as the winner, or close the bid if there's no bidder
                    check_bid_status(self.bid_object.id)
                    self.bid_object.bought = True
                bid_observer.detach(self.bid_object)
                break
            if self.bid_object.bought:
                break


class BidObject():

    def __init__(self, bid_id):
        # self.timer = 0
        self.id = bid_id
        self.bought = False


bid_observer = BidObserver()