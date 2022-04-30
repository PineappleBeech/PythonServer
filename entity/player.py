from line_profiler_pycharm import profile

import entity.entity as entity
from util import util
import world.world as world
import nbt
from network.clientbound import play
from structure import structure
from util.raycasting import path, path_to_list, follow_directions


class Player(entity.LivingEntity):
    def __init__(self, conn, name):
        self.username = name
        self.conn = conn
        self.gamemode = 0
        self.thread = util.TaskExecutor()

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
        self.block = follow_directions(self.block, path_to_list(path(self.client_position, new_position)))
        if (self.client_position[0] // 16, self.client_position[2] // 16) != (new_position[0] // 16, new_position[2] // 16):
            self.conn.send_packet(play.UpdateViewPosition(x=new_position[0], z=new_position[2]))
        self.client_position = new_position

    @profile
    def spawn_player(self, *args, **kwargs):
        self.conn.send_keep_alive()

        super().__init__(*args, **kwargs)
        spawn_house = structure.SimpleStructure("basic_room")
        self.block = spawn_house.blocks[(5, 2, 5)]

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

        self.conn.send_packet(play.SpawnPosition(0, 0, 0, 0))
        self.conn.send_packet(play.PlayerPositionAndLook(*self.client_position, *self.rotation, 0))

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