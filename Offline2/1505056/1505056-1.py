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
import numpy as np
import math

from lcgrand import MODLUS
from lcgrand import MULT1
from lcgrand import MULT2
from lcgrand import zrng
from lcgrand import lcgrand

IDLE = 0
BUSY = 1


# Parameters
class Params:
    def __init__(self, t, workStationNo, machinePerStation, jobTypes, jobProbs, stationPerJob, routing, serviceTime):
        self.meanArrivalTime = t #mean value
        self.workStationNo = workStationNo
        self.jobTypes = jobTypes
        self.machinePerStation = machinePerStation
        self.jobProbs = jobProbs
        self.jobProbsCumulative = [self.jobProbs[i] for i in range(self.jobTypes)]
        for i in range(1, self.jobTypes):
            self.jobProbsCumulative[i] += self.jobProbsCumulative[i-1]
        # print(self.jobProbsCumulative)
        self.stationPerJob = stationPerJob
        self.routing = routing
        self.meanServiceTime = serviceTime #mean value
    # Note meanArrivalTime and meanServiceTime are mean values, they are NOT rates i.e. (1/mean)


# States and statistical counters
class States:
    def __init__(self, jobTypes, workStationNo):
        # States
        self.queue = [] #this queue stores the arrival times
        self.status = [] #this holds the status of k servers
        self.numInQ = [0.0 for i in range(workStationNo)]
        self.timeLastEvent = 0.0
        
        #intermediate running statistics
        self.totalDelayQueue = []
        self.totalDelayJob = []
        self.totalServedQ = []
        self.jobsCount = [0.0 for i in range(jobTypes)] #keeps track of number of instances for each job type
        self.totalServedJob = []
        self.areaNumInQ = [0.0 for i in range(workStationNo)]
        self.areaJobNumber = 0.0

        # Statistics
        self.avgJobNumber = 0.0
        self.avgQdelay = []
        self.avgJobDelay = []
        self.overallDelay = 0.0
        self.avgQlength = []


    def update(self, sim, event):
        #if the event is the START event
        if event.eventType == 'START':
            return

        timeSincelastEvent = event.eventTime - self.timeLastEvent
        self.timeLastEvent = event.eventTime
        # # print(f'time since last event= {timeSincelastEvent}')

        #update area under numberInQ curve
        self.areaNumInQ = [self.areaNumInQ[i]+(self.numInQ[i] * timeSincelastEvent) for i in range(sim.params.workStationNo)]

        #update area under server-busy indicator function
        runningJobs = 0
        for i in range(sim.params.workStationNo):
            runningJobs += self.status[i]
        for i in range(sim.params.workStationNo):
            runningJobs += len(self.queue[i])
        self.areaJobNumber += (runningJobs * timeSincelastEvent)
        return
        

    def finish(self, sim):
        # print(f'total Delay: {self.totalDelay}')
        self.avgJobDelay = [self.totalDelayJob[i]/self.jobsCount[i] for i in range(len(self.totalDelayJob))]
        self.avgQdelay = [self.totalDelayQueue[i]/self.totalServedQ[i] for i in range(len(self.totalDelayQueue))]
        for i in range(sim.params.jobTypes):
            self.overallDelay += sim.params.jobProbs[i]*self.avgJobDelay[i]
        self.avgQlength = [self.areaNumInQ[i]/sim.simclock for i in range(sim.params.workStationNo)]
        self.avgJobNumber = self.areaJobNumber/sim.simclock
        return

    def printResults(self, sim):
        
        # print("\n\nResults from experiment.")
        # # DO NOT CHANGE THESE LINES
        # print('MMk Results: lambda = %lf, mu = %lf, k = %d' % (sim.params.lambd, sim.params.mu, sim.params.k))
        # print('MMk Total customer served: %d' % (self.served))
        # print('MMk Average queue length: %lf' % (self.avgQlength))
        # print('MMk Average customer delay in queue: %lf' % (self.avgQdelay))
        # print('MMk Time-average server utility: %lf' % (self.util))
        return

    def getResults(self, sim):
        return (self.avgJobDelay, self.overallDelay, self.avgQdelay, self.avgQlength, self.avgJobNumber)

    def initStatus(self, workStationNo:int, machinePerStation:int):
        self.status = [0 for i in range(workStationNo)]


    def checkStatus(self, workStationIdx:int, machinePerStation:int):
        if self.status[workStationIdx]<machinePerStation:
                return True
        return False

    def initQueue(self, workStationNo:int):
        self.queue = [[] for i in range(workStationNo)]

    def initDelayQ(self, workStationNo:int):
        self.totalDelayQueue = [0.0 for i in range(workStationNo)]
        self.totalServedQ = [0.0 for i in range(workStationNo)]
    
    def initDelayJob(self, jobTypes:int):
        self.totalDelayJob = [0.0 for i in range(jobTypes)]
        self.totalServedJob = [0.0 for i in range(jobTypes)]

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
        firstArrivalTime = self.eventTime + sim.expon(sim.params.meanArrivalTime)
        sim.scheduleEvent(ArrivalEvent(firstArrivalTime, sim))
        sim.scheduleEvent(ExitEvent(8, sim))
        
        


class ExitEvent(Event):
    def __init__(self, eventTime, sim):
        self.eventTime = eventTime
        self.eventType = 'EXIT'
        self.sim = sim

    def process(self, sim):
        None


class ArrivalEvent(Event):
    # Write __init__ function
    def __init__(self, eventTime ,sim):
        self.eventTime = eventTime
        self.sim = sim
        self.eventType = 'ARRIVAL'
        self.jobType = None #this is calculated as 0 indexed
        self.taskNo = None #this is calculated as 1 indexed

    def process(self, sim):
        #check if this a new arrival to the system or an already existing job visiting another station
        if self.jobType == None:
            #this is a new arrival to the system, give this a job type
            self.jobType = np.random.choice([i for i in range(sim.params.jobTypes)], p = np.array(sim.params.jobProbs))
            # tempProb = np.random.uniform()
            # for i in range(sim.params.jobTypes):
            #     if tempProb<=sim.params.jobProbsCumulative[i]:
            #         self.jobType = i
            #         break
            sim.states.jobsCount[self.jobType] += 1
            # print('job type for the new arrival: ',self.jobType)
            #set the taskNo to 1
            self.taskNo = 1 #taskNo is 1-indexed
            #schedule the next arrival
            temp = sim.expon(sim.params.meanArrivalTime)
            nextArrival = sim.simclock + temp
            # print('nextArrival: ',nextArrival,'\n')
            sim.scheduleEvent(ArrivalEvent(nextArrival, sim))

        #find the workstation
        # print('job type for the arrival: ',self.jobType)
        workStationIdx = sim.params.routing[self.jobType][self.taskNo-1]
        # print('workStationIdx: ',workStationIdx)
        # print('stationPerJob: ',sim.params.stationPerJob)
        #check to see if any server is in the workstation is idle
        freeServer = sim.states.checkStatus(workStationIdx, sim.params.machinePerStation[workStationIdx])
        if freeServer == False:
            #if all the servers are busy, then put the event in the queue
            sim.states.numInQ[workStationIdx] += 1
            sim.states.queue[workStationIdx].append(self) #this is the arrival event
        else:
            delay = 0.0
            sim.states.totalDelayJob[self.jobType] += delay
            sim.states.totalDelayQueue[workStationIdx] += delay

            #increment the number of customers served and make server busy
            sim.states.totalServedQ[workStationIdx] += 1
            sim.states.status[workStationIdx] += 1 #make another machine in that station busy

            #create the departure event for this arrival
            temp = sim.erlang(sim.params.meanServiceTime[self.jobType][self.taskNo-1])
            departureTime = sim.simclock + temp
            sim.scheduleEvent(DepartureEvent(departureTime, sim, jobType=self.jobType, taskNo=self.taskNo)) #departure is made for the same taskNo, so it remains unchanged


class DepartureEvent(Event):
    
    def __init__(self, eventTime, sim, jobType:int, taskNo:int):
        self.eventTime = eventTime
        self.eventType = 'DEPART'
        self.sim = sim
        self.jobType = jobType #0 indexed
        self.taskNo = taskNo #1 indexed


    def process(self, sim):
        #figure out the station number of this departing job
        workStationIdx = sim.params.routing[self.jobType][self.taskNo-1]
        # print('jobtype: ',self.jobType, "taskNo: ",self.taskNo)
        
        # if there is no one in the particular queue from which the departure event is being issued, make the server idle
        if len(sim.states.queue[workStationIdx])==0:
                sim.states.status[workStationIdx] -= 1


        else:
            #queue of this particular server is nonempty, so let the first person in queue receive service
            sim.states.numInQ[workStationIdx] -= 1

            #then we get the arrival time of the first person
            #in the queue(sim.states.queue) and calculate the delay faced
            nextEvent = sim.states.queue[workStationIdx][0]
            delay = sim.simclock - nextEvent.eventTime
            sim.states.totalDelayQueue[workStationIdx] += delay
            sim.states.totalDelayJob[self.jobType] += delay

            #increment the number of customers served at this workstation and schedule departure
            sim.states.totalServedQ[workStationIdx] += 1
            temp = sim.erlang(sim.params.meanServiceTime[nextEvent.jobType][nextEvent.taskNo-1])
            departureTime = sim.simclock + temp
            sim.scheduleEvent(DepartureEvent(departureTime, sim, jobType=nextEvent.jobType, taskNo=nextEvent.taskNo))
            sim.states.queue[workStationIdx] = sim.states.queue[workStationIdx][1:]

        #figure out if it was the last task for this job
        #if this was not the last task
        if self.taskNo < sim.params.stationPerJob[self.jobType]:
            #create a new arrival event
            newArrivalEvent = ArrivalEvent(eventTime=sim.simclock, sim=sim)
            #assign the jobtype as the same type as this departing event
            newArrivalEvent.jobType = self.jobType
            #taskNo will be the next task
            newArrivalEvent.taskNo = self.taskNo + 1
            #call process of this newArrivalEvent
            newArrivalEvent.process(sim)
        else:
            #if this was the last task,
            #increase the number of jobs completed
            sim.states.totalServedJob[self.jobType] += 1



class Simulator:
    def __init__(self, seed):
        self.eventQ = [] #this stores the arrival and departure events
        self.simclock = 0
        self.seed = seed
        self.params = None
        self.states = None

    def initialize(self):
        self.simclock = 0
        self.states.initStatus(machinePerStation=self.params.machinePerStation, workStationNo=self.params.workStationNo)
        self.states.initQueue(workStationNo=self.params.workStationNo)
        self.states.initDelayJob(jobTypes=self.params.jobTypes)
        self.states.initDelayQ(workStationNo=self.params.workStationNo)
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
        # np.random.seed(self.seed)
        self.initialize()

        while len(self.eventQ) > 0:
            time, event = heapq.heappop(self.eventQ)
            if event.eventType == 'EXIT':
                break

            #states are the performance matrices i.e. avg_q_len, avg_delay etc
            if self.states != None:
                self.states.update(self, event)

            # print(event.eventTime, 'Event', event)
            self.simclock = event.eventTime
            event.process(self)
            # print('status: ',self.states.status)
            # print('queue: ',self.states.queue)
        # print('jobs count: ',self.states.jobsCount)
        # print('jobs completed: ', self.states.totalServedJob)
        self.states.finish(self)

    def printResults(self):
        self.states.printResults(self)

    def getResults(self):
        return self.states.getResults(self)

    def expon(self, mean):
        return (-mean * math.log(lcgrand(1)))

    def erlang(self, mean):
        return self.expon(mean/2) + self.expon(mean/2)
        # return random.expovariate(1/mean)


def experiment1():
    #read in the input params from text file
    inputLines = []
    with open('config.txt', 'r') as f:
        inputLines = f.readlines()
    
    stationNumber = int(inputLines[0].strip('\n'))
    machinesNumber = [int(n.strip('\n')) for n in inputLines[1].split()]
    interArrivalMean = float(inputLines[2].strip('\n'))
    jobNo = int(inputLines[3].strip('\n'))
    jobProbs = [float(p.strip('\n')) for p in inputLines[4].split()]
    stationPerJob = [int(n.strip('\n')) for n in inputLines[5].split()]

    routing = [[] for i in range(jobNo)]
    serviceTime = [[] for i in range(jobNo)]
    for idx in range(jobNo):
        routing[idx] = [int(n.strip('\n')) - 1 for n in inputLines[6+idx*2].split()] #counters are stored as 0-indexed
        serviceTime[idx] = [float(n.strip('\n')) for n in inputLines[7+idx*2].split()]
    
    avgJobDelay = [0.0 for i in range(jobNo)]
    avgQdelay = [0.0 for i in range(stationNumber)]
    avgQlen = [0.0 for i in range(stationNumber)]
    avgOverallDelay = 0.0
    avgJobNumber = 0.0
    
    np.random.seed(101)
    for i in range(30):
        print('iteration: ',i+1)
        zrng[1] = 1973272912
        seed = 101
        sim = Simulator(seed)
        sim.configure(Params(t=interArrivalMean, 
                        workStationNo=stationNumber, 
                        machinePerStation=machinesNumber, 
                        jobTypes=jobNo, 
                        jobProbs=jobProbs,
                        stationPerJob=stationPerJob,
                        routing=routing,
                        serviceTime=serviceTime), 
                        States(jobNo,stationNumber))
        sim.run()
        jobDelay, overallDelay, Qdelay, Qlen, jobNumber = sim.getResults()
        avgJobDelay = [avgJobDelay[i]+jobDelay[i] for i in range(jobNo)]
        avgOverallDelay += overallDelay
        avgQdelay = [avgQdelay[i]+Qdelay[i] for i in range(stationNumber)]
        avgQlen = [avgQlen[i]+Qlen[i] for i in range(stationNumber)]
        avgJobNumber += jobNumber
    
    print('Avg Job Delay')
    for i in range(jobNo):
        print('job ',i+1, ': ',avgJobDelay[i]/30.0)
    
    print('Over all delay: ',avgOverallDelay/30.0)

    print('Avg Q Delay')
    for i in range(stationNumber):
        print('Queue ',i+1, ': ',avgQdelay[i]/30.0)
    
    print('Avg Q Len')
    for i in range(stationNumber):
        print('Queue ',i+1, ': ',avgQlen[i]/30.0)

    print('Avg Job Number: ',avgJobNumber/30.0)
    # print(sim.params.jobProbs)
    # sim.printResults()    


def main():
    print("Task 1")
    experiment1()


if __name__ == "__main__":
    main()
