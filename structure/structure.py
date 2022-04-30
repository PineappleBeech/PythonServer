import buffer
from block import block
from util.util import Direction
import nbt

class SimpleStructure:
    def __init__(self, path):
        self.path = path
        self.load_structure()

    def load_structure(self):
        self.blocks = {}

        with open("data/mystructure/structures/" + self.path + ".nbt", 'rb') as f:
            nbt_data = nbt.read_nbt(f, True)

        json = nbt.to_json(nbt_data)

        self.size = (json["size"][0], json["size"][1], json["size"][2])
        palette = [{"name": i['Name'], "state": i["Properties"] if "Properties" in i else None}
                   for i in json['palette']]

        for i in json['blocks']:
            b = palette[i["state"]]
            self.blocks[(i["pos"][0], i["pos"][1], i["pos"][2])] = block.SimpleBlock(b["name"], b["state"])

        for x in range(self.size[0]):
            for y in range(self.size[1]):
                for z in range(self.size[2]):
                    try:
                        target_block = self.blocks[(x+1, y, z)]
                    except KeyError:
                        target_block = self.blocks[(0, y, z)]
                        self.blocks[(x, y, z)].connect(Direction.EAST, target_block, Direction.WEST)
                    else:
                        self.blocks[(x, y, z)].connect(Direction.EAST, target_block, Direction.WEST)

                    try:
                        target_block = self.blocks[(x, y+1, z)]
                    except KeyError:
                        target_block = self.blocks[(x, 0, z)]
                        self.blocks[(x, y, z)].connect(Direction.UP, target_block, Direction.DOWN)
                    else:
                        self.blocks[(x, y, z)].connect(Direction.UP, target_block, Direction.DOWN)

                    try:
                        target_block = self.blocks[(x, y, z+1)]
                    except KeyError:
                        target_block = self.blocks[(x, y, 0)]
                        self.blocks[(x, y, z)].connect(Direction.SOUTH, target_block, Direction.NORTH)
                    else:
                        self.blocks[(x, y, z)].connect(Direction.SOUTH, target_block, Direction.NORTH)

