import math
import time

import numba
from line_profiler_pycharm import profile

import nbt
from block import block
from network.clientbound import play
from util.util import round_towards, round_away, Direction
from util import raycasting

class World:
    def __init__(self):
        self.hardcore = False
        self.players = []
        self.dimension_type = DimensionType()

    @property
    def min_y(self):
        return self.dimension_type.min_y

    @property
    def height(self):
        return self.dimension_type.height

    def tick(self):
        pass


class WorldView:
    block_render_distance = 32

    def __init__(self, world, player):
        self.world = world
        self.player = player
        self.chunks = {}
        self.last_player_block_pos = (math.floor(self.player.client_position[0]), math.floor(self.player.client_position[1]), math.floor(self.player.client_position[2]))
        self.AIR = block.BlockView(block.Block("minecraft:air"))
        self.blocks = {(x, y, z): self.AIR for x in range(self.last_player_block_pos[0]-self.block_render_distance, self.last_player_block_pos[0]+self.block_render_distance+1)
                       for y in range(self.last_player_block_pos[1]-self.block_render_distance, self.last_player_block_pos[1]+self.block_render_distance+1)
                       for z in range(self.last_player_block_pos[2]-self.block_render_distance, self.last_player_block_pos[2]+self.block_render_distance+1)}


        self.STONE = block.Block("minecraft:stone")
        self.update_view()
        self.load_chunks()

    @profile
    def update_view(self):
        s = time.time()
        new_blocks = {}
        changed_blocks = {}
        new_player_position = (int(self.player.client_position[0]), int(self.player.client_position[1]), int(self.player.client_position[2]))
        block_pos_diff = (math.floor(new_player_position[0]) - self.last_player_block_pos[0],
                          math.floor(new_player_position[1]) - self.last_player_block_pos[1],
                          math.floor(new_player_position[2]) - self.last_player_block_pos[2])
        start_block = block.BlockView(self.player.block)

        #self.calculate_block(new_player_position, start_block, block_pos_diff, new_blocks, changed_blocks, raycasting.paths_list)

        length = len(raycasting.paths_list)
        i = 0

        for path in raycasting.paths_list:
            self.calculate_ray(start_block, new_player_position, path, block_pos_diff, new_blocks, changed_blocks, self.blocks)
            i += 1
            if i % 1000 == 0:
                print("Traced {}/{} Rays".format(i, length))

        self.last_player_block_pos = (math.floor(new_player_position[0]), math.floor(new_player_position[1]), math.floor(new_player_position[2]))
        self.blocks = {k: block.BlockView(*v) for k, v in new_blocks.items()}

        chunks = {}
        for block_pos in changed_blocks:
            chunk_pos = (block_pos[0] // 16, block_pos[2] // 16)
            if chunk_pos not in chunks:
                chunks[chunk_pos] = {}
            chunks[chunk_pos][block_pos] = changed_blocks[block_pos]

        for chunk_pos in self.chunks:
            for block_pos in chunks[chunk_pos]:
                self.chunks[chunk_pos].update_heightmap(block_pos[0], block_pos[1], block_pos[2], self.blocks[block_pos] == self.AIR)
                self.player.conn.send_packet(play.BlockChange(block_pos[0], block_pos[1], block_pos[2], self.blocks[block_pos].get_id()))

        print("WorldView update took {} seconds".format(time.time() - s))

    @staticmethod
    @numba.vectorize(target="cuda")
    def calculate_ray(start_block, start_pos, ray, pos_diff, new_blocks, changed_blocks, old_blocks):
        current_block = start_block.block
        current_transform = start_block.transform

        x = start_pos[0]
        y = start_pos[1]
        z = start_pos[2]
        dx = pos_diff[0]
        dy = pos_diff[1]
        dz = pos_diff[2]
        for next_direction in ray:
            if next_direction == 0:
                z -= 1
            elif next_direction == 1:
                x += 1
            elif next_direction == 2:
                z += 1
            elif next_direction == 3:
                x -= 1
            elif next_direction == 4:
                y += 1
            else:
                y -= 1

            current_block, current_transform = block.BlockView.fast_get_block(next_direction, current_block, current_transform)
            if (x, y, z) not in new_blocks:
                new_blocks[(x, y, z)] = (current_block, current_transform)
                b = old_blocks[(x - dx, y - dy, z - dz)]
                if (b.block, b.transform) != (current_block, current_transform):
                    changed_blocks[(x, y, z)] = (current_block, current_transform)





    @profile
    def calculate_block(self, current_pos, current_block, pos_diff, new_blocks, changed_blocks, current_paths):
        assert isinstance(current_block, block.BlockView)
        new_blocks[current_pos] = current_block
        if self.blocks[(current_pos[0] - pos_diff[0], current_pos[1] - pos_diff[1], current_pos[2] - pos_diff[2])] != current_block:
            changed_blocks[current_pos] = current_block

        paths_in_direction = [[], [], [], [], [], []]
        for path in current_paths:
            if path != 0:
                paths_in_direction[(path & 0x07) - 1].append(path >> 3)

        for i, direction in enumerate(((0, 0, -1), (1, 0, 0), (0, 0, 1), (-1, 0, 0), (0, 1, 0), (0, -1, 0))):
            if paths_in_direction[i] == []:
                continue
            next_pos = (current_pos[0] + direction[0], current_pos[1] + direction[1], current_pos[2] + direction[2])
            try:
                next_block = current_block.get_block(Direction(i))
            except block.NoBlock as e:
                new_blocks[next_pos] = block.BlockView(block.Block(e.block_id))
            else:
                self.calculate_block(next_pos,
                                     next_block,
                                     pos_diff,
                                     new_blocks,
                                     changed_blocks,
                                     paths_in_direction[i])

    def get_block(self, x, y, z):
        try:
            return self.blocks[(x, y, z)]
        except KeyError:
            return self.AIR

    def block_in_render_distance(self, x, y, z):
        return abs(self.last_player_block_pos[0] - x) <= self.block_render_distance\
               and abs(self.last_player_block_pos[1] - y) <= self.block_render_distance\
               and abs(self.last_player_block_pos[2] - z) <= self.block_render_distance

    def column_in_render_distance(self, x, z):
        return abs(self.last_player_block_pos[0] - x) <= self.block_render_distance\
               and abs(self.last_player_block_pos[2] - z) <= self.block_render_distance

    def load_chunks(self):
        mid_chunk_pos = (int(self.player.client_position[0] // 16), int(self.player.client_position[2] // 16))
        distance = 5
        for z in range(-distance, distance + 1):
            for x in range(-distance, distance + 1):
                self.chunks[(mid_chunk_pos[0] + x, mid_chunk_pos[1] + z)] = ChunkView(self, mid_chunk_pos[0] + x, mid_chunk_pos[1] + z)


class ChunkView:
    def __init__(self, world_view, x, z):
        self.world_view = world_view
        self.x = x
        self.z = z
        self.gen_heightmap()
        self.world_view.player.conn.send_packet(play.ChunkData(self.x, self.z, self))

    @property
    def section_count(self):
        return self.world_view.world.height // 16

    def get_block(self, x, y, z):
        assert x < 16
        assert z < 16
        return self.world_view.get_block(self.x * 16 + x, y, self.z * 16 + z)

    @profile
    def get_block_id(self, x, y, z):
        if self.world_view.block_in_render_distance(self.x * 16 + x, y, self.z * 16 + z):
            return self.get_block(x, y, z).get_id()
        else:
            return 0

    def set_block(self, x, y, z, block):
        assert x < 16
        assert z < 16
        self.world_view.set_block(self.x * 16 + x, y, self.z * 16 + z, block)

    def gen_heightmap(self):
        self.heightmap = [0] * 256
        if not self.in_render_distance():
            return

        for z in range(16):
            for x in range(16):
                for y in range(self.world_view.world.min_y+self.world_view.world.height-1, self.world_view.world.min_y-1, -1):
                    if self.get_block(x, y, z).block.name != "minecraft:air":
                        self.heightmap[x + z * 16] = y
                        break

    def update_heightmap(self, x, y, z, is_air):
        assert x < 16
        assert z < 16

        if is_air:
            if self.heightmap[x + z * 16] == y:
                for yy in range(y, self.world_view.world.min_y, -1):
                    if self.get_block(x, yy, z).name != "minecraft:air":
                        self.heightmap[x + z * 16] = yy
                        break
        else:
            if self.heightmap[x + z * 16] < y:
                self.heightmap[x + z * 16] = y

    def in_render_distance(self):
        return self.world_view.column_in_render_distance(self.x * 16, self.z * 16)\
               or self.world_view.column_in_render_distance(self.x * 16 + 15, self.z * 16 + 15)\
               or self.world_view.column_in_render_distance(self.x * 16, self.z * 16 + 15)\
               or self.world_view.column_in_render_distance(self.x * 16 + 15, self.z * 16)



class DimensionType:
    def __init__(self):
        self.piglin_safe = False
        self.natural = False
        self.ambient_light = 15
        self.infiniburn = "#minecraft:infiniburn_overworld"
        self.respawn_anchor_works = False
        self.has_skylight = True
        self.bed_works = False
        self.effects = "minecraft:overworld"
        self.has_raids = False
        self.min_y = 0
        self.height = 256
        self.logical_height = 256
        self.coordinate_scale = 1
        self.ultrawarm = False
        self.has_ceiling = False

    def to_nbt(self):
        return nbt.NBT_Compound({
            "piglin_safe": nbt.NBT_Byte(self.piglin_safe),
            "natural": nbt.NBT_Byte(self.natural),
            "ambient_light": nbt.NBT_Float(self.ambient_light),
            "infiniburn": nbt.NBT_String(self.infiniburn),
            "respawn_anchor_works": nbt.NBT_Byte(self.respawn_anchor_works),
            "has_skylight": nbt.NBT_Byte(self.has_skylight),
            "bed_works": nbt.NBT_Byte(self.bed_works),
            "effects": nbt.NBT_String(self.effects),
            "has_raids": nbt.NBT_Byte(self.has_raids),
            "min_y": nbt.NBT_Int(self.min_y),
            "height": nbt.NBT_Int(self.height),
            "logical_height": nbt.NBT_Int(self.logical_height),
            "coordinate_scale": nbt.NBT_Double(self.coordinate_scale),
            "ultrawarm": nbt.NBT_Byte(self.ultrawarm),
            "has_ceiling": nbt.NBT_Byte(self.has_ceiling)
        })


class Biome:
    def __init__(self):
        self.precipitation = "rain"
        self.temperature = 0.8
        self.downfall = 0.4
        self.category = "plains"
        self.effects = {"sky_color": 0x78A7FF,
                        "water_fog_color": 0x050533,
                        "fog_color": 0xC0D8FF,
                        "water_color": 0x4159204}

    def to_nbt(self):
        return nbt.NBT_Compound({
            "precipitation": nbt.NBT_String(self.precipitation),
            "temperature": nbt.NBT_Float(self.temperature),
            "downfall": nbt.NBT_Float(self.downfall),
            "category": nbt.NBT_String(self.category),
            "effects": nbt.NBT_Compound({
                "sky_color": nbt.NBT_Int(self.effects["sky_color"]),
                "water_fog_color": nbt.NBT_Int(self.effects["water_fog_color"]),
                "fog_color": nbt.NBT_Int(self.effects["fog_color"]),
                "water_color": nbt.NBT_Int(self.effects["water_color"])
            })})

