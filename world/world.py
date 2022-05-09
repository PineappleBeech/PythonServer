import math
import time

import numba
import numpy
from line_profiler_pycharm import profile
import numpy as np
from numba import cuda

import nbt
from block import block
from network.clientbound import play
from util.util import shift_and_pad, integers_between_numba
from util.constants import BLOCK_RENDER_DISTANCE, CHUNK_RENDER_DISTANCE
from util import raycasting

USE_CUDA = True

host_array_of_indexes = np.array([[[[x, y, z] for x in range(BLOCK_RENDER_DISTANCE * 2 + 1)]
                                   for y in range(BLOCK_RENDER_DISTANCE * 2 + 1)]
                                  for z in range(BLOCK_RENDER_DISTANCE * 2 + 1)], dtype=np.int32)

if USE_CUDA:
    device_array_of_indexes = numba.cuda.to_device(host_array_of_indexes)


class World:
    def __init__(self):
        self.hardcore = False
        self.players = []
        self.entities = []
        self.dimension_type = DimensionType()
        self.blocks = {}
        self.block_neighbors_by_index = np.zeros((len(self.blocks), 6), dtype=np.int32)
        self.block_index_to_id = np.zeros(len(self.blocks), dtype=np.int32)
        self.block_neighbors_by_index_needs_update = False

    @property
    def min_y(self):
        return self.dimension_type.min_y

    @property
    def height(self):
        return self.dimension_type.height

    def tick(self):
        for player in self.players:
            player.tick()

    def add_player(self, player):
        self.players.append(player)

    def remove_player(self, player):
        self.players.remove(player)

    def add_block(self, block):
        self.blocks[block.id] = block
        self.block_neighbors_by_index_needs_update = True

    def remove_block(self, block):
        del self.blocks[block.id]
        self.block_neighbors_by_index_needs_update = True

    def get_block_neighbors_by_index(self):
        if self.block_neighbors_by_index_needs_update:
            print("Updating block neighbors by index")
            self.block_neighbors_by_index_needs_update = False
            self.block_neighbors_by_index = np.zeros((len(self.blocks), 6), dtype=np.int32)
            self.block_index_to_id = np.array(list(self.blocks.keys()), dtype=np.int32)
            block_id_to_index = {block_id: index for index, block_id in enumerate(self.block_index_to_id)}
            for i, b in enumerate(self.blocks.values()):
                for direction in range(6):
                    try:
                        next_block = b.get_block(direction)
                    except block.NoBlock:
                        self.block_neighbors_by_index[i, direction] = -1
                    else:
                        self.block_neighbors_by_index[i, direction] = block_id_to_index[next_block.id]

        return self.block_neighbors_by_index


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
        print("Starting to load chunks...")
        self.load_chunks()


    @profile
    def update_view(self):
        s = time.time()

        new_player_position = (math.floor(self.player.client_position[0]), math.floor(self.player.client_position[1]), math.floor(self.player.client_position[2]))
        block_pos_diff = (math.floor(new_player_position[0]) - self.last_player_block_pos[0],
                          math.floor(new_player_position[1]) - self.last_player_block_pos[1],
                          math.floor(new_player_position[2]) - self.last_player_block_pos[2])
        start_block = block.BlockView(self.player.block)

        #block_map = {}
        #WorldView.map_blocks(block_map, start_block.block)

        block_map = self.world.blocks

        #fast_block_map = numba.typed.Dict.empty(key_type=numba.types.int32, value_type=numba.types.int32)
        #for key, value in enumerate(block_map.keys()):
        #    fast_block_map[key] = value
        #fast_block_map = np.array(list(block_map.keys()), dtype=np.int32)
        block_neighbor_ids = self.world.get_block_neighbors_by_index()
        fast_block_map = self.world.block_index_to_id
        #WorldView.map_block_ids(block_map, block_neighbor_ids)

        start_block_id = np.where(fast_block_map == start_block.block.id)[0][0]

        #fast_new_blocks = np.zeros((BLOCK_RENDER_DISTANCE * 2 + 1, BLOCK_RENDER_DISTANCE * 2 + 1, BLOCK_RENDER_DISTANCE * 2 + 1), dtype=np.int32)

        if time.time() - s > 0.1:
            print("Mapping blocks took:", time.time() - s)
        s = time.time()

        if USE_CUDA:
            device_new_blocks = WorldView.calculate_ray(raycasting.device_array, block_neighbor_ids, start_block_id)
            fast_new_blocks = device_new_blocks.copy_to_host()
        else:
            fast_new_blocks = WorldView.calculate_ray(raycasting.host_array, block_neighbor_ids, start_block_id)

        if time.time() - s > 0.1:
            print("Calculating ray took:", time.time() - s)
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
            if chunk_pos in chunks:
                sections = {}

                for block_pos in chunks[chunk_pos]:
                    section_pos = int((block_pos[1] - self.world.min_y) // 16)
                    if section_pos not in sections:
                        sections[section_pos] = []
                    sections[section_pos].append(block_pos)

                for section_pos in sections:
                    # why would i update heightmaps if they aren't sent to the client?
                    # heightmaps might be useful
                    #self.player.conn.send_packet(play.BlockChange(block_pos[0], block_pos[1], block_pos[2], self.get_block(*block_pos).get_id()))
                    block_list = [(*i, self.get_block(*i).get_id()) for i in sections[section_pos]]
                    self.player.conn.send_packet(play.MultiBlockChange(chunk_pos[0], chunk_pos[1], section_pos, block_list))

        if time.time() - s > 0.1:
            print("Updating chunks took:", time.time() - s)
        s = time.time()

        return
        #raise Exception

    @staticmethod
    @numba.guvectorize(["void(int32[:], int32[:,:], int32, int32[:])"], "(n), (m,p), () -> ()", target="cuda" if USE_CUDA else "parallel")
    def calculate_ray(ray, blocks, start_id, out):
        current_block = start_id

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
        new_blocks = {current_block.id: current_block}
        new_new_blocks = {}
        processed_ids = set()

        loop_starting = True

        while len(processed_ids) != len(blocks) or loop_starting:
            loop_starting = False
            for b in new_blocks.values():
                if b.id not in processed_ids:
                    for direction in range(6):
                        try:
                            next_block = b.get_block(direction)
                        except block.NoBlock:
                            continue
                        else:
                            new_new_blocks[next_block.id] = next_block

                    processed_ids.add(b.id)

            blocks.update(new_new_blocks)
            new_blocks = new_new_blocks
            new_new_blocks = {}




        '''
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
        '''

    @staticmethod
    @profile
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
            rx = x + BLOCK_RENDER_DISTANCE - self.last_player_block_pos[0]
            ry = y + BLOCK_RENDER_DISTANCE - self.last_player_block_pos[1]
            rz = z + BLOCK_RENDER_DISTANCE - self.last_player_block_pos[2]
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
        mid_chunk_pos = (math.floor(self.player.client_position[0] // 16), math.floor(self.player.client_position[2] // 16))
        distance = CHUNK_RENDER_DISTANCE
        for z in range(-distance, distance + 1):
            for x in range(-distance, distance + 1):
                self.chunks[(mid_chunk_pos[0] + x, mid_chunk_pos[1] + z)] = ChunkView(self, mid_chunk_pos[0] + x, mid_chunk_pos[1] + z)

    def change_chunk(self, x, z):
        new_chunks = {}
        for xx in range(-CHUNK_RENDER_DISTANCE, CHUNK_RENDER_DISTANCE + 1):
            for zz in range(-CHUNK_RENDER_DISTANCE, CHUNK_RENDER_DISTANCE + 1):
                if (x + xx, z + zz) in self.chunks:
                    new_chunks[(x + xx, z + zz)] = self.chunks[(x + xx, z + zz)]
                else:
                    new_chunks[(x + xx, z + zz)] = ChunkView(self, x + xx, z + zz)
        old_chunks = self.chunks
        self.chunks = new_chunks
        for chunk in old_chunks.keys():
            if chunk not in self.chunks:
                self.player.conn.send_packet(play.UnloadChunk(chunk[0], chunk[1]))


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
                    if self.get_block(x, yy, z).block.name != "minecraft:air":
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

