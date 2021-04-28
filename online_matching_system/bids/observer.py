import time
from datetime import datetime
import threading, queue
from flask import redirect, url_for, make_response
from .utils import close_bid

class BidObserver(object):

    def __init__(self,*args,**kwargs):
        self.observer_list = []
        thread = threading.Thread(target=self.count_down, args=())
        thread.start()

    def attach(self, bid_object):
        
        self.observer_list.append(bid_object)

    def detach(self, bid_object):

        self.observer_list.remove(bid_object)

    def count_down(self):

        while True:
            time.sleep(1)
            for bid in self.observer_list:
                bid.timer -= 1
                print(bid.id, bid.timer)
                if bid.timer == 0:
                    self.detach(bid)
                    print(bid.id, bid.timer)
                    status = close_bid(bid.id)
                    print(status)


class BidObject():

    def __init__(self, bid_id):
        self.timer = 10
        self.id = bid_id

    