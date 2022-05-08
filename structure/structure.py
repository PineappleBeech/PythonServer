import buffer
from block import block
from util.util import Direction
import nbt

class SimpleStructure:
    def __init__(self, path):
        self.path = path
        self.spawn_pos = None
        self.load_structure()

    def load_structure(self):
        self.blocks = {}

        with open("data/mystructure/structures/" + self.path + ".nbt", 'rb') as f:
            nbt_data = nbt.read_nbt(f, True)

        json = nbt.to_json(nbt_data)

        self.size = (json["size"][0], json["size"][1], json["size"][2])
        palette = [{"name": i['Name'], "state": i["Properties"] if "Properties" in i else None}
                   for i in json['palette']]

        jigsaw_connections = {}

        for i in json['blocks']:
            pos = (i['pos'][0], i['pos'][1], i['pos'][2])
            b = palette[i["state"]]
            if b["name"] not in ["minecraft:jigsaw", "minecraft:command_block"]:
                self.blocks[pos] = block.SimpleBlock(b["name"], b["state"])
            else:
                if b["name"] == "minecraft:jigsaw":
                    block_data = i["nbt"]
                    self.blocks[pos] = block.SimpleBlock(block_data["final_state"])
                    direction = Direction.from_string(b["state"]["orientation"].split("_")[0])
                    jigsaw_connections[block_data["name"]] = JigsawData(pos, direction, block_data["name"], block_data["target"])

                elif b["name"] == "minecraft:command_block":
                    self.blocks[pos] = block.SimpleBlock("minecraft:air")

                    block_data = i["nbt"]
                    if block_data["Command"] == "playerspawn":
                        self.spawn_pos = pos

            self.blocks[pos].pos_in_structure = pos


        self.interconnect_blocks()


        for i in jigsaw_connections.values():
            target_jig = jigsaw_connections[i.target]
            self.blocks[i.pos].disconnect(i.direction)
            self.blocks[target_jig.pos].disconnect(target_jig.direction)
            self.blocks[i.pos].connect(i.direction, self.blocks[target_jig.pos], target_jig.direction)


    def interconnect_blocks(self, repeat=False):
        for x in range(self.size[0]):
            for y in range(self.size[1]):
                for z in range(self.size[2]):
                    try:
                        target_block = self.blocks[(x+1, y, z)]
                    except KeyError:
                        if repeat:
                            target_block = self.blocks[(0, y, z)]
                            self.blocks[(x, y, z)].connect(Direction.EAST, target_block, Direction.WEST)
                    else:
                        self.blocks[(x, y, z)].connect(Direction.EAST, target_block, Direction.WEST)

                    try:
                        target_block = self.blocks[(x, y+1, z)]
                    except KeyError:
                        if repeat:
                            target_block = self.blocks[(x, 0, z)]
                            self.blocks[(x, y, z)].connect(Direction.UP, target_block, Direction.DOWN)
                    else:
                        self.blocks[(x, y, z)].connect(Direction.UP, target_block, Direction.DOWN)

                    try:
                        target_block = self.blocks[(x, y, z+1)]
                    except KeyError:
                        if repeat:
                            target_block = self.blocks[(x, y, 0)]
                            self.blocks[(x, y, z)].connect(Direction.SOUTH, target_block, Direction.NORTH)
                    else:
                        self.blocks[(x, y, z)].connect(Direction.SOUTH, target_block, Direction.NORTH)


class JigsawData:
    def __init__(self, pos, direction, name, target):
        self.pos = pos
        self.direction = direction
        self.name = name
        self.target = target
