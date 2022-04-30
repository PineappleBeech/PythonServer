import chunk
import math
import time

from line_profiler_pycharm import profile

import nbt
from network.packets import ClientBoundPlayPacket
import buffer


class BlockChange(ClientBoundPlayPacket):
    packet_id = 0x0C

    def __init__(self, x, y, z, block_id):
        self.x = x
        self.y = y
        self.z = z
        self.block_id = block_id

    def write(self, buf):
        buf.write_position((self.x, self.y, self.z))
        buf.write_varint(self.block_id)


class PluginMessage(ClientBoundPlayPacket):
    packet_id = 0x18

    def __init__(self, channel, data):
        self.channel = channel
        self.data = data

    def write(self, buf):
        buf.write_string(self.channel)
        buf.write_varint(len(self.data))
        buf.write(self.data)


class KeepAlive(ClientBoundPlayPacket):
    packet_id = 0x21

    def __init__(self, id):
        self.id = id

    def write(self, buf):
        buf.write_long(self.id)


class ChunkData(ClientBoundPlayPacket):
    packet_id = 0x22

    def __init__(self, chunk_x, chunk_z, chunk):
        self.chunk_x = chunk_x
        self.chunk_z = chunk_z
        self.chunk = chunk

    @profile
    def write(self, buf):
        buf.write_int(self.chunk_x)
        buf.write_int(self.chunk_z)
        buf.write_nbt(nbt.NBT_Compound({
            "MOTION_BLOCKING": nbt.NBT_Long_Array(buffer.PackedDataArray(
                self.chunk.heightmap,
                math.ceil(math.log2(self.chunk.world_view.world.height+1))
            ).get_long_array()),
        }))

        data = buffer.Buffer()
        for i in range(self.chunk.section_count):
            if self.chunk.in_render_distance():
                #s = time.time()
                blocks = []
                nonair_count = 0
                for y in range(i*16 + self.chunk.world_view.world.min_y, i*16 + self.chunk.world_view.world.min_y + 16):
                    for z in range(16):
                        for x in range(16):
                            coord = (x, y, z)
                            block_id = self.chunk.get_block_id(*coord)
                            blocks.append(block_id)
                            if blocks[-1] != 0:
                                nonair_count += 1

                data.write_short(nonair_count)
                block_set = set(blocks)
                bit_count = (len(block_set)-1).bit_length()
                data.write_byte(bit_count)

                #print("time taken to write block set:", time.time() - s)

                if bit_count == 0:
                    data.write_varint(blocks[0])
                    data.write_varint(0)

                else:
                    if bit_count < 4:
                        bit_count = 4

                    if bit_count <= 8:
                        blocks_indexed = list(block_set)
                        block_palette = {blocks_indexed[i]: i for i in range(len(blocks_indexed))}
                        data.write_varint(len(blocks_indexed))
                        for block in blocks_indexed:
                            data.write_varint(block)

                        encoded_blocks = list([block_palette[block] for block in blocks])

                        array = buffer.PackedDataArray(encoded_blocks, bit_count)
                        array.write(data)

            else:
                data.write_short(0)
                data.write_byte(0)
                data.write_varint(0)
                data.write_varint(0)

            data.write_byte(0)
            data.write_varint(0)
            data.write_varint(0)

        buf.write_varint(len(data))
        buf.write(data.getvalue())

        # block entities
        buf.write_varint(0)

        # trust edges
        buf.write_bool(True)

        # sky light mask
        buffer.PackedDataArray([0] * (self.chunk.section_count + 2), 1).write(buf)
        # block light mask
        buffer.PackedDataArray([1] * (self.chunk.section_count + 2), 1).write(buf)
        # empty sky light mask
        buffer.PackedDataArray([1] * (self.chunk.section_count + 2), 1).write(buf)
        # empty block light mask
        buffer.PackedDataArray([0] * (self.chunk.section_count + 2), 1).write(buf)

        buf.write_varint(0)
        buf.write_varint(self.chunk.section_count + 2)

        for i in range(self.chunk.section_count + 2):
            buf.write_varint(2048)
            buf.write(b"\xff" * 2048)







class JoinGame(ClientBoundPlayPacket):
    packet_id = 0x26

    def __init__(self,
                 entity_id,
                 hardcore,
                 gamemode,
                 dimension_names,
                 dimension_registry,
                 dimension,
                 dimension_name,
                 hashed_seed,
                 max_players,
                 view_distance,
                 simulation_distance,
                 reduced_debug_info,
                 respawn_screen,
                 debug,
                 flat):
        self.entity_id = entity_id
        self.hardcore = hardcore
        self.gamemode = gamemode
        self.dimension_names = dimension_names
        self.dimension_registry = dimension_registry
        self.dimension = dimension
        self.dimension_name = dimension_name
        self.hashed_seed = hashed_seed
        self.max_players = max_players
        self.view_distance = view_distance
        self.simulation_distance = simulation_distance
        self.reduced_debug_info = reduced_debug_info
        self.respawn_screen = respawn_screen
        self.debug = debug
        self.flat = flat

    def write(self, buf):
        buf.write_int(self.entity_id)
        buf.write_bool(self.hardcore)
        buf.write_ubyte(self.gamemode)
        buf.write_byte(-1)
        buf.write_varint(len(self.dimension_names))
        for dimension_name in self.dimension_names:
            buf.write_string(dimension_name)
        #buf.write(b"\x0a\x00\x02\x68\x68\x08\x00\x02\x67\x67\x00\x03\x66\x66\x66\x00")
        buf.write_nbt(self.dimension_registry)
        buf.write_nbt(self.dimension)
        buf.write_string(self.dimension_name)
        buf.write_long(self.hashed_seed)
        buf.write_varint(self.max_players)
        buf.write_varint(self.view_distance)
        buf.write_varint(self.simulation_distance)
        buf.write_bool(self.reduced_debug_info)
        buf.write_bool(self.respawn_screen)
        buf.write_bool(self.debug)
        buf.write_bool(self.flat)


class PlayerPositionAndLook(ClientBoundPlayPacket):
    packet_id = 0x38

    def __init__(self, x, y, z, yaw, pitch, teleport_id, dismount_vehicle=False, x_rel=False, y_rel=False, z_rel=False, yaw_rel=False, pitch_rel=False):
        self.x = x
        self.y = y
        self.z = z
        self.yaw = yaw
        self.pitch = pitch
        self.teleport_id = teleport_id
        self.dismount_vehicle = dismount_vehicle
        self.x_rel = x_rel
        self.y_rel = y_rel
        self.z_rel = z_rel
        self.yaw_rel = yaw_rel
        self.pitch_rel = pitch_rel

    def write(self, buf):
        buf.write_double(self.x)
        buf.write_double(self.y)
        buf.write_double(self.z)
        buf.write_float(self.yaw)
        buf.write_float(self.pitch)
        flags = 0
        if self.x_rel:
            flags |= 0x01
        if self.y_rel:
            flags |= 0x02
        if self.z_rel:
            flags |= 0x04
        if self.yaw_rel:
            flags |= 0x08
        if self.pitch_rel:
            flags |= 0x10

        buf.write_byte(flags)
        buf.write_varint(self.teleport_id)
        buf.write_bool(self.dismount_vehicle)


class UpdateViewPosition(ClientBoundPlayPacket):
    packet_id = 0x49

    def __init__(self, x, z):
        self.x = x
        self.z = z

    def write(self, buf):
        buf.write_varint(self.x)
        buf.write_varint(self.z)


class SpawnPosition(ClientBoundPlayPacket):
    packet_id = 0x4b

    def __init__(self, x, y, z, angle):
        self.x = x
        self.y = y
        self.z = z
        self.angle = angle

    def write(self, buf):
        buf.write_position((self.x, self.y, self.z))
        buf.write_float(self.angle)
