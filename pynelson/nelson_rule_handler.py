from threading import Thread
from threading import Event
from pynelson.types import Data,NelsonRuleEvent,ExceptionEvent
from queue import Queue
import sys
import math
import pynelson

class NelsonRuleHandler(Thread):
    """Apply Nelson Rules to a continuous process

    Creates a thread to check all received data if they trigger a Nelson Rule. Data is aggregated, and stores the last 15 at all times.
    
    Requires: queues for exceptions, data and events; stop event to signal thread to terminate gracefully and the data rate from the manufacturing process

    Arguments:   
    - exception_queue -- If an exception occurs during any process, put a NelsonRuleException object inside of it
    - stop_event -- Event to stop thread
    - data_queue -- Containts the manufacturing data arriving from any source, data is wrapped in a Data object
    - event_queue -- If a Nelson Rule is triggered/cleared, place NelsonRuleEvent inside of this queue
    - data_rate -- The data rate of the currently running manufacturing process
    """

    def __init__(
            self,
            exception_queue:Queue,
            stop_event:Event,
            data_queue:Queue,
            event_queue:Queue,
            data_rate:float) -> None:
        Thread.__init__(self)
        self.exception_queue=exception_queue
        self.stop_event=stop_event
        self.data_queue = data_queue
        self.event_queue=event_queue
        self.data_rate=data_rate

        self.print_data = False

        self.previous_data:Data = None
        self.data_sum:float = 0
        self.data_count = 0
        self.deviation_sq_sums:float = 0 # Sum of the deviation of elements squared
        self.mean=0
        self.standard_deviation=0

        # NR 2 variables
        self.same_side_mean_count = 0

        # NR 3 variables
        self.rule3_increasing = False
        self.continuous_slope_change_count = 0

        # NR 4 variables
        self.expect_increase = False
        self.continuous_alt_direction_count=0

        # NR 5+6 variables
        self.data_window = [Data]*15
        self.data_window_len=len(self.data_window)

        # NR 7 variables
        self.within_standard_deviation_count = 0

        # NR 8 variables
        self.none_within_standard_deviation_count = 0
        self.none_within_standard_deviation_sides = [False,False]

        # Events
        self.nelson_rule_1_event = Event()
        self.nelson_rule_2_event = Event()
        self.nelson_rule_3_event = Event()
        self.nelson_rule_4_event = Event()
        self.nelson_rule_5_event = Event()
        self.nelson_rule_6_event = Event()
        self.nelson_rule_7_event = Event()
        self.nelson_rule_8_event = Event()
    
    # Runs at thread start
    def run(self):
        while not self.stop_event.is_set():
            try:
                data:Data = self.data_queue.get(True)
                if self.print_data:
                    print(str(self.data_sum)+"/"+str(self.data_count)+" -> "+str(data.value)+" <"+str(self.standard_deviation)+">",)
                    self.print_data=False
                if self.data_count>pynelson.IGNORE_FIRST_ELEMENTS_COUNT:
                    self.apply_nelson_rule_1(data)
                    self.apply_nelson_rule_2(data)
                    self.apply_nelson_rule_3(data)
                    self.apply_nelson_rule_4(data)
                    self.apply_nelson_rule_5(data)
                    self.apply_nelson_rule_6(data)
                    self.apply_nelson_rule_7(data)
                    self.apply_nelson_rule_8(data)
                
                # Shifting array to the left, placing new data to the right
                for i in range(1,self.data_window_len):
                    self.data_window[i-1]=self.data_window[i]
                self.data_window[self.data_window_len-1]=data

                # Add data to the accumulated values
                self.data_sum+=data.value
                self.data_count+=1
                self.deviation_sq_sums+=((self.data_sum/self.data_count)-data.value)*((self.data_sum/self.data_count)-data.value)

                # Calculate mean and standard deviation, make sure to put this after accumulating data
                self.mean = self.data_sum/self.data_count
                self.standard_deviation = math.sqrt(self.deviation_sq_sums/self.data_count)
                
                # Save previous element
                self.previous_data=data

                # Check memory size to avoid running out of memory
                if self.data_count%10000==0:
                    self.resize_memory()

            except Exception as e:
                self.exception_queue.put(
                    ExceptionEvent(self.ident,e))
                break

    # One point is more than 3 standard deviations from the mean.
    def apply_nelson_rule_1(
            self,
            data:Data):
        value = data.value
        if value>self.mean+3*self.standard_deviation or value<self.mean-3*self.standard_deviation:
            if not self.nelson_rule_1_event.is_set():
                # print("[NELSON RULE 1 TRIGGERED] -> data: "+str(value)+" | mean: "+str(self.mean)+" | SD: "+str(self.standardDeviation))
                self.nelson_rule_1_event.set()
                self.event_queue.put(
                    NelsonRuleEvent(
                        1,
                        False,
                        [data])
                    )
        else:
            if self.nelson_rule_1_event.is_set():
                # print("[NELSON RULE 1 CLEARED]")
                self.nelson_rule_1_event.clear()
                self.event_queue.put(
                    NelsonRuleEvent(
                        1,
                        True,
                        [data])
                    )

    # Nine (or more) points in a row are on the same side of the mean.
    def apply_nelson_rule_2(
            self,
            data:Data):
        value = data.value
        if self.same_side_mean_count>=9:
            if not self.nelson_rule_2_event.is_set():
                self.nelson_rule_2_event.set()
                self.event_queue.put(
                    NelsonRuleEvent(
                        2,
                        False,
                        self.data_window[self.data_window_len-9:self.data_window_len-1])
                    )
        else:
            if self.nelson_rule_2_event.is_set():
                self.nelson_rule_2_event.clear()
                self.event_queue.put(
                    NelsonRuleEvent(
                        2,
                        True,
                        self.data_window[self.data_window_len-9:self.data_window_len-1])
                    )

        if (self.previous_data.value>=self.mean and value>=self.mean) or (self.previous_data.value<self.mean and value<self.mean):
            self.same_side_mean_count+=1
        else:
            self.same_side_mean_count=0

    # Six (or more) points in a row are continually increasing (or decreasing).
    def apply_nelson_rule_3(
            self,
            data:Data):
        value = data.value
        if self.continuous_slope_change_count>=6:
            if not self.nelson_rule_3_event.is_set():
                self.nelson_rule_3_event.set()
                self.event_queue.put(
                    NelsonRuleEvent(
                        3,
                        False,
                        self.data_window[self.data_window_len-6:self.data_window_len-1])
                    )
        else:
            if self.nelson_rule_3_event.is_set():
                self.nelson_rule_3_event.clear()
                self.event_queue.put(
                    NelsonRuleEvent(
                        3,
                        True,
                        self.data_window[self.data_window_len-6:self.data_window_len-1])
                    )

        if self.previous_data.value<value:
            if self.rule3_increasing:
                self.continuous_slope_change_count+=1
            else:
                self.continuous_slope_change_count=0
                self.rule3_increasing=True
        if self.previous_data.value>value:
            if not self.rule3_increasing:
                self.continuous_slope_change_count+=1
            else:
                self.continuous_slope_change_count=0
                self.rule3_increasing=False

    # Fourteen (or more) points in a row alternate in direction, increasing then decreasing.
    def apply_nelson_rule_4(
            self,
            data:Data):
        value = data.value
        if self.continuous_alt_direction_count>=14:
            if not self.nelson_rule_4_event.is_set():
                self.nelson_rule_4_event.set()
                self.event_queue.put(
                    NelsonRuleEvent(
                        4,
                        False,
                        self.data_window[self.data_window_len-14:self.data_window_len-1])
                    )
        else:
            if self.nelson_rule_4_event.is_set():
                self.nelson_rule_4_event.clear()
                self.event_queue.put(
                    NelsonRuleEvent(
                        4,
                        True,
                        self.data_window[self.data_window_len-14:self.data_window_len-1])
                    )

        if self.previous_data.value<value:
            if self.expect_increase:
                self.continuous_alt_direction_count+=1
            else:
                self.continuous_alt_direction_count=1
            self.expect_increase=False
        elif self.previous_data.value>value:
            if self.expect_increase:
                self.continuous_alt_direction_count=1
            else:
                self.continuous_alt_direction_count+=1
            self.expect_increase=True
        else:
            self.continuous_alt_direction_count=0
    
    # Two (or three) out of three points in a row are more than 2 standard deviations from the mean in the same direction.
    def apply_nelson_rule_5(
            self,
            data:Data):
        pos_count = 0
        pos_count_max = 0
        neg_count = 0
        neg_count_max = 0
        
        for i in range(self.data_window_len-3,self.data_window_len):
            if self.data_window[i].value>(self.mean+2*self.standard_deviation):
                pos_count+=1
            elif self.data_window[i].value<(self.mean-2*self.standard_deviation):
                neg_count+=1

            if neg_count>0:
                neg_count_max = self.get_max([neg_count,neg_count_max])
            if pos_count>0:
                pos_count_max = self.get_max([pos_count,pos_count_max])

        if pos_count_max>=2 or neg_count_max>=2:
            if not self.nelson_rule_5_event.is_set():
                self.nelson_rule_5_event.set()
                self.event_queue.put(
                    NelsonRuleEvent(
                        5,
                        False,
                        self.data_window[self.data_window_len-3:self.data_window_len-1])
                    )
        else:
            if self.nelson_rule_5_event.is_set():
                self.nelson_rule_5_event.clear()
                self.event_queue.put(
                    NelsonRuleEvent(
                        5,
                        True,
                        self.data_window[self.data_window_len-3:self.data_window_len-1])
                    )

    # Four (or five) out of five points in a row are more than 1 standard deviation from the mean in the same direction.
    def apply_nelson_rule_6(
            self,
            data:Data):
        pos_count = 0
        pos_count_max = 0
        neg_count = 0
        neg_count_max = 0

        for i in range(self.data_window_len-5,self.data_window_len):
            if self.data_window[i].value>(self.mean+self.standard_deviation):
                pos_count+=1
            elif self.data_window[i].value<(self.mean-self.standard_deviation):
                neg_count+=1

            if neg_count>0:
                neg_count_max = self.get_max([neg_count,neg_count_max])
            if pos_count>0:
                pos_count_max = self.get_max([pos_count,pos_count_max])

        if pos_count_max>=4 or neg_count_max>=4:
            if not self.nelson_rule_6_event.is_set():
                self.nelson_rule_6_event.set()
                self.event_queue.put(
                    NelsonRuleEvent(
                        6,
                        False,
                        self.data_window[self.data_window_len-5:self.data_window_len-1])
                    )
        else:
            if self.nelson_rule_6_event.is_set():
                self.nelson_rule_6_event.clear()
                self.event_queue.put(
                    NelsonRuleEvent(
                        6,
                        True,
                        self.data_window[self.data_window_len-5:self.data_window_len-1])
                    )

    # Fifteen points in a row are all within 1 standard deviation of the mean on either side of the mean.
    def apply_nelson_rule_7(
            self,
            data:Data):
        value = data.value
        if self.within_standard_deviation_count>=15:
            if not self.nelson_rule_7_event.is_set():
                self.nelson_rule_7_event.set()
                self.event_queue.put(
                    NelsonRuleEvent(
                        7,
                        False,
                        self.data_window[self.data_window_len-15:self.data_window_len-1])
                    )
        else:
            if self.nelson_rule_7_event.is_set():
                self.nelson_rule_7_event.clear()
                self.event_queue.put(
                    NelsonRuleEvent(
                        7,
                        True,
                        self.data_window[self.data_window_len-15:self.data_window_len-1])
                    )

        if value>=self.mean-self.standard_deviation and value<=self.mean+self.standard_deviation:
            self.within_standard_deviation_count+=1
        else:
            self.within_standard_deviation_count=0

    # Eight points in a row exist, but none within 1 standard deviation of the mean, and the points are in both directions from the mean.
    def apply_nelson_rule_8(
            self,
            data:Data):
        value = data.value
        if self.none_within_standard_deviation_count>=8 and self.none_within_standard_deviation_sides==[True,True]:
                if not self.nelson_rule_8_event.is_set():
                    self.nelson_rule_8_event.set()
                    self.event_queue.put(
                        NelsonRuleEvent(
                            8,
                            False,
                            self.data_window[self.data_window_len-8:self.data_window_len-1])
                        )
        else:
            if self.nelson_rule_8_event.is_set():
                self.nelson_rule_8_event.clear()
                self.event_queue.put(
                    NelsonRuleEvent(
                        8,
                        True,
                        self.data_window[self.data_window_len-8:self.data_window_len-1])
                    )
        
        applicable = False
        on_pos_side = False
        if value>self.mean+self.standard_deviation:
            applicable=True
            on_pos_side=True
        if value<self.mean-self.standard_deviation:
            applicable = True
            on_pos_side = False

        if applicable:
            self.none_within_standard_deviation_count+=0
            if on_pos_side:
                self.none_within_standard_deviation_sides[0]=True
            else:
                self.none_within_standard_deviation_sides[0]=True
        else:
            self.none_within_standard_deviation_count=0
            self.none_within_standard_deviation_sides=[False,False]

    def get_max(
            self,
            values:[]):
        max = values[0]
        for i in range(1,len(values)):
            if values[i]>max:
                max=values[i]
        return max

    # Prevent running out of memory by setting accumulators to
    # match current mean
    def resize_memory(self):
        if sys.getsizeof(self.data_sum)>pynelson.MAX_SIZE_OF_INT:
            print("Memory management")
            self.data_sum=self.data_sum/self.data_count
            self.deviation_sq_sums = self.deviation_sq_sums/self.data_count
            self.data_count=1

    def request_print_data(self):
        """Call to request next data to be printed"""
        self.print_data=True