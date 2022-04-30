from entity import player

class PlayPacketHandler:
    def __init__(self, conn, server, player):
        self.conn = conn
        self.server = server
        self.player = player

    def on_teleport_confirm(self, packet):
        self.player.last_teleport_id = packet.teleport_id

    def on_client_settings(self, packet):
        self.player.settings = player.PlayerOptions(
            packet.locale,
            packet.view_distance,
            packet.chat_mode,
            packet.chat_colors,
            packet.skin_flags,
            packet.main_hand,
            packet.text_filtering,
            packet.server_listing
        )

    def on_plugin_message(self, packet):
        if packet.channel == "minecraft:brand":
            self.player.brand = packet.data.decode("utf-8")

    def on_keep_alive(self, packet):
        print("Received keep alive")
        self.conn.current_keep_alive_id = None

    def on_player_position(self, packet):
        self.player.position = (packet.x, packet.y, packet.z)
        self.player.on_ground = packet.on_ground

    def on_player_position_and_rotation(self, packet):
        self.player.position = (packet.x, packet.y, packet.z)
        self.player.rotation = (packet.yaw, packet.pitch)
        self.player.on_ground = packet.on_ground

    def on_player_rotation(self, packet):
        self.player.rotation = (packet.yaw, packet.pitch)
        self.player.on_ground = packet.on_ground