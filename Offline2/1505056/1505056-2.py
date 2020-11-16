"""
The task is to simulate an M/M/k system with a single queue.
Complete the skeleton code and produce results for three experiments.
The study is mainly to show various results of a queue against its ro parameter.
ro is defined as the ratio of arrival rate vs service rate.
For the sake of comparison, while plotting results from simulation, also produce the analytical results.
"""

import heapq
import random
import numpy as np
import math

import matplotlib.pyplot as plt
from lcgrand import MODLUS
from lcgrand import MULT1
from lcgrand import MULT2
from lcgrand import zrng
from lcgrand import lcgrand

IDLE = 0
BUSY = 1
HOTFOOD = 1
SANDWICH = 2
DRINKS = 3
CASHIER = 4

# Parameters
class Params:
    def __init__(self, meanArrivalTime, groupSizeProbs, routes, routeProbs, staff, ST, ACT):
        self.meanArrivalTime = meanArrivalTime
        self.groupSizeProbs = groupSizeProbs
        self.routes = routes
        self.routeProbs = routeProbs
        self.staff = staff
        self.ST = ST
        self.ACT = ACT

    # Note meanArrival time is a mean value

# States and statistical counters
class States:
    def __init__(self):
        # States
        self.groupId = 1 #next expected groupId
        self.foodQueue = [] #this queue stores the arrival times for arrivals at hot-food and sandwich bar
        self.cashierQueue = [] #stores arrival time at queues in cashier counters
        self.foodStatus = [] #this holds the status of food servers
        self.cashierStatus = [] #this holds the status of the cashiers
        self.numInQ = [0.0 for i in range(3)] #for storing number of people in hotfood, sandwich and all cashier queues respectively
        self.timeLastEvent = 0.0
        
        # #intermediate running statistics
        self.totalQDelay = [0.0 for i in range(3)] #index-0: hotfood, index-1: sandwich, index-2: cashiers
        self.totalQServed = [0.0 for i in range(3)] #index-0: hotfood, index-1: sandwich, index-2: cashiers
        self.totalTypeDelay = [0.0 for i in range(3)] #there are 3 types of routes
        self.totalTypeServed = [0.0 for i in range(3)]
        self.areaNumInQ = [0.0 for i in range(3)]
        self.areaCustomerNumber = 0.0

        #Statistics
        self.avgCustomerNumber = 0.0
        self.maxCustomerNumber = 0.0
        self.avgQdelay = []
        self.maxQDelay = [0.0 for i in range(3)] #index-0: hotfood, index-1: sandwich, index-2: cashiers
        self.avgTypeDelay = []
        self.maxTypeDelay = [0.0 for i in range(3)]
        self.avgOverallDelay = 0.0 #for all types of customers
        self.avgQlength = []
        self.maxNumInQ = [0.0 for i in range(3)]
        self.totalServed = 0



    def update(self, sim, event):
        #if the event is the START event
        if event.eventType == 'START':
            return

        timeSincelastEvent = event.eventTime - self.timeLastEvent
        self.timeLastEvent = event.eventTime

        #update area under numberInQ curve
        self.areaNumInQ = [self.areaNumInQ[i]+(self.numInQ[i] * timeSincelastEvent) for i in range(3)]

        #update area under server-busy indicator function
        totalCustomers = 0
        for i in range(2):
            totalCustomers += self.foodStatus[i]
        for i in range(sim.params.staff[2]):
            totalCustomers += self.cashierStatus[i]
        for i in range(2):
            totalCustomers += len(self.foodQueue[i])
        for i in range(sim.params.staff[2]):
            totalCustomers += len(self.cashierQueue[i])
        self.areaCustomerNumber += (totalCustomers * timeSincelastEvent)   
        self.maxCustomerNumber = max(self.maxCustomerNumber, totalCustomers)    

    def finish(self, sim):
        # print(f'total Delay: {self.totalDelay}')
        self.avgQdelay = [self.totalQDelay[i]/self.totalQServed[i] for i in range(3)]
        self.avgTypeDelay = [self.totalTypeDelay[i]/self.totalTypeServed[i] for i in range(3)]
        for i in range(3):
            self.avgOverallDelay += self.avgTypeDelay[i]*sim.params.routeProbs[i]
        self.avgQlength = [self.areaNumInQ[i]/sim.simclock for i in range(3)]
        self.avgQlength[2] = self.avgQdelay[2]/sim.params.staff[2] # dividing the number of q length of the cashiers by the number of cashiers 
        self.avgCustomerNumber = self.areaCustomerNumber/sim.simclock

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
        return (self.avgQdelay, self.maxQDelay, self.avgTypeDelay, self.maxTypeDelay, self.avgOverallDelay, self.avgQlength, self.maxNumInQ, self.avgCustomerNumber, self.maxCustomerNumber, self.totalServed)

    def initStatus(self, staff:list):
        self.foodStatus = [IDLE for i in range(2)]
        self.cashierStatus = [IDLE for i in range(staff[CASHIER-2])]

    def checkFoodStatus(self, counterNo): #counterNo is 1-indexed
        return self.foodStatus[counterNo-1]

    def findShortestCashierQueue(self, staff): #returns 0-indexed value
        #first look for the cashier who is idle
        for i in range(staff[2]):
            if self.cashierStatus[i] == IDLE:
                return i
        #if none of the cashiers is free, find the shortest Queue
        shortestQueue = 0
        for i in range(1,staff[2]):
            if len(self.cashierQueue[i])<len(self.cashierQueue[shortestQueue]):
                shortestQueue = i
        return shortestQueue

    def initQueue(self, staff:list):
        self.foodQueue = [[] for i in range(2)]
        self.cashierQueue = [[] for i in range(staff[CASHIER-2])]




class Event:
    def __init__(self, sim):
        self.eventType = None
        self.sim = sim
        self.eventTime = None

    def process(self, sim):
        raise Exception('Unimplemented process method for the event!')

    def __repr__(self):
        return self.eventType

    def __lt__(self,other):
        return self.eventTime < other.eventTime

class StartEvent(Event):
    def __init__(self, eventTime, sim):
        self.eventTime = eventTime
        self.eventType = 'START'
        self.sim = sim

    def process(self, sim):
        # this is the startEvent. It will enqueue an arrival event
        firstArrivalTime = self.eventTime + sim.expon(sim.params.meanArrivalTime)
        #figure out the size of the first arriving group
        groupSize = np.random.choice([i+1 for i in range(4)], p=sim.params.groupSizeProbs)
        for i in range(groupSize):
            sim.scheduleEvent(ArrivalEvent(firstArrivalTime, sim, groupId=1, taskNo=1 , act=0.0, routingId=None))
        sim.scheduleEvent(ExitEvent(90*60, sim))
        
        


class ExitEvent(Event):
    def __init__(self, eventTime, sim):
        self.eventTime = eventTime
        self.eventType = 'EXIT'
        self.sim = sim

    def process(self, sim):
        None


class ArrivalEvent(Event):
    # Write __init__ function
    def __init__(self, eventTime ,sim, groupId, taskNo, act, routingId):
        self.eventTime = eventTime
        self.sim = sim
        self.eventType = 'ARRIVAL'
        self.groupId = groupId
        self.taskNo = taskNo #1 indexed
        self.routingId = routingId #1 indexed
        self.act = act

    def process(self, sim):
        #check if we are processing a new group
        #if it's a new group, schedule the next arrival
        if sim.states.groupId == self.groupId: #found the next expected groupId, increment the next expected groupId
            sim.states.groupId = self.groupId + 1
            temp = sim.expon(sim.params.meanArrivalTime)
            nextArrival = sim.simclock + temp
            groupSize = np.random.choice([i+1 for i in range(4)], p=sim.params.groupSizeProbs)
            for i in range(groupSize):
                sim.scheduleEvent(ArrivalEvent(nextArrival, sim, groupId=sim.states.groupId, taskNo=1 ,act=0.0, routingId=None))
            # sim.scheduleEvent(ArrivalEvent(nextArrival, sim, groupId=sim.states.groupId, taskNo=1 ,act=0.0, routingId=None) )

        #if the customer is visiting the first ever counter
        if self.taskNo == 1:
            #assign a routing Id
            self.routingId = np.random.choice( [i+1 for i in range(len(sim.params.routes))], p=sim.params.routeProbs )
            #update totalTypeServed
            sim.states.totalTypeServed[self.routingId-1] += 1
        
        #based on routingId and taskNo, figure out the station this customer should be at
        # print('routingId: ',self.routingId, 'taskId: ',self.taskNo)
        counterNo = sim.params.routes[self.routingId-1][self.taskNo-1] #1-indexed value
        # print('counterNo: ',counterNo)

        #check if the customer is either at HOTFOOD or SANDWICH
        if counterNo < DRINKS: 
            #check to see if any counter is free
            status = sim.states.checkFoodStatus(counterNo)
            if status == BUSY:
                sim.states.numInQ[counterNo-1] += 1
                sim.states.maxNumInQ[counterNo-1] = max(sim.states.maxNumInQ[counterNo-1], sim.states.numInQ[counterNo-1])
                #the counter is busy, append it to the queue
                sim.states.foodQueue[counterNo-1].append(self) #this is the arrival event
                # print(sim.states.queue)
            else:
                delay = 0.0
                #update totalQdelay
                sim.states.totalQDelay[counterNo-1] += delay
                #update maxQDelay
                sim.states.maxQDelay[counterNo-1] = max(sim.states.maxQDelay[counterNo-1], delay)
                #update totalTypeDelay
                sim.states.totalTypeDelay[self.routingId-1] += delay
                #update maxTypeDelay
                sim.states.maxTypeDelay[self.routingId-1] = max(sim.states.maxTypeDelay[self.routingId-1], delay)

                #increment the number of customers served and make server busy
                sim.states.totalQServed[counterNo-1] += 1
                sim.states.foodStatus[counterNo-1] = BUSY

                #calculate nextAct for this service
                nextAct = self.act + np.random.uniform(sim.params.ACT[counterNo-1][0],sim.params.ACT[counterNo-1][1])
                #create the departure event for this arrival
                temp = np.random.uniform(sim.params.ST[counterNo-1][0], sim.params.ST[counterNo-1][1])
                departureTime = sim.simclock + temp
                sim.scheduleEvent(DepartureEvent(departureTime, sim, groupId=self.groupId, taskNo=self.taskNo, routingId=self.routingId, act=nextAct, cashierNo=None))
        #the customer is at DRINKs
        elif counterNo < CASHIER:
            #accumulate act
            nextAct = self.act + np.random.uniform(sim.params.ACT[counterNo-1][0],sim.params.ACT[counterNo-1][1])
            #schedule departure time using ST
            temp = np.random.uniform(sim.params.ST[counterNo-1][0],sim.params.ST[counterNo-1][1])
            departureTime = sim.simclock + temp
            sim.scheduleEvent(DepartureEvent(departureTime, sim, groupId=self.groupId, taskNo=self.taskNo, routingId=self.routingId, act=nextAct, cashierNo=None))

        else:
            #if the customer is at the cashier
            #find the shortest queue or the available cashier
            cashierNo = sim.states.findShortestCashierQueue(sim.params.staff)
            #check if the cashier is IDLE, if so, make the cashier busy
            if sim.states.cashierStatus[cashierNo] == IDLE:
                #update totalQDelay
                delay = 0.0
                sim.states.totalQDelay[counterNo-2] += delay
                #update maxQdelay
                sim.states.maxQDelay[counterNo-2] = max(sim.states.maxQDelay[counterNo-2], delay)
                #update totalTypeDelay
                sim.states.totalTypeDelay[self.routingId-1] += delay
                #update maxTypeDelay
                sim.states.maxTypeDelay[self.routingId-1] = max(sim.states.maxTypeDelay[self.routingId-1], delay)

                #increment the number of customers served and make server busy
                sim.states.totalQServed[counterNo-2] += 1
                sim.states.cashierStatus[cashierNo] = BUSY

                #no need to calculate nextACT because there will be no arrival event after this departure
                #schedule the departure event based on ACT
                departureTime = sim.simclock + self.act
                #when scheduling for departure from cashier, we have no need for act
                sim.scheduleEvent(DepartureEvent(departureTime, sim, groupId=self.groupId, taskNo=self.taskNo, routingId=self.routingId, act=0.0, cashierNo=cashierNo))
            #if the cashier is busy, join the queue
            else:
                sim.states.numInQ[counterNo-2] += 1
                sim.states.maxNumInQ[counterNo-2] = max(sim.states.maxNumInQ[counterNo-2], sim.states.numInQ[counterNo-2])
                sim.states.cashierQueue[cashierNo].append(self)


class DepartureEvent(Event):
    
    def __init__(self, eventTime, sim, groupId:int, routingId:int, taskNo:int, act, cashierNo):
        self.eventTime = eventTime
        self.eventType = 'DEPART'
        self.sim = sim
        self.groupId = groupId
        self.taskNo = taskNo #1-indexed
        self.routingId = routingId #1-indexed
        self.act = act #this is the nextAct, which will handed to the next arrival event
        self.cashierNo = cashierNo #0-indexed

    def process(self, sim):
        # print('routingId: ',self.routingId)
        # print('taskNo: ', self.taskNo)
        # print('ACT: ',self.act)

        #first figure out the current counterNo
        counterNo = sim.params.routes[self.routingId-1][self.taskNo-1]
        #if the customer is leaving from either Hotfood or Sandwich
        if counterNo<DRINKS:
        #if there is no one in the particular queue from which the departure event is being issued, make the server idle
            if len(sim.states.foodQueue[counterNo-1])==0:
                sim.states.foodStatus[counterNo-1] = IDLE

            else:
                #we get the first customer from the queue
                newEvent = sim.states.foodQueue[counterNo-1][0]

                #decrease the number of people in this particular queue
                sim.states.numInQ[counterNo-1] -= 1

                #calculate the delay faced
                delay = sim.simclock - newEvent.eventTime
                #update totalQdelay
                sim.states.totalQDelay[counterNo-1] += delay
                #update maxQdelay
                sim.states.maxQDelay[counterNo-1] = max(sim.states.maxQDelay[counterNo-1], delay)
                #update totalTypeDelay
                sim.states.totalTypeDelay[newEvent.routingId-1] += delay
                #update maxTypeDelay
                sim.states.maxTypeDelay[newEvent.routingId-1] = max(sim.states.maxTypeDelay[newEvent.routingId-1], delay)


                #increment the number of customers served and calculate act for this event
                sim.states.totalQServed[counterNo-1] += 1
                nextAct = newEvent.act + np.random.uniform(sim.params.ACT[counterNo-1][0],sim.params.ACT[counterNo-1][1])
                
                #schedule departure time using ST
                temp = np.random.uniform(sim.params.ST[counterNo-1][0],sim.params.ST[counterNo-1][1])
                # print(temp)
                departureTime = sim.simclock + temp
                sim.scheduleEvent(DepartureEvent(departureTime, sim, groupId=newEvent.groupId, taskNo=newEvent.taskNo, routingId=newEvent.routingId, act=nextAct, cashierNo=None))

                #move everyone in the queue one step up
                sim.states.foodQueue[counterNo-1] = sim.states.foodQueue[counterNo-1][1:]
        #if the customer was leaving from Drinks, there is nothing to be done for the next event in the queue, because there is no queue
        # if the customer was leaving from Cashier, there are things to be done, because there is a queue
        elif  counterNo == CASHIER:
            sim.states.totalServed += 1 #increment totalServed while leaving from cashier
            #if the queue is empty, make the cashier idle
            if len(sim.states.cashierQueue[self.cashierNo]) == 0:
                sim.states.cashierStatus[self.cashierNo] = IDLE
            else:
                #get the next customer at this cashier counter
                newEvent = sim.states.cashierQueue[self.cashierNo][0]
                
                #decrease the number of people in this particular queue
                sim.states.numInQ[counterNo-2] -= 1

                #calculate the delay faced
                delay = sim.simclock - newEvent.eventTime
                #update totalQdelay
                sim.states.totalQDelay[counterNo-2] += delay
                #update maxQDelay
                sim.states.maxQDelay[counterNo-2] = max(sim.states.maxQDelay[counterNo-2], delay)
                #update totalTypeDelay
                sim.states.totalTypeDelay[newEvent.routingId-1] += delay
                #update maxTypeDelay
                sim.states.maxTypeDelay[newEvent.routingId-1] = max(sim.states.maxTypeDelay[newEvent.routingId-1], delay)
                #increment the number of customers served
                sim.states.totalQServed[counterNo-2] += 1

                #no need to calculate nextACT because there will be no arrival event after this departure
                #schedule the departure event based on ACT
                departureTime = sim.simclock + newEvent.act
                sim.scheduleEvent(DepartureEvent(departureTime, sim, groupId=newEvent.groupId, taskNo=newEvent.taskNo, routingId=newEvent.routingId, act=0.0, cashierNo=self.cashierNo))

                #move everyone in the queue one position up
                sim.states.cashierQueue[self.cashierNo] = sim.states.cashierQueue[self.cashierNo][1:]
                
        #if the customer was leaving from anywhere but the cashier's, an arrival event has to be created for going to the next counter
        if counterNo != CASHIER:
            #schedule an Arrival event with the same ACT(because ACT was calculated at the corresponding Arrival event)
            #increased taskNo, same routingId, same groupId as the sim.states.groupId
            sim.scheduleEvent(ArrivalEvent(sim.simclock, sim, sim.states.groupId, taskNo=self.taskNo+1, act=self.act, routingId=self.routingId))

class Simulator:
    def __init__(self, seed):
        self.eventQ = [] #this stores the arrival and departure events
        self.simclock = 0
        self.seed = seed
        self.params = None
        self.states = None

    def initialize(self):
        self.simclock = 0
        self.states.initStatus(self.params.staff)
        self.states.initQueue(self.params.staff)
        # print('foodQueue: ',self.states.foodQueue)
        # print('cashierQueue: ',self.states.cashierQueue)
        # print('foodStatus: ', self.states.foodStatus)
        # print('cashierStatus: ', self.states.cashierStatus)
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
        # random.seed(self.seed)
        self.initialize()

        while len(self.eventQ) > 0:
            time, event = heapq.heappop(self.eventQ)

            # print('time: ', time,'\nevent: ',event)
            if event.eventType == 'EXIT':
                # event.process(self)
                break

            #states are the performance matrices i.e. avg_q_len, avg_delay etc
            if self.states != None:
                self.states.update(self, event)

            self.simclock = event.eventTime
            event.process(self)
            # print('foodQueue: ',self.states.foodQueue)
            # print('foodStatus: ',self.states.foodStatus)
            # print('cashierQueue: ',self.states.cashierQueue)
            # print('cashierStatus: ',self.states.cashierStatus)
            # print('\n')

        self.states.finish(self)

    def printResults(self):
        self.states.printResults(self)

    def getResults(self):
        return self.states.getResults(self)

    def expon(self, mean):
        return (-mean * math.log(lcgrand(1)))
        # return np.random.exponential(mean)


def base_case():
    print('Base model')
    seed = 101
    np.random.seed(seed)
    
    zrng[1] = 1973272912
    sim = Simulator(seed)
    sim.configure(Params(meanArrivalTime=30,
                        groupSizeProbs= [0.5, 0.3, 0.1, 0.1],
                        routes= [[HOTFOOD,DRINKS,CASHIER], [SANDWICH,DRINKS,CASHIER],[DRINKS,CASHIER]],
                        routeProbs = [0.8, 0.15, 0.05],
                        staff= [1,1,2],
                        ST= [(50.0,120.0),(60,180),(5.0,20.0)],
                        ACT= [(20.0,40.0),(5.0,15.0),(5.0,10.0)]
                        ), 
                        States())
    sim.run()
    avgQdelay, maxQDelay, avgTypeDelay, maxTypeDelay, avgOverallDelay, avgQlength, maxQlength, avgCustomerNumber, maxCustomerNumber, totalServed = sim.getResults()

    print('avgQdelay')
    for i in range(3):
        print('Q',i+1,": ",avgQdelay[i]/60.0)
    print()

    print('maxQdelay')
    for i in range(3):
        print('Q',i+1,": ",maxQDelay[i]/60.0)
    print()

    print('avgTypedelay')
    for i in range(3):
        print('Type',i+1,": ",avgTypeDelay[i]/60.0)
    print()

    print('maxTypedelay')
    for i in range(3):
        print('Q',i+1,": ",maxTypeDelay[i]/60.0)
    print()

    print('overallDelay: ', avgOverallDelay/60.0)

    print('avgQlength')
    for i in range(3):
        print('Q',i+1,': ',avgQlength[i])
    print()

    print('maxQlength')
    for i in range(3):
        print('Q',i+1,': ',maxQlength[i])
    print()

    print('avgCustomerNumber: ', avgCustomerNumber)
    print('maxCustomerNumber: ', maxCustomerNumber)
    print('Total Served: ', totalServed,'\n')
    # print('groupId: ', sim.states.groupId)
    # print('served', sim.states.totalTypeServed)

def thirdCashier():
    print('[1,1,3]')
    seed = 101
    np.random.seed(seed)
    
    zrng[1] = 1973272912
    sim = Simulator(seed)
    sim.configure(Params(meanArrivalTime=30,
                        groupSizeProbs= [0.5, 0.3, 0.1, 0.1],
                        routes= [[HOTFOOD,DRINKS,CASHIER], [SANDWICH,DRINKS,CASHIER],[DRINKS,CASHIER]],
                        routeProbs = [0.8, 0.15, 0.05],
                        staff= [1,1,3], #a third cashier has been added
                        ST= [(50.0,120.0),(60,180),(5.0,20.0)],
                        ACT= [(20.0,40.0),(5.0,15.0),(5.0,10.0)]
                        ), 
                        States())
    sim.run()
    avgQdelay, maxQDelay, avgTypeDelay, maxTypeDelay, avgOverallDelay, avgQlength, maxQlength, avgCustomerNumber, maxCustomerNumber, totalServed = sim.getResults()
    
    # print('avgQdelay')
    # for i in range(3):
    #     print('Q',i+1,": ",avgQdelay[i]/60.0)
    # print()

    # print('maxQdelay')
    # for i in range(3):
    #     print('Q',i+1,": ",maxQDelay[i]/60.)
    # print()

    # print('avgTypedelay')
    # for i in range(3):
    #     print('Type',i+1,": ",avgTypeDelay[i]/60.0)
    # print()

    # print('maxTypedelay')
    # for i in range(3):
    #     print('Q',i+1,": ",maxTypeDelay[i]/60.0)
    # print()

    print('overallDelay: ', avgOverallDelay/60.0)

    # print('avgQlength')
    # for i in range(3):
    #     print('Q',i+1,': ',avgQlength[i])
    # print()

    # print('maxQlength')
    # for i in range(3):
    #     print('Q',i+1,': ',maxQlength[i])
    # print()

    print('avgCustomerNumber: ', avgCustomerNumber)
    print('maxCustomerNumber: ', maxCustomerNumber)
    print('Total Served: ', totalServed,'\n')

def exp3():
    print('[2,1,2]')
    seed = 101
    np.random.seed(seed)
    
    zrng[1] = 1973272912
    sim = Simulator(seed)
    sim.configure(Params(meanArrivalTime=30,
                        groupSizeProbs= [0.5, 0.3, 0.1, 0.1],
                        routes= [[HOTFOOD,DRINKS,CASHIER], [SANDWICH,DRINKS,CASHIER],[DRINKS,CASHIER]],
                        routeProbs = [0.8, 0.15, 0.05],
                        staff= [2,1,2], #one server added at hot food station
                        ST= [(50.0/2.0,120.0/2.0),(60,180),(5.0,20.0)],
                        ACT= [(20.0/2.0,40.0/2.0),(5.0,15.0),(5.0,10.0)]
                        ), 
                        States())
    sim.run()
    avgQdelay, maxQDelay, avgTypeDelay, maxTypeDelay, avgOverallDelay, avgQlength, maxQlength, avgCustomerNumber, maxCustomerNumber, totalServed = sim.getResults()
    
    # print('avgQdelay')
    # for i in range(3):
    #     print('Q',i+1,": ",avgQdelay[i]/60.0)
    # print()

    # print('maxQdelay')
    # for i in range(3):
    #     print('Q',i+1,": ",maxQDelay[i]/60.)
    # print()

    # print('avgTypedelay')
    # for i in range(3):
    #     print('Type',i+1,": ",avgTypeDelay[i]/60.0)
    # print()

    # print('maxTypedelay')
    # for i in range(3):
    #     print('Q',i+1,": ",maxTypeDelay[i]/60.0)
    # print()

    print('overallDelay: ', avgOverallDelay/60.0)

    # print('avgQlength')
    # for i in range(3):
    #     print('Q',i+1,': ',avgQlength[i])
    # print()

    # print('maxQlength')
    # for i in range(3):
    #     print('Q',i+1,': ',maxQlength[i])
    # print()

    print('avgCustomerNumber: ', avgCustomerNumber)
    print('maxCustomerNumber: ', maxCustomerNumber)
    print('Total Served: ', totalServed,'\n')

def exp4():
    print('[1,2,2]')
    seed = 101
    np.random.seed(seed)
    
    zrng[1] = 1973272912
    sim = Simulator(seed)
    sim.configure(Params(meanArrivalTime=30,
                        groupSizeProbs= [0.5, 0.3, 0.1, 0.1],
                        routes= [[HOTFOOD,DRINKS,CASHIER], [SANDWICH,DRINKS,CASHIER],[DRINKS,CASHIER]],
                        routeProbs = [0.8, 0.15, 0.05],
                        staff= [1,2,2], #extra server at sandwich bar
                        ST= [(50.0,120.0),(60/2.0,180/2.0),(5.0,20.0)],
                        ACT= [(20.0,40.0),(5.0/2.0,15.0/2.0),(5.0,10.0)]
                        ), 
                        States())
    sim.run()
    avgQdelay, maxQDelay, avgTypeDelay, maxTypeDelay, avgOverallDelay, avgQlength, maxQlength, avgCustomerNumber, maxCustomerNumber, totalServed = sim.getResults()
    
    # print('avgQdelay')
    # for i in range(3):
    #     print('Q',i+1,": ",avgQdelay[i]/60.0)
    # print()

    # print('maxQdelay')
    # for i in range(3):
    #     print('Q',i+1,": ",maxQDelay[i]/60.)
    # print()

    # print('avgTypedelay')
    # for i in range(3):
    #     print('Type',i+1,": ",avgTypeDelay[i]/60.0)
    # print()

    # print('maxTypedelay')
    # for i in range(3):
    #     print('Q',i+1,": ",maxTypeDelay[i]/60.0)
    # print()

    print('overallDelay: ', avgOverallDelay/60.0)

    # print('avgQlength')
    # for i in range(3):
    #     print('Q',i+1,': ',avgQlength[i])
    # print()

    # print('maxQlength')
    # for i in range(3):
    #     print('Q',i+1,': ',maxQlength[i])
    # print()

    print('avgCustomerNumber: ', avgCustomerNumber)
    print('maxCustomerNumber: ', maxCustomerNumber)
    print('Total Served: ', totalServed,'\n')

def exp5():
    print('[2,2,2]')
    seed = 101
    np.random.seed(seed)
    
    zrng[1] = 1973272912
    sim = Simulator(seed)
    sim.configure(Params(meanArrivalTime=30,
                        groupSizeProbs= [0.5, 0.3, 0.1, 0.1],
                        routes= [[HOTFOOD,DRINKS,CASHIER], [SANDWICH,DRINKS,CASHIER],[DRINKS,CASHIER]],
                        routeProbs = [0.8, 0.15, 0.05],
                        staff= [2,2,2], #two servers added respectively at hotfood and sandwich
                        ST= [(50.0/2.0,120.0/2.0),(60/2.0,180/2.0),(5.0,20.0)],
                        ACT= [(20.0/2.0,40.0/2.0),(5.0/2.0,15.0/2.0),(5.0,10.0)]
                        ), 
                        States())
    sim.run()
    avgQdelay, maxQDelay, avgTypeDelay, maxTypeDelay, avgOverallDelay, avgQlength, maxQlength, avgCustomerNumber, maxCustomerNumber, totalServed = sim.getResults()
    
    # print('avgQdelay')
    # for i in range(3):
    #     print('Q',i+1,": ",avgQdelay[i]/60.0)
    # print()

    # print('maxQdelay')
    # for i in range(3):
    #     print('Q',i+1,": ",maxQDelay[i]/60.)
    # print()

    # print('avgTypedelay')
    # for i in range(3):
    #     print('Type',i+1,": ",avgTypeDelay[i]/60.0)
    # print()

    # print('maxTypedelay')
    # for i in range(3):
    #     print('Q',i+1,": ",maxTypeDelay[i]/60.0)
    # print()

    print('overallDelay: ', avgOverallDelay/60.0)

    # print('avgQlength')
    # for i in range(3):
    #     print('Q',i+1,': ',avgQlength[i])
    # print()

    # print('maxQlength')
    # for i in range(3):
    #     print('Q',i+1,': ',maxQlength[i])
    # print()

    print('avgCustomerNumber: ', avgCustomerNumber)
    print('maxCustomerNumber: ', maxCustomerNumber)
    print('Total Served: ', totalServed,'\n')

def exp6():
    print('[2,1,3]')
    seed = 101
    np.random.seed(seed)
    
    zrng[1] = 1973272912
    sim = Simulator(seed)
    sim.configure(Params(meanArrivalTime=30,
                        groupSizeProbs= [0.5, 0.3, 0.1, 0.1],
                        routes= [[HOTFOOD,DRINKS,CASHIER], [SANDWICH,DRINKS,CASHIER],[DRINKS,CASHIER]],
                        routeProbs = [0.8, 0.15, 0.05],
                        staff= [2,1,3], #one server and one cashier added respectively at hotfood and sandwich
                        ST= [(50.0/2.0,120.0/2.0),(60,180),(5.0,20.0)],
                        ACT= [(20.0/2.0,40.0/2.0),(5.0,15.0),(5.0,10.0)]
                        ), 
                        States())
    sim.run()
    avgQdelay, maxQDelay, avgTypeDelay, maxTypeDelay, avgOverallDelay, avgQlength, maxQlength, avgCustomerNumber, maxCustomerNumber, totalServed = sim.getResults()
    
    # print('avgQdelay')
    # for i in range(3):
    #     print('Q',i+1,": ",avgQdelay[i]/60.0)
    # print()

    # print('maxQdelay')
    # for i in range(3):
    #     print('Q',i+1,": ",maxQDelay[i]/60.)
    # print()

    # print('avgTypedelay')
    # for i in range(3):
    #     print('Type',i+1,": ",avgTypeDelay[i]/60.0)
    # print()

    # print('maxTypedelay')
    # for i in range(3):
    #     print('Q',i+1,": ",maxTypeDelay[i]/60.0)
    # print()

    print('overallDelay: ', avgOverallDelay/60.0)

    # print('avgQlength')
    # for i in range(3):
    #     print('Q',i+1,': ',avgQlength[i])
    # print()

    # print('maxQlength')
    # for i in range(3):
    #     print('Q',i+1,': ',maxQlength[i])
    # print()

    print('avgCustomerNumber: ', avgCustomerNumber)
    print('maxCustomerNumber: ', maxCustomerNumber)
    print('Total Served: ', totalServed,'\n')

def exp7():
    print('[1,2,3]')
    seed = 101
    np.random.seed(seed)
    
    zrng[1] = 1973272912
    sim = Simulator(seed)
    sim.configure(Params(meanArrivalTime=30,
                        groupSizeProbs= [0.5, 0.3, 0.1, 0.1],
                        routes= [[HOTFOOD,DRINKS,CASHIER], [SANDWICH,DRINKS,CASHIER],[DRINKS,CASHIER]],
                        routeProbs = [0.8, 0.15, 0.05],
                        staff= [1,2,3], #two servers added respectively at hotfood and sandwich
                        ST= [(50.0,120.0),(60/2.0,180/2.0),(5.0,20.0)],
                        ACT= [(20.0,40.0),(5.0/2.0,15.0/2.0),(5.0,10.0)]
                        ), 
                        States())
    sim.run()
    avgQdelay, maxQDelay, avgTypeDelay, maxTypeDelay, avgOverallDelay, avgQlength, maxQlength, avgCustomerNumber, maxCustomerNumber, totalServed = sim.getResults()
    
    # print('avgQdelay')
    # for i in range(3):
    #     print('Q',i+1,": ",avgQdelay[i]/60.0)
    # print()

    # print('maxQdelay')
    # for i in range(3):
    #     print('Q',i+1,": ",maxQDelay[i]/60.)
    # print()

    # print('avgTypedelay')
    # for i in range(3):
    #     print('Type',i+1,": ",avgTypeDelay[i]/60.0)
    # print()

    # print('maxTypedelay')
    # for i in range(3):
    #     print('Q',i+1,": ",maxTypeDelay[i]/60.0)
    # print()

    print('overallDelay: ', avgOverallDelay/60.0)

    # print('avgQlength')
    # for i in range(3):
    #     print('Q',i+1,': ',avgQlength[i])
    # print()

    # print('maxQlength')
    # for i in range(3):
    #     print('Q',i+1,': ',maxQlength[i])
    # print()

    print('avgCustomerNumber: ', avgCustomerNumber)
    print('maxCustomerNumber: ', maxCustomerNumber)
    print('Total Served: ', totalServed,'\n')

def exp8():
    print('[2,2,3]')
    seed = 101
    np.random.seed(seed)
    
    zrng[1] = 1973272912
    sim = Simulator(seed)
    sim.configure(Params(meanArrivalTime=30,
                        groupSizeProbs= [0.5, 0.3, 0.1, 0.1],
                        routes= [[HOTFOOD,DRINKS,CASHIER], [SANDWICH,DRINKS,CASHIER],[DRINKS,CASHIER]],
                        routeProbs = [0.8, 0.15, 0.05],
                        staff= [2,2,3], #two servers added respectively at hotfood and sandwich
                        ST= [(50.0/2.0,120.0/2.0),(60/2.0,180/2.0),(5.0,20.0)],
                        ACT= [(20.0/2.0,40.0/2.0),(5.0/2.0,15.0/2.0),(5.0,10.0)]
                        ), 
                        States())
    sim.run()
    avgQdelay, maxQDelay, avgTypeDelay, maxTypeDelay, avgOverallDelay, avgQlength, maxQlength, avgCustomerNumber, maxCustomerNumber, totalServed = sim.getResults()
    
    # print('avgQdelay')
    # for i in range(3):
    #     print('Q',i+1,": ",avgQdelay[i]/60.0)
    # print()

    # print('maxQdelay')
    # for i in range(3):
    #     print('Q',i+1,": ",maxQDelay[i]/60.)
    # print()

    # print('avgTypedelay')
    # for i in range(3):
    #     print('Type',i+1,": ",avgTypeDelay[i]/60.0)
    # print()

    # print('maxTypedelay')
    # for i in range(3):
    #     print('Q',i+1,": ",maxTypeDelay[i]/60.0)
    # print()

    print('overallDelay: ', avgOverallDelay/60.0)

    # print('avgQlength')
    # for i in range(3):
    #     print('Q',i+1,': ',avgQlength[i])
    # print()

    # print('maxQlength')
    # for i in range(3):
    #     print('Q',i+1,': ',maxQlength[i])
    # print()

    print('avgCustomerNumber: ', avgCustomerNumber)
    print('maxCustomerNumber: ', maxCustomerNumber)
    print('Total Served: ', totalServed,'\n')

def main():
    base_case()
    thirdCashier()
    exp3()
    exp4()
    exp5()
    exp6()
    exp7()
    exp8()

if __name__ == "__main__":
    main()
