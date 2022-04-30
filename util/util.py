import queue
import threading
from threading import Lock
import math
from enum import Enum

import numba


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

#@numba.njit
def integers_between(start, end):
    if start > end:
        return range(int(start), int(end), -1)
    else:
        return range(int(start) + 1, int(end) + 1)
