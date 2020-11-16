#a process can be used like an event
#if I yield a process, I will be resumed once the process is finished
import simpy

class Car:

    def __init__(self, env):
        
        self.env = env
        self.runAction = env.process(self.run())

    def run(self):
        while True:
            print("The car starts driving at: ", self.env.now)
            tripDuration = 2
            yield self.env.timeout(tripDuration)

            print("The car will now park and start charging at: ", self.env.now)
            chargeDuration = 5
            yield self.env.process(self.charge(chargeDuration))

    def charge(self, chargeDuration):
        yield self.env.timeout(chargeDuration)

if __name__=="__main__":
    env = simpy.Environment()
    car = Car(env)
    env.run(until=20)