import math
import time

import numba
import numpy
from line_profiler_pycharm import profile
import numpy as np

import nbt
from block import block
from network.clientbound import play
from util.util import shift_and_pad
from util import raycasting


BLOCK_RENDER_DISTANCE = 32

USE_CUDA = False


class World:
    def __init__(self):
        self.hardcore = False
        self.players = []
        self.dimension_type = DimensionType()
        self.blocks = {}

    @property
    def min_y(self):
        return self.dimension_type.min_y

    @property
    def height(self):
        return self.dimension_type.height

    def tick(self):
        pass


class WorldView:
    block_render_distance = BLOCK_RENDER_DISTANCE

    def __init__(self, world, player):
        self.world = world
        self.player = player
        self.chunks = {}
        self.last_player_block_pos = (math.floor(self.player.client_position[0]), math.floor(self.player.client_position[1]), math.floor(self.player.client_position[2]))
        self.AIR = block.Block("minecraft:air")
        self.AIR_VIEW = block.BlockView(self.AIR)
        self.blocks = {}
        self.block_id_array = numpy.full((self.block_render_distance*2+1, self.block_render_distance*2+1, self.block_render_distance*2+1), -1, dtype=numpy.int32)
        self.block_id_to_block = {}

        self.STONE = block.Block("minecraft:stone")
        self.update_view()
        self.load_chunks()


    @profile
    def update_view(self):
        s = time.time()
        new_player_position = (int(self.player.client_position[0]), int(self.player.client_position[1]), int(self.player.client_position[2]))
        block_pos_diff = (math.floor(new_player_position[0]) - self.last_player_block_pos[0],
                          math.floor(new_player_position[1]) - self.last_player_block_pos[1],
                          math.floor(new_player_position[2]) - self.last_player_block_pos[2])
        start_block = block.BlockView(self.player.block)

        block_map = {}
        WorldView.map_blocks(block_map, start_block.block)
        #fast_block_map = numba.typed.Dict.empty(key_type=numba.types.int32, value_type=numba.types.int32)
        #for key, value in enumerate(block_map.keys()):
        #    fast_block_map[key] = value
        fast_block_map = np.array(list(block_map.keys()), dtype=np.int32)
        block_neighbor_ids = np.zeros((len(block_map), 6), dtype=np.int32)
        WorldView.map_block_ids(block_map, block_neighbor_ids)

        #fast_new_blocks = np.zeros((BLOCK_RENDER_DISTANCE * 2 + 1, BLOCK_RENDER_DISTANCE * 2 + 1, BLOCK_RENDER_DISTANCE * 2 + 1), dtype=np.int32)

        print("Preparation time:", time.time() - s)
        s = time.time()
        print("Block pos diff:", block_pos_diff)

        if USE_CUDA:
            device_new_blocks = WorldView.calculate_ray(raycasting.device_array, block_neighbor_ids)
            fast_new_blocks = device_new_blocks.copy_to_host()
        else:
            fast_new_blocks = WorldView.calculate_ray(raycasting.host_array, block_neighbor_ids)

        print("Raycasting time:", time.time() - s)
        s = time.time()

        #new_block_id_array = numpy.empty((self.block_render_distance*2+1, self.block_render_distance*2+1, self.block_render_distance*2+1), dtype=numpy.int32)
        #WorldView.map_new_blocks_to_array(new_block_id_array, fast_new_blocks, fast_block_map)

        old_block_id_array = shift_and_pad(self.block_id_array, (-block_pos_diff[0], -block_pos_diff[1], -block_pos_diff[2]), -1)

        new_block_id_array = WorldView.map_new_blocks_vector(fast_new_blocks, fast_block_map, old_block_id_array)

        changed_blocks = np.argwhere(new_block_id_array != old_block_id_array)

        self.blocks = {}
        self.block_id_array = new_block_id_array
        self.block_id_to_block = block_map

        self.last_player_block_pos = (math.floor(new_player_position[0]), math.floor(new_player_position[1]), math.floor(new_player_position[2]))

        chunks = {}
        for block_pos in changed_blocks:
            real_pos = (block_pos[0] + self.last_player_block_pos[0] - BLOCK_RENDER_DISTANCE,
                        block_pos[1] + self.last_player_block_pos[1] - BLOCK_RENDER_DISTANCE,
                        block_pos[2] + self.last_player_block_pos[2] - BLOCK_RENDER_DISTANCE)

            chunk_pos = (real_pos[0] // 16, real_pos[2] // 16)
            if chunk_pos not in chunks:
                chunks[chunk_pos] = []
            chunks[chunk_pos].append(real_pos)

        for chunk_pos in self.chunks:
            for block_pos in chunks[chunk_pos]:
                self.chunks[chunk_pos].update_heightmap(block_pos[0], block_pos[1], block_pos[2], self.get_block(*block_pos).block == self.AIR)
                self.player.conn.send_packet(play.BlockChange(block_pos[0], block_pos[1], block_pos[2], self.get_block(*block_pos).get_id()))

        print("WorldView update took {} seconds".format(time.time() - s))
        #raise Exception

    @staticmethod
    @numba.guvectorize(["void(int32[:], int32[:,:], int32[:])"], "(n), (m,p) -> ()", target="cuda" if USE_CUDA else "parallel")
    def calculate_ray(ray, blocks, out):
        current_block = 0

        x = BLOCK_RENDER_DISTANCE + 1
        y = BLOCK_RENDER_DISTANCE + 1
        z = BLOCK_RENDER_DISTANCE + 1
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
            elif next_direction == 5:
                y -= 1
            else:
                break

            current_block = blocks[current_block, next_direction]

            if current_block == -1:
                break

        out[:] = current_block


    @staticmethod
    def map_fast_blocks(fast_block_map, current_block):
        if current_block.id in fast_block_map:
            return

        fast_current_block = block.FastBlock(current_block.get_id(), current_block.id, True)

        fast_block_map[current_block.id] = fast_current_block

        for direction in range(6):
            next_block = current_block.get_block(direction)
            WorldView.map_fast_blocks(fast_block_map, next_block)
            fast_current_block.neighbors.append(next_block.id)

    @staticmethod
    def map_blocks(blocks, current_block):
        if current_block.id in blocks:
            return

        blocks[current_block.id] = current_block

        for direction in range(6):
            try:
                next_block = current_block.get_block(direction)
            except block.NoBlock:
                pass
            else:
                WorldView.map_blocks(blocks, next_block)

    @staticmethod
    def map_block_ids(blocks, block_neighbor_ids):
        block_id_to_array_id = {k: v for v, k in enumerate(blocks.keys())}

        for i, key in enumerate(blocks.keys()):
            b = blocks[key]
            for direction in range(6):
                try:
                    next_block = b.get_block(direction)
                except block.NoBlock:
                    block_neighbor_ids[i, direction] = -1
                else:
                    block_neighbor_ids[i, direction] = block_id_to_array_id[next_block.id]

    @staticmethod
    @numba.njit(parallel=True)
    def map_new_blocks_to_array(new_block_id_array, fast_new_block_array, index_to_id):
        for x in numba.prange(BLOCK_RENDER_DISTANCE * 2 + 1):
            for y in numba.prange(BLOCK_RENDER_DISTANCE * 2 + 1):
                for z in numba.prange(BLOCK_RENDER_DISTANCE * 2 + 1):
                    new_block_id = index_to_id[fast_new_block_array[x, y, z]]
                    new_block_id_array[x, y, z] = new_block_id

    @staticmethod
    @numba.guvectorize("void(int32, int32[:], int32, int32[:])", "(), (m), () -> ()", target="cuda" if USE_CUDA else "parallel")
    def map_new_blocks_vector(fast_new_block_array, index_to_id, old_block_id_array, new_block_id_array):
        if fast_new_block_array == -1:
            new_block_id_array[:] = old_block_id_array
        else:
            new_block_id = index_to_id[fast_new_block_array]
            new_block_id_array[:] = new_block_id

    def get_block(self, x, y, z):
        if self.block_in_render_distance(x, y, z):
            rx = x - BLOCK_RENDER_DISTANCE - self.last_player_block_pos[0]
            ry = y - BLOCK_RENDER_DISTANCE - self.last_player_block_pos[1]
            rz = z - BLOCK_RENDER_DISTANCE - self.last_player_block_pos[2]
            if (x, y, z) in self.blocks:
                return self.blocks[(x, y, z)]
            else:
                if self.block_id_array[rx, ry, rz] == -1:
                    return self.AIR_VIEW
                else:
                    b = block.BlockView(self.block_id_to_block[self.block_id_array[rx, ry, rz]])
                    self.blocks[(x, y, z)] = b
                    return b
        else:
            return self.AIR_VIEW

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


#@numba.guvectorize(["int32(int32[:], int32[:, :])"], "(n), (m,p) -> ()", target="cuda")
@numba.guvectorize(["void(int32[:], int32[:,:], int32[:])"], "(n), (m,p) -> ()", target="cuda")
def calculate_ray(ray, blocks, out):
    current_block = 0

    x = BLOCK_RENDER_DISTANCE + 1
    y = BLOCK_RENDER_DISTANCE + 1
    z = BLOCK_RENDER_DISTANCE + 1
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
        elif next_direction == 5:
            y -= 1
        else:
            break

        current_block = blocks[current_block, next_direction]
        #if new_blocks[x, y, z] is None:
    out[:] = current_block


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

