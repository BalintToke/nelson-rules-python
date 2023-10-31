from threading import Thread
from threading import Event
from queue import Queue
from pynelson.types import NelsonRuleEvent

# A simple way to process NelsonRuleEvents and print them on screen
class Output(Thread):
    def __init__(
            self,
            exception_queue:Queue,
            stop_event:Event,
            event_queue:Queue) -> Thread:
        Thread.__init__(self)
        self.stop_event = stop_event
        self.event_queue = event_queue
        self.exception_queue=exception_queue

    def run(self):
        while not self.stop_event.is_set():
            nelson_rule_event:NelsonRuleEvent = self.event_queue.get(True)
            self.process_event(nelson_rule_event)

    def process_event(
            self,
            nelson_rule_event:NelsonRuleEvent):
        status = "CLEARED" if nelson_rule_event.clear_event else "TRIGGERED"
        timestamp = nelson_rule_event.trigger_data[len(nelson_rule_event.trigger_data)-1].timestamp
        print("-----------")
        print("Nelson Rule #"+str(nelson_rule_event.rule_id)+" ["+status+"] : "+str(timestamp))