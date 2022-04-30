import random
import time

reps = 10000

def process(data):
    return data

def gen_int():
    num = 0

    for i in range(100):
        num = (num << 3) | random.randint(1, 6)

    return num

def gen_list():
    l = []
    for i in range(100):
        l.append(random.randint(0, 5))
    return l

def test_int():
    l = []
    for i in range(reps):
        l.append(gen_int())

    s = time.time()

    for i in l:
        while i != 0:
            d = (i & 0x07) - 1
            i >>= 3
            process(d)

    print("Int:", time.time() - s)

def test_list():
    l = []
    for i in range(reps):
        l.append(gen_list())

    s = time.time()

    for i in l:
        for j in i:
            process(j)

    print("List:", time.time() - s)

if __name__ == "__main__":
    test_int()
    test_list()