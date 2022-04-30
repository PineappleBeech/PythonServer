from network.packets import ServerBoundHandshakePacket

class Handshake(ServerBoundHandshakePacket):
    packet_id = 0x00

    def __init__(self, packet_data):
        self.protocol_version = packet_data.read_varint()
        self.server_address = packet_data.read_string()
        self.server_port = packet_data.read_ushort()
        self.next_state = packet_data.read_varint()


    def handle(self, conn):
        conn.on_handshake(self)
