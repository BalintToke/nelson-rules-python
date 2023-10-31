from threading import Thread
from threading import Event
from pynelson.types import Data 
import random
from queue import Queue
from datetime import datetime

# Simple random input simulation
class Input(Thread):
    def __init__(
            self,
            exception_queue:Queue,
            stop_event:Event,
            data_queue:Queue,
            data_rate:float,
            min_value:int=1,
            max_value:int=1000) -> None:
        Thread.__init__(self)
        self.exception_queue=exception_queue
        self.stop_event = stop_event
        self.data_queue = data_queue
        self.data_rate=data_rate
        self.min_value = min_value
        self.max_value = max_value

    def run(self):
        try:
            while not self.stop_event.wait(self.data_rate):
                self.data_queue.put(Data(random.randrange(self.min_value,self.max_value,1),None,datetime.now()))
        except:
            pass
    

    