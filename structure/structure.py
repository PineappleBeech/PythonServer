import buffer
from block import block
from util.util import Direction
import nbt
from util.vector import Vec3


class SimpleStructure:
    def __init__(self, path, world):
        self.path = path
        self.world = world
        self.spawn_pos = None
        print("Loading structure " + path)
        self.load_structure()
        print("Structure loaded")

    def load_structure(self):
        self.blocks = {}

        with open("data/mystructure/structures/" + self.path + ".nbt", 'rb') as f:
            nbt_data = nbt.read_nbt(f, True)

        json = nbt.to_json(nbt_data)

        self.size = (json["size"][0], json["size"][1], json["size"][2])
        palette = [{"name": i['Name'], "state": i["Properties"] if "Properties" in i else None}
                   for i in json['palette']]

        jigsaw_connections = {}
        commands = CommandProcessor(self)

        for i in json['blocks']:
            pos = Vec3(i['pos'][0], i['pos'][1], i['pos'][2])
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
                    commands.add(Command(pos, Direction.from_string(b["state"]["facing"]), block_data["Command"]))

            self.blocks[pos].pos_in_structure = pos

        self.interconnect_blocks()

        commands.execute_all()

        for i in jigsaw_connections.values():
            target_jig = jigsaw_connections[i.target]
            self.blocks[i.pos].disconnect(i.direction)
            self.blocks[target_jig.pos].disconnect(target_jig.direction)
            self.blocks[i.pos].connect(i.direction, self.blocks[target_jig.pos], target_jig.direction)

        for i in self.blocks.values():
            self.world.add_block(i)


    def interconnect_blocks(self, repeat=False):
        for x in range(self.size[0]):
            for y in range(self.size[1]):
                for z in range(self.size[2]):
                    try:
                        target_block = self.blocks[Vec3(x+1, y, z)]
                    except KeyError:
                        if repeat:
                            target_block = self.blocks[Vec3(0, y, z)]
                            self.blocks[Vec3(x, y, z)].connect(Direction.EAST, target_block, Direction.WEST)
                    else:
                        self.blocks[Vec3(x, y, z)].connect(Direction.EAST, target_block, Direction.WEST)

                    try:
                        target_block = self.blocks[Vec3(x, y+1, z)]
                    except KeyError:
                        if repeat:
                            target_block = self.blocks[Vec3(x, 0, z)]
                            self.blocks[Vec3(x, y, z)].connect(Direction.UP, target_block, Direction.DOWN)
                    else:
                        self.blocks[Vec3(x, y, z)].connect(Direction.UP, target_block, Direction.DOWN)

                    try:
                        target_block = self.blocks[Vec3(x, y, z+1)]
                    except KeyError:
                        if repeat:
                            target_block = self.blocks[Vec3(x, y, 0)]
                            self.blocks[Vec3(x, y, z)].connect(Direction.SOUTH, target_block, Direction.NORTH)
                    else:
                        self.blocks[Vec3(x, y, z)].connect(Direction.SOUTH, target_block, Direction.NORTH)


class JigsawData:
    def __init__(self, pos, direction, name, target):
        self.pos = pos
        self.direction = direction
        self.name = name
        self.target = target


class Command:
    def __init__(self, pos, direction, command):
        self.pos = Vec3(pos)
        self.direction = direction
        self.command = command

    def execute(self, structure, processor):
        args = self.command.split()

        if args[0] == "playerspawn":
            structure.spawn_pos = self.pos

        elif args[0] == "connect":
            name = args[1]
            width = int(args[2])
            height = int(args[3])
            assert width % 2 == 1

            if name not in processor.half_connections:
                processor.half_connections[name] = (self.pos, self.direction, width, height)

            else:
                target_pos, target_direction, target_width, target_height = processor.half_connections[name]
                del processor.half_connections[name]
                target_pos = Vec3(target_pos)

                right = Direction.to_vector(Direction.rotate(self.direction, 1))
                target_left = Direction.to_vector(Direction.rotate(target_direction, -1))
                up = Direction.to_vector(Direction.UP)

                side = width // 2

                for x in range(-side, side+1):
                    for y in range(-1, height):
                        start_pos = self.pos + right * x + up * y
                        end_pos = target_pos + target_left * x + up * y
                        structure.blocks[start_pos].disconnect(self.direction)
                        structure.blocks[end_pos].disconnect(target_direction)
                        structure.blocks[start_pos].connect(self.direction, structure.blocks[end_pos], target_direction)


class CommandProcessor:
    def __init__(self, structure):
        self.structure = structure
        self.commands = []
        self.half_connections = {}

    def add(self, command):
        self.commands.append(command)

    def execute_all(self):
        for command in self.commands:
            command.execute(self.structure, self)

