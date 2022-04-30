import zlib

import buffer

import network.packets
import network.serverbound.handshake
import network.serverbound.status
import network.serverbound.login
import network.serverbound.play

class PacketHandler:
    def __init__(self, conn):
        self.conn = conn
        self.compressed = False

    def handle(self, packet):
        if self.compressed:
            packet_length = packet.read_varint()
            packet = buffer.from_bytes(zlib.decompress(packet.read()))

            if len(packet) != packet_length:
                raise Exception("Packet length mismatch")

        packet_id = packet.read_varint()

        try:
            packet_type = network.packets.SERVERBOUND_PACKETS[self.conn.state][packet_id]
        except KeyError:
            print("Unknown packet:", format(packet_id, '#04x'))

        else:
            if packet_type not in [network.serverbound.play.PlayerPosition,
                                   network.serverbound.play.PlayerPositionAndRotation,
                                   network.serverbound.play.PlayerRotation]:
                print("Receiving Packet:", packet_type)

            packet_type(packet).handle(self.conn)






CONNECTION_STATES = {0: "Handshake",
                     1: "Status",
                     2: "Login",
                     3: "Play"}
