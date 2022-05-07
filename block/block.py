import json

import numba.experimental

from util.util import Direction, AtomicInteger


class BlockType:
    def __init__(self, name, id_start, properties, default_properties):
        self.name = name
        self.id_start = id_start
        self.properties = properties
        self.default_properties = default_properties


class Block:
    id_counter = AtomicInteger()

    def __init__(self, id, state=None):
        self.id = Block.id_counter.increment_and_get()

        if isinstance(id, str):
            self.name = id
        elif isinstance(id, int):
            self.name, state = blocks_by_id[id]
        self.state = state
        self.type = blocks[self.name]

    def __eq__(self, other):
        return self.name == other.name and self.state == other.state

    def get_id(self):
        if self.type.properties == {}:
            return self.type.id_start
        else:
            offset = 0
            for property in self.type.properties:
                offset *= len(self.type.properties[property])
                try:
                    value = self.state[property]
                except KeyError:
                    value = self.type.default_properties[property]
                except TypeError:
                    value = self.type.default_properties[property]

                offset += self.type.properties[property].index(value)
            return self.type.id_start + offset


class Transform:
    __slots__ = "rotation", "flip_x", "flip_y"

    def __init__(self, rotation=0, flip_x=False, flip_y=False):
        self.rotation = rotation
        self.flip_x = flip_x
        self.flip_y = flip_y

    def apply(self, x, y, z):
        self.fast_apply(x, y, z, self.rotation, self.flip_x, self.flip_y)

    @staticmethod
    def fast_apply(x, y, z, rotation=0, flip_x=False, flip_y=False):
        if rotation == 0:
            pass
        elif rotation == 1:
            x, z = z, -x
        elif rotation == 2:
            x, z = -x, -z
        elif rotation == 3:
            x, z = -z, x
        if flip_x:
            x = -x
        if flip_y:
            z = -z
        return x, y, z


class SimpleBlock(Block):
    def __init__(self, id, state=None):
        super().__init__(id, state)
        self.neighbors = [None, None, None, None, None, None]

    def connect(self, direction, block, target_face):
        self.neighbors[direction] = (block, target_face)
        block.neighbors[target_face] = (self, direction)

    def get_block(self, direction):
        try:
            return self.neighbors[direction][0]
        except TypeError:
            raise NoBlock("", 0)


class BlockView:
    __slots__ = ["block", "transform"]

    def __init__(self, block, transform=None):
        self.block = block
        self.transform = transform
        if self.transform is None:
            return
            self.transform = Transform()

    def __eq__(self, other):
        return self.block == other.block

    def get_block(self, direction):
        BlockView(self.fast_get_block(direction, self.block, self.transform))

    @staticmethod
    def fast_get_block(direction, block, transform=None):
        if (b := block.neighbors[direction]) is not None:
            return b
        else:
            raise NoBlock("", 0)

    def get_id(self):
        return self.block.get_id()


fast_block_type = numba.deferred_type()


@numba.experimental.jitclass([
    ("block_id", numba.int32),
    ("id", numba.int32),
    ("real", numba.boolean),
    ("neighbors", numba.typeof(numba.typed.List.empty_list(numba.int32)))])
class FastBlock:
    def __init__(self, block_id, id, real):
        self.block_id = block_id
        self.id = id
        self.real = real
        self.neighbors = numba.typed.List.empty_list(numba.int32)

    def get_block(self, direction):
        if self.real:
            return self.neighbors[direction]
        else:
            return self.id


fast_block_type.define(FastBlock.class_type.instance_type)


@numba.experimental.jitclass([
    ("rotation", numba.int32),
    ("flip_x", numba.boolean),
    ("flip_y", numba.boolean)])
class FastTransform:
    def __init__(self, rotation, flip_x, flip_y):
        self.rotation = rotation
        self.flip_x = flip_x
        self.flip_y = flip_y


@numba.experimental.jitclass([
    ("block", FastBlock.class_type.instance_type),
    ("transform", FastTransform.class_type.instance_type)])
class FastBlockView:
    def __init__(self, block, transform):
        self.block = block
        self.transform = transform

    def get_block(self, direction):
        return FastBlockView(self.block.get_block(direction), self.transform)


class NoBlock(Exception):
    def __init__(self, message, block_id):
        super().__init__(message)
        self.block_id = block_id


blocks = {}

blocks_by_id = []

def load_blocks():
    global blocks
    global blocks_by_id
    blocks = {}
    blocks_by_id = {}
    with open("data_generator/generated/reports/blocks.json", "r") as f:
        data = json.load(f)
        for block in data:
            if "properties" in data[block]:
                properties = data[block]["properties"]
                for i in data[block]["states"]:
                    try:
                        i["default"]
                    except KeyError:
                        pass
                    else:
                        default_properties = i["properties"]
                blocks[block] = BlockType(block, data[block]["states"][0]["id"], properties, default_properties)
            else:
                blocks[block] = BlockType(block, data[block]["states"][0]["id"], {}, {})

            for state in data[block]["states"]:
                try:
                    blocks_by_id[state["id"]] = (block, state["properties"])
                except KeyError:
                    blocks_by_id[state["id"]] = (block, None)

    return blocks