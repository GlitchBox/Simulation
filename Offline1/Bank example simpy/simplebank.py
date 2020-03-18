import simpy

class Customer:

    def __init__(self, env, name, timeInBank):
        self.env = env
        self.name = name
        self.timeBank = timeInBank

    def visit(self, timeBank):
        print(f'{self.env.now},{self.name}, Here I am')
        yield self.env


if __name__=="__main__":
    env = simpy.Environment()