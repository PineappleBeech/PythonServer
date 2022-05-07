import queue
import threading
from threading import Lock
import math
from enum import Enum

import numba
import numpy as np


class AtomicInteger:
    def __init__(self, value=0):
        self.value = value
        self.lock = Lock()

    def increment_and_get(self):
        with self.lock:
            self.value += 1
            return self.value


class TaskExecutor:
    def __init__(self):
        self.tasks = queue.Queue()
        self.thread = threading.Thread(target=self.run)
        self.thread.start()

    def add_task(self, func, *args, **kwargs):
        self.tasks.put((func, args, kwargs))

    def run(self):
        while True:
            func, args, kwargs = self.tasks.get()
            func(*args, **kwargs)


class Direction:
    NORTH = 0
    EAST = 1
    SOUTH = 2
    WEST = 3
    UP = 4
    DOWN = 5

    @staticmethod
    def get_opposite(value):
        if value == 0:
            return 2
        elif value == 1:
            return 3
        elif value == 2:
            return 0
        elif value == 3:
            return 1
        elif value == 4:
            return 5
        elif value == 5:
            return 4

    @staticmethod
    def rotate(value, amount):
        if amount == 0:
            return value
        elif value == 4:
            return value
        elif value == 5:
            return value
        else:
            return (value + amount) % 4


def round_towards(value, target):
    if value < target:
        return math.ceil(value)
    else:
        return math.floor(value)

def round_away(value, target):
    if value < target:
        return math.floor(value)
    else:
        return math.ceil(value)

def integers_between(start, end):
    if start > end:
        return range(math.floor(start), math.floor(end), -1)
    else:
        return range(math.floor(start) + 1, math.floor(end) + 1)

@numba.njit
def integers_between_numba(start, end):
    if start > end:
        return range(math.floor(start), math.floor(end), -1)
    else:
        return range(math.floor(start) + 1, math.floor(end) + 1)

# [0 1 2 3 4 5 6 7 8 9] -> [0 1 2 3 4 5 6 7] -> [-1 -1 0 1 2 3 4 5 6 7] 2
# [0 1 2 3 4 5 6 7 8 9] -> [2 3 4 5 6 7 8 9] -> [2 3 4 5 6 7 8 9 -1 -1] -2
def shift_and_pad(array, shift, pad_value):
    x_start = -min(0, shift[0])
    x_end = array.shape[0] - max(0, shift[0])
    y_start = -min(0, shift[1])
    y_end = array.shape[1] - max(0, shift[1])
    z_start = -min(0, shift[2])
    z_end = array.shape[2] - max(0, shift[2])
    shrunk = array[x_start:x_end, y_start:y_end, z_start:z_end]
    print(shrunk.shape)
    result = np.pad(shrunk, ((max(0, shift[0]), -min(0, shift[0])),
                   (max(0, shift[1]), -min(0, shift[1])),
                   (max(0, shift[2]), -min(0, shift[2]))),
                   'constant', constant_values=pad_value)
    return result
