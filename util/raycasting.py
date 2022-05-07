import math
import os
import pickle

import numba
import numpy as np

from util.util import round_towards, round_away, integers_between, Direction, integers_between_numba

NORTH = 0x00
EAST = 0x01
SOUTH = 0x02
WEST = 0x03
UP = 0x04
DOWN = 0x05
INTERUPT = 0x06
BIT_MASK = 0x07

@numba.njit
def path(start, end):
    """
    Finds all grid edges intersecting the ray from start to end.
    Returns an integer with each 3 bits representing each intersection.
    """

    direction = (end[0] - start[0], end[1] - start[1], end[2] - start[2])
    length = (direction[0] ** 2 + direction[1] ** 2 + direction[2] ** 2) ** 0.5
    if length == 0:
        return [-1]
    direction = (direction[0] / length, direction[1] / length, direction[2] / length)

    x_steps = []
    y_steps = []
    z_steps = []

    for x in integers_between_numba(start[0], end[0]):
        x_steps.append((x - start[0]) / direction[0])

    for y in integers_between_numba(start[1], end[1]):
        y_steps.append((y - start[1]) / direction[1])

    for z in integers_between_numba(start[2], end[2]):
        z_steps.append((z - start[2]) / direction[2])

    x_counter = 0
    y_counter = 0
    z_counter = 0
    x_len = len(x_steps)
    y_len = len(y_steps)
    z_len = len(z_steps)
    x_steps.append(math.inf)
    y_steps.append(math.inf)
    z_steps.append(math.inf)
    x_current = x_steps[x_counter]
    y_current = y_steps[y_counter]
    z_current = z_steps[z_counter]
    x_direction = EAST if start[0] < end[0] else WEST
    y_direction = UP if start[1] < end[1] else DOWN
    z_direction = SOUTH if start[2] < end[2] else NORTH
    steps = []

    while x_counter < x_len or y_counter < y_len or z_counter < z_len:
        if x_current < y_current and x_current < z_current:
            x_counter += 1
            x_current = x_steps[x_counter]
            steps.append(x_direction)
        elif y_current < z_current:
            y_counter += 1
            y_current = y_steps[y_counter]
            steps.append(y_direction)
        else:
            z_counter += 1
            z_current = z_steps[z_counter]
            steps.append(z_direction)

    return steps


def path_og(start, end):
    direction = (end[0] - start[0], end[1] - start[1], end[2] - start[2])
    length = (direction[0] ** 2 + direction[1] ** 2 + direction[2] ** 2) ** 0.5
    if length == 0:
        return [-1]
    direction = (direction[0] / length, direction[1] / length, direction[2] / length)

    x_steps = []
    y_steps = []
    z_steps = []

    for x in integers_between(start[0], end[0]):
        x_steps.append((x - start[0]) / direction[0])

    for y in integers_between(start[1], end[1]):
        y_steps.append((y - start[1]) / direction[1])

    for z in integers_between(start[2], end[2]):
        z_steps.append((z - start[2]) / direction[2])

    x_counter = 0
    y_counter = 0
    z_counter = 0
    x_len = len(x_steps)
    y_len = len(y_steps)
    z_len = len(z_steps)
    x_steps.append(math.inf)
    y_steps.append(math.inf)
    z_steps.append(math.inf)
    x_current = x_steps[x_counter]
    y_current = y_steps[y_counter]
    z_current = z_steps[z_counter]
    x_direction = EAST if start[0] < end[0] else WEST
    y_direction = UP if start[1] < end[1] else DOWN
    z_direction = SOUTH if start[2] < end[2] else NORTH
    steps = []

    while x_counter < x_len or y_counter < y_len or z_counter < z_len:
        if x_current < y_current and x_current < z_current:
            x_counter += 1
            x_current = x_steps[x_counter]
            steps.append(x_direction)
        elif y_current < z_current:
            y_counter += 1
            y_current = y_steps[y_counter]
            steps.append(y_direction)
        else:
            z_counter += 1
            z_current = z_steps[z_counter]
            steps.append(z_direction)

    return steps


def path_to_list(path):
    """
    Converts a path to a list of directions.
    """

    directions = []
    while path:
        directions.append((path & BIT_MASK) - 1)
        path >>= 3

    return directions

def follow_directions(start_block, directions):
    """
    Follows a list of directions from a starting point.
    """
    current_block = start_block
    for direction in directions:
        current_block = current_block.get_block(direction)

    return current_block


paths = {}
paths_list = []
host_array = None
device_array = None


def quick_path(diff):
    """
    Returns a path from the middle of one block to the middle of another
    """
    try:
        return paths[diff]
    except KeyError:
        paths[diff] = path((0.5, 0.5, 0.5), (diff[0] + 0.5, diff[1] + 0.5, diff[2] + 0.5))

def gen_paths(distance):
    """
    Generates all paths to points within a certain distance of the origin.
    """
    global paths
    global paths_list
    global host_array
    global device_array

    if "cache" in os.listdir() and f"paths{distance}.pkl" in os.listdir("cache"):
        with open(f"cache/paths{distance}.pkl", "rb") as f:
            paths = pickle.load(f)
            print("Loaded paths from cache.")

    else:
        for x in range(-distance, distance + 1):
            for y in range(-distance, distance + 1):
                for z in range(-distance, distance + 1):
                    #if abs(x) == distance or abs(y) == distance or abs(z) == distance:
                    paths[(x, y, z)] = path((0.5, 0.5, 0.5), (x + 0.5, y + 0.5, z + 0.5))

            print("Generated paths for x = " + str(x))

        with open(f"cache/paths{distance}.pkl", "wb") as f:
            pickle.dump(paths, f)

        print("Generated Paths")

    paths_list = list(paths.values())

    max_path_len = distance * 3

    host_array = np.full((2 * distance + 1, 2 * distance + 1, 2 * distance + 1, max_path_len), -1, dtype=np.int32)

    for x in range(distance * 2 + 1):
        for y in range(distance * 2 + 1):
            for z in range(distance * 2 + 1):
                p = paths[(x - distance, y - distance, z - distance)]
                for i, direction in enumerate(p):
                    host_array[x, y, z, i] = direction

    device_array = numba.cuda.to_device(host_array)

    print("Loaded device array")
