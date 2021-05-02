import time
from datetime import datetime
import threading, queue
from flask import redirect, url_for, make_response
from .utils import close_bid, check_bid_status


class BidObserver(object):

    def __init__(self,*args,**kwargs):
        self.observer_list = []

    def attach(self, bid_object):
        
        self.observer_list.append(bid_object)
        BidTimer(bid_object)

    def detach(self, bid_object):

        if not bid_object.bought:
            bid_object.bought = True

        try:
            self.observer_list.remove(bid_object)
        except:
            pass

        status = close_bid(bid_object.id)
        
        # TODO: log the close bid information
        if (status != 200) | (status !=  204):
            print(status)

    def find_and_detach(self, bid_id):
        for bid in self.observer_list:
            if bid.id == bid_id:
                bid.timer = 0
                # self.detach(bid)


class BidTimer():

    def __init__(self, bid_object):
        self.bid_object = bid_object
        self.timer = 60
        self.thread = threading.Thread(target=self.count_down, args=())
        self.thread.start()

    def count_down(self):

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

        # self.thread.terminate()


class BidObject():

    def __init__(self, bid_id):
        # self.timer = 60
        self.id = bid_id
        self.bought = False


bid_observer = BidObserver()