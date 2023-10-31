from pynelson.nelson_rule_handler import NelsonRuleHandler
from sample.input import Input
from sample.output import Output
from sample.interface import ConsoleHandler
from threading import Event
from queue import Queue

# A simple method to showcase how to use pynelson
def main(dataRate:float):

    # Create an event to be called for to terminate all threads gracefully
    stop_event = Event()
    # Data queue containing continuously received manufacturing data as a Data object
    data_queue = Queue()
    # Event queue containing all triggered/cleared events originating from the NelsonRuleHandler as a NelsonRuleEvent object
    event_queue = Queue()
    # Exception queue to gather all exceptions originating from any currently running threads
    exception_queue = Queue()

    # Initiate input simulation
    sample_input = Input(
        exception_queue,
        stop_event,
        data_queue,
        dataRate)
    sample_input.daemon=True
    sample_input.start()

    # Initiating output handling sample
    event_handler = Output(
        exception_queue,
        stop_event,
        event_queue)
    event_handler.daemon=True
    event_handler.start()

    # Initiate the main object responsible for checking Nelson Rules against the received data 
    nelson_rule_handler = NelsonRuleHandler(
        exception_queue,
        stop_event,
        data_queue,
        event_queue,
        dataRate)
    nelson_rule_handler.daemon=True
    nelson_rule_handler.start()

    # A simple console
    console_handler = ConsoleHandler(
        exception_queue,
        sample_input,
        nelson_rule_handler,
        event_handler,
        stop_event)
    console_handler.daemon=True
    console_handler.start()

    while not stop_event.is_set():
        continue

    print("Program terminated")

if __name__ == "__main__":
    main(0.2)