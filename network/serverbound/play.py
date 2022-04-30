from network.packets import ServerBoundPlayPacket


class TeleportConfirm(ServerBoundPlayPacket):
    packet_id = 0x00

    def __init__(self, data):
        self.teleport_id = data.read_varint()


    def handle(self, conn):
        pass


class ClientSettings(ServerBoundPlayPacket):
    packet_id = 0x05

    def __init__(self, data):
        self.locale = data.read_string()
        self.view_distance = data.read_ubyte()
        self.chat_mode = data.read_varint()
        self.chat_colors = data.read_bool()
        self.skin_flags = data.read_ubyte()
        self.main_hand = data.read_varint()
        self.text_filtering = data.read_bool()
        self.server_listing = data.read_bool()


    def handle(self, conn):
        conn.play_packet_handler.on_client_settings(self)


class PluginMessage(ServerBoundPlayPacket):
    packet_id = 0x0A

    def __init__(self, data):
        self.channel = data.read_string()
        self.data_length = data.read_varint()
        self.data = data.read(self.data_length)

    def handle(self, conn):
        conn.play_packet_handler.on_plugin_message(self)


class KeepAlive(ServerBoundPlayPacket):
    packet_id = 0x0F

    def __init__(self, data):
        self.id = data.read_long()

    def handle(self, conn):
        conn.play_packet_handler.on_keep_alive(self)


class PlayerPosition(ServerBoundPlayPacket):
    packet_id = 0x11

    def __init__(self, data):
        self.x = data.read_double()
        self.y = data.read_double()
        self.z = data.read_double()
        self.on_ground = data.read_bool()

    def handle(self, conn):
        conn.play_packet_handler.on_player_position(self)


class PlayerPositionAndRotation(ServerBoundPlayPacket):
    packet_id = 0x12

    def __init__(self, data):
        self.x = data.read_double()
        self.y = data.read_double()
        self.z = data.read_double()
        self.yaw = data.read_float()
        self.pitch = data.read_float()
        self.on_ground = data.read_bool()

    def handle(self, conn):
        conn.play_packet_handler.on_player_position_and_rotation(self)


class PlayerRotation(ServerBoundPlayPacket):
    packet_id = 0x13

    def __init__(self, data):
        self.yaw = data.read_float()
        self.pitch = data.read_float()
        self.on_ground = data.read_bool()

    def handle(self, conn):
        conn.play_packet_handler.on_player_rotation(self)
