#processes are described by generator functions
#during the lifetime of a process, the process function(generator function) 
#creates events and yields them

#when a process yields an event, it gets suspended
#Simpy resumes the process when the event is triggered
#multiple processes waiting on the same event is resumed in the same order
#it yielded the event

import simpy

def car(env):
    # i = 0
    # while i<=10:
    while True:
        print("The car will start parking at: ",env.now)
        parking_timeout = 5
        yield env.timeout(parking_timeout)

        print("The car will start driving at: ",env.now)
        driving_timeout = 2
        yield env.timeout(driving_timeout)

        # if i == 10:
        #     print("the car is done moving")
        #     yield env.timeout(1)
        # i += 1


env = simpy.Environment()
env.process(car(env)) #the generator function creates the process called car
#env.run()
env.run(until=20)


    