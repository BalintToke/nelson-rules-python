import datetime

class Data:
    """Represents a single data point originating from any manufacturing process
            
    Arguments:
    - value: Current value
    - id: Any sort of identification, defaults to None
    - timestamp: Timestamp of the received data, defaults to the current system time
    """

    def __init__(
            self,
            value,
            id=None,
            timestamp=None) -> None:
        
        if not isinstance(value,int) and not isinstance(value,float):
            raise ValueError("Invalid Data value")

        self.value=value
        self.id=id
        if timestamp==None:
            self.timestamp=datetime.datetime.now().timestamp()
        else:
            self.timestamp=timestamp

class NelsonRuleEvent:
    """Schema to represent any event triggered/cleared by a Nelson Rule
            
    Arguments:
    - rule_id: 1-indexed identification of a rule [1-8]
    - clear_event: True if this event is supposed to clear a previously triggered event, False otherwise
    - trigger_data: Depending on the rule, contains the values responsible for triggering/clearing an event
    """
            
    def __init__(
            self,
            rule_id:int,
            clear_event:bool,
            trigger_data:[]) -> None:
        self.rule_id=rule_id
        self.clear_event=clear_event
        self.trigger_data=trigger_data

class ExceptionEvent:
    """Unified schema to represent an Exception raised by any threads used during the process
            
    Arguments:
    - thread_id: Identification of the thread that raised an exception
    - exception: Exception object raised by the thread
    """
            
    def __init__(
            self,
            thread_id,
            exception) -> None:
        self.thread_id=thread_id
        self.exception=exception