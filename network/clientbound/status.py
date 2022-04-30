from network.packets import ClientBoundStatusPacket
import json

class Response(ClientBoundStatusPacket):
    packet_id = 0x00

    def __init__(self, server_data):
        self.server_data = server_data

    def write(self, buf):
        buf.write_string(json.dumps(self.server_data))


class Pong(ClientBoundStatusPacket):
    packet_id = 0x01

    def __init__(self, time):
        self.time = time

    def write(self, buf):
        buf.write_long(self.time)