#when a process doesn't not wait for another process to finish(or an event to occur)
#the first process can interrupt the second process
import simpy

class Car:

    def __init__(self, env):
        
        self.env = env
        self.runAction = env.process(self.run())

    def run(self):
        while True:
            print("The car starts driving at: ", self.env.now)
            tripDuration = 2
            try:
                yield self.env.timeout(tripDuration)
            except simpy.Interrupt:
                print("Some problem with the battery. Gotta recharge.")

            print("The car will now park and start charging at: ", self.env.now)
            chargeDuration = 5
            try:
                yield self.env.process(self.charge(chargeDuration))
            except simpy.Interrupt:
                print('Was interrupted. Hope the battery was charged well enough')

    def charge(self, chargeDuration):
        yield self.env.timeout(chargeDuration)


def driver(env, car):
   while True:
        #the chargre process waits for 5 seconds
        #we wish to interrupt the process after 3 seconds
        yield env.timeout(1)
        #here we aim to interrupt the run process, because that process
        #runs forever
        car.runAction.interrupt() 

if __name__=="__main__":
    env = simpy.Environment()
    car = Car(env)
    env.process(driver(env, car))

    env.run(until=20)