from network.packets import ServerBoundStatusPacket

class Request(ServerBoundStatusPacket):
    packet_id = 0x00
    def __init__(self, packet_data):
        pass

    def handle(self, conn):
        conn.on_server_status_request(self)


class Ping(ServerBoundStatusPacket):
    packet_id = 0x01
    def __init__(self, packet_data):
        self.time = packet_data.read_long()

    def handle(self, conn):
        conn.on_server_status_ping(self)
