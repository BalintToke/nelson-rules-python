# Nelson Rules - Python (v3.11.1) implementation 

Apply Nelson Rules for a continuous manufacturing process using Python.  

Mean and standard deviation are aggregated as data is arriving into the process, sending an event if a Nelson Rule is triggered/cleared.  

A thread is used for any singular machine to check Nelson Rules and threads communicate via Queues including data, event and exception forwarding.

### pynelson

Contains the NelsonRuleHandler class that is used to check Nelson Rules against the dataset arriving from a manufacturing machine.  
Contains the Types class which provides schemas to effectively communicate between threads.

### sample

A sample to showcase the implementation of the pynelson module.  
Contains a simple simulation providing randomized data.  
Contains an output implementation to show how to handle NelsonRuleEvent objects  
Contains a simple console user interface.

### sample_main.py

Run the sample described above.