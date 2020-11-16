
#       YIELD 
#Yield keyword returns a value and suspends the execution of a function
#The yield keyword merely suspends and return control to the caller
#when resumed, the function starting working from where it left off


# GENERATOR FUNCTION
#If a function or method body contains the yield keyword, in place of return;
#It becomes a generator.

# def SimpleGenerator():
#     yield 1
#     yield 2
#     yield 3

# for value in SimpleGenerator():
#     print(value)

#generator functions return generator objects
# x = SimpleGenerator()
# print(x.__next__())
# print(x.__next__())
# print(x.__next__())

#deriving fibonacci numbers using generator
def fibonacci(limit):
    a ,b = 0, 1

    while a<limit:
        yield a
        a,b = b, a+b

x = fibonacci(5)

print("sequential prints\n")
print(x.__next__())
print(x.__next__())
print(x.__next__())
print(x.__next__())
print(x.__next__())


print("loops\n")
for i in fibonacci(5):
    print(i)
