"""
The task is to simulate an M/M/k system with a single queue.
Complete the skeleton code and produce results for three experiments.
The study is mainly to show various results of a queue against its ro parameter.
ro is defined as the ratio of arrival rate vs service rate.
For the sake of comparison, while plotting results from simulation, also produce the analytical results.
"""

import heapq
import random
import matplotlib.pyplot as plt
from lcgrand import MODLUS
from lcgrand import MULT1
from lcgrand import MULT2
from lcgrand import zrng
from lcgrand import lcgrand
import math
IDLE = 0
BUSY = 1


# Parameters
class Params:
    def __init__(self, lambd, mu, k):
        self.lambd = lambd  # interarrival rate
        self.mu = mu  # service rate
        self.k = k
    # Note lambd and mu are not mean value, they are rates i.e. (1/mean)

# Write more functions if required


# States and statistical counters
class States:
    def __init__(self):
        # States
        self.queue = [] #this queue stores the arrival times
        self.status = IDLE
        self.numInQ = 0.0
        self.timeLastEvent = 0.0
        
        #intermediate running statistics
        self.totalDelay = 0.0
        self.areaNumInQ = 0.0
        self.areaServerStatus = 0.0

        # Statistics
        self.util = 0.0
        self.avgQdelay = 0.0
        self.avgQlength = 0.0
        self.served = 0 #customers delayed

    def update(self, sim, event):
        #if the event is the START event
        if event.eventType == 'START':
            return

        timeSincelastEvent = sim.simclock - self.timeLastEvent
        self.timeLastEvent = sim.simclock

        #update area under numberInQ curve
        self.areaNumInQ += (self.numInQ * timeSincelastEvent)

        #update area under server-busy indicator function
        self.areaServerStatus += (self.status * timeSincelastEvent)
        

    def finish(self, sim):
        self.avgQdelay = self.totalDelay/self.served
        self.avgQlength = self.areaNumInQ/sim.simclock
        self.util = self.areaServerStatus/sim.simclock

    def printResults(self, sim):
        self.finish(sim)

        print("Results from experiment.")
        # DO NOT CHANGE THESE LINES
        print('MMk Results: lambda = %lf, mu = %lf, k = %d' % (sim.params.lambd, sim.params.mu, sim.params.k))
        print('MMk Total customer served: %d' % (self.served))
        print('MMk Average queue length: %lf' % (self.avgQlength))
        print('MMk Average customer delay in queue: %lf' % (self.avgQdelay))
        print('MMk Time-average server utility: %lf' % (self.util))

        print("Analytic Results")
        #Analytical Results
        l = sim.params.lambd
        m = sim.params.mu
        print(f'Average Queue Length: {(l*l)/(m*(m-l))}')
        print(f'Average Delay in Queue: {l/(m*(m-l))}')
        print(f'Average Queue Length: {l/m}')

    def getResults(self, sim):
        return (self.avgQlength, self.avgQdelay, self.util)

# Write more functions if required


class Event:
    def __init__(self, sim):
        self.eventType = None
        self.sim = sim
        self.eventTime = None

    def process(self, sim):
        raise Exception('Unimplemented process method for the event!')

    def __repr__(self):
        return self.eventType


class StartEvent(Event):
    def __init__(self, eventTime, sim):
        self.eventTime = eventTime
        self.eventType = 'START'
        self.sim = sim

    def process(self, sim):
        # this is the startEvent. It will enqueue an arrival event
        firstArrivalTime = self.eventTime + sim.expon(1/sim.params.lambd)
        sim.scheduleEvent(ArrivalEvent(firstArrivalTime, sim))
        sim.scheduleEvent(ExitEvent(10000, sim))
        
        


class ExitEvent(Event):
    def __init__(self, eventTime, sim):
        self.eventTime = eventTime
        self.eventType = 'EXIT'
        self.sim = sim

    def process(self, sim):
        # Complete this function
        None


class ArrivalEvent(Event):
    # Write __init__ function
    def __init__(self, eventTime ,sim):
        self.eventTime = eventTime
        self.sim = sim
        self.eventType = 'ARRIVAL'

    def process(self, sim):
        #schedule the next arrival
        nextArrival = sim.simclock + sim.expon(1/sim.params.lambd)
        sim.scheduleEvent(ArrivalEvent(nextArrival, sim))

        #check to see if the server is busy
        if sim.states.status==BUSY:
            sim.states.numInQ += 1
            sim.states.queue.append(sim.simclock)
        else:
            delay = 0.0
            sim.states.totalDelay += delay

            #increment the number of customers served and make server busy
            sim.states.served += 1
            sim.states.status = BUSY

            #create the departure event for this arrival
            departureTime = sim.simclock + sim.expon(1/sim.params.mu)
            sim.scheduleEvent(DepartureEvent(departureTime, sim))


class DepartureEvent(Event):
    
    def __init__(self, eventTime, sim):
        self.eventTime = eventTime
        self.eventType = 'DEPART'
        self.sim = sim


    def process(self, sim):
        #if there is no one in the queue, make the server idle
        if sim.states.numInQ==0:
            sim.states.status = IDLE
        else:
            #queue is nonempty, so let the first person in queue receive service
            sim.states.numInQ -= 1

            #the we get the arrival time of the first person
            #in the queue(sim.states.queue) and calculate the delay faced
            delay = sim.simclock - sim.states.queue[0]
            sim.states.totalDelay += delay

            #increment the number of customers served and schedule departure
            sim.states.served += 1
            departureTime = sim.simclock + sim.expon(1/sim.params.mu)
            sim.scheduleEvent(DepartureEvent(departureTime, sim))

            #move everyone in the queue one step up
            sim.states.queue = sim.states.queue[1:]





class Simulator:
    def __init__(self, seed):
        self.eventQ = [] #this stores the arrival and departure events
        self.simclock = 0
        self.seed = seed
        self.params = None
        self.states = None

    def initialize(self):
        self.simclock = 0
        self.scheduleEvent(StartEvent(0, self))

    def configure(self, params, states):
        self.params = params
        self.states = states

    def now(self):
        return self.simclock

    def scheduleEvent(self, event):
        #heapq is a priority queue
        heapq.heappush(self.eventQ, (event.eventTime, event))

    def run(self):
        random.seed(self.seed)
        self.initialize()

        while len(self.eventQ) > 0:
            time, event = heapq.heappop(self.eventQ)
            #print(event.eventTime, 'Event', event)

            if event.eventType == 'EXIT':
                break

            #states are the performance matrices i.e. avg_q_len, avg_delay etc
            if self.states != None:
                self.states.update(self, event)

            # print(event.eventTime, 'Event', event)
            self.simclock = event.eventTime
            event.process(self)

        self.states.finish(self)

    def printResults(self):
        self.states.printResults(self)

    def getResults(self):
        return self.states.getResults(self)

    def expon(self, mean):
        return (-mean * math.log(lcgrand(1)))


def experiment1():
    seed = 101
    sim = Simulator(seed)
    sim.configure(Params(5.0 / 60, 8.0 / 60, 1), States())
    sim.run()
    sim.printResults()


def experiment2():
    seed = 110
    mu = 1000.0 / 60
    ratios = [u / 10.0 for u in range(1, 11)]

    avglength = []
    avgdelay = []
    util = []

    i=1
    for ro in ratios:
        print(f"iteration {i}")
        sim = Simulator(seed)
        sim.configure(Params(mu * ro, mu, 1), States())
        sim.run()

        length, delay, utl = sim.getResults()
        avglength.append(length)
        avgdelay.append(delay)
        util.append(utl)
        i+=1

    plt.figure(1)
    plt.subplot(311)
    plt.plot(ratios, avglength)
    plt.xlabel('Ratio (ro)')
    plt.ylabel('Avg Q length')

    plt.subplot(312)
    plt.plot(ratios, avgdelay)
    plt.xlabel('Ratio (ro)')
    plt.ylabel('Avg Q delay (sec)')

    plt.subplot(313)
    plt.plot(ratios, util)
    plt.xlabel('Ratio (ro)')
    plt.ylabel('Util')

    plt.show()


def experiment3():
    # Similar to experiment2 but for different values of k; 1, 2, 3, 4
    # Generate the same plots
    # Fix lambd = (5.0/60), mu = (8.0/60) and change value of k
    None


def main():
    print("Experiment 1")
    experiment1()
    print("\n\nExperiment 2")
    experiment2()
    # experiment3()


if __name__ == "__main__":
    main()
