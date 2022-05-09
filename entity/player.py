import math
import time

from line_profiler_pycharm import profile

import entity.entity as entity
from util import util
import world.world as world
import nbt
from network.clientbound import play
from structure import structure
from util.raycasting import path, path_to_list, follow_directions
from util.util import Direction


class Player(entity.LivingEntity):
    def __init__(self, conn, name):
        self.username = name
        self.conn = conn
        self.gamemode = 0
        self.thread = util.TaskExecutor()
        self.is_spawned = False

    def tick(self):
        if self.is_spawned:
            super().tick()
            if time.time() - self.last_world_view_update > 0.2:
                self.thread.add_task(self.world_view.update_view)
                self.last_world_view_update = time.time()

    @property
    def position(self):
        return (self.client_position[0] % 1, self.client_position[1] % 1, self.client_position[2] % 1)

    @position.setter
    def position(self, value):
        pass

    def set_client_position(self, x, y, z):
        diff = (x - self.client_position[0], y - self.client_position[1], z - self.client_position[2])
        self.move(diff)

    def move(self, x, y, z):
        new_position = (self.client_position[0] + x, self.client_position[1] + y, self.client_position[2] + z)
        self.block = follow_directions(self.block, path(self.client_position, new_position))
        old_position = self.client_position
        self.client_position = new_position

        if (old_position[0] // 16, old_position[2] // 16) != (new_position[0] // 16, new_position[2] // 16):
            self.conn.send_packet(play.UpdateViewPosition(x=math.floor(new_position[0]//16), z=math.floor(new_position[2]//16)))
            self.world_view.change_chunk(math.floor(new_position[0]//16), math.floor(new_position[2]//16))

    def move_to(self, x, y, z):
        self.move(x - self.client_position[0], y - self.client_position[1], z - self.client_position[2])

    def spawn_player(self, *args, **kwargs):
        self.conn.send_keep_alive()

        super().__init__(*args, **kwargs)
        spawn_house = structure.SimpleStructure("less_simple_portal_room", self.world)
        self.block = spawn_house.blocks[spawn_house.spawn_pos]

        self.client_position = (0.5, 100.5, 0.5)

        dimension_registry = nbt.NBT_Compound({
            "minecraft:dimension_type": nbt.NBT_Compound({
                "type": nbt.NBT_String("minecraft:dimension_type"),
                "value": nbt.NBT_List([
                    nbt.NBT_Compound({
                        "name": nbt.NBT_String("minecraft:overworld"),
                        "id": nbt.NBT_Int(0),
                        "element": world.DimensionType().to_nbt()
                    })
                ])
            }),
            "minecraft:worldgen/biome": nbt.NBT_Compound({
                "type": nbt.NBT_String("minecraft:worldgen/biome"),
                "value": nbt.NBT_List([
                    nbt.NBT_Compound({
                        "name": nbt.NBT_String("minecraft:plains"),
                        "id": nbt.NBT_Int(0),
                        "element": world.Biome().to_nbt()
                    })
                ])
            })
        })
        self.conn.send_packet(play.JoinGame(self.id,
                                       self.world.hardcore,
                                       self.gamemode,
                                       ["minecraft:overworld"],
                                       dimension_registry,
                                       world.DimensionType().to_nbt(),
                                       "minecraft:overworld",
                                       12345,
                                       100,
                                       8,
                                       8,
                                       False,
                                       True,
                                       False,
                                       False))
        self.conn.send_packet(play.PluginMessage("minecraft:brand", bytes("Peter"*17, "utf-8")))

        self.world_view = world.WorldView(self.world, self)
        self.last_world_view_update = time.time()

        self.conn.send_packet(play.SpawnPosition(0, 0, 0, 0))
        self.conn.send_packet(play.PlayerPositionAndLook(*self.client_position, *self.rotation, 0))

        self.world.add_player(self)
        self.is_spawned = True

class PlayerOptions:
    def __init__(self, locale, view_distance, chat_mode, chat_colors, skin_flags, main_hand, text_filtering, server_listings):
        self.locale = locale
        self.view_distance = view_distance
        self.chat_mode = chat_mode
        self.chat_colors = chat_colors
        self.skin_flags = skin_flags
        self.main_hand = main_hand
        self.text_filtering = text_filtering
        self.server_listings = server_listings