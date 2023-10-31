from pynelson.nelson_rule_handler import NelsonRuleHandler
from sample.input import Input
from sample.output import Output
from threading import Event
from threading import Thread
from queue import Queue

# Simple console handling to check threads' health, some processing data and terminate sample process
class ConsoleHandler(Thread):
    def __init__(
            self,
            exception_queue:Queue,
            input_thread:Input,
            nelson_rule_thread:NelsonRuleHandler,
            event_thread:Output,
            stop_event:Event):
        Thread.__init__(Thread)
        self.exception_queue=exception_queue
        self.input_thread=input_thread
        self.nelson_rule_thread=nelson_rule_thread
        self.event_thread=event_thread
        self.stop_event = stop_event

    def run(self):
        command = "status"
        while not self.stop_event.is_set():
            if command == "":
                command = input("> ")
            exception_objects = []
            while True:
                try:
                    exception_objects.append(self.exception_queue.get_nowait())
                except:
                    break
            match command:
                case "status":
                    if self.input_thread.is_alive():
                        print("Input status: ACTIVE")
                    else:
                        exception = None
                        for e in exception_objects:
                            if e.thread_id == self.input_thread.ident:
                                exception=e
                        exception_message = "null" if exception == None else str(exception.exception)
                        print("Input status: STOPPED - Exception: "+exception_message)

                    if self.nelson_rule_thread.is_alive():
                        print("NelsonRuleHandler status: ACTIVE")
                    else:
                        exception = None
                        for e in exception_objects:
                            if e.thread_id == self.nelson_rule_thread.ident:
                                exception=e
                        exception_message = "null" if exception == None else str(exception.exception)
                        print("NelsonRuleHandler status: STOPPED - Exception: "+exception_message)

                    if self.event_thread.is_alive():
                        print("EventHandler status: ACTIVE")
                    else:
                        exception = None
                        for e in exception_objects:
                            if e.thread_id == self.event_thread.ident:
                                exception=e
                        exception_message = "null" if exception == None else str(exception.exception)
                        print("EventHandler status: STOPPED - Exception: "+exception_message)
                case "print":
                    self.nelson_rule_thread.request_print_data()
                case "exit":
                    self.stop_event.set()
                case "":
                    pass
                case _:
                    print("Command not found")
            command=""