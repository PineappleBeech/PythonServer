from network.packets import ServerBoundLoginPacket

class LoginStart(ServerBoundLoginPacket):
    packet_id = 0x00

    def __init__(self, data):
        self.username = data.read_string()

    def handle(self, conn):
        conn.on_login_start(self)


class EncryptionResponse(ServerBoundLoginPacket):
    packet_id = 0x01

    def __init__(self, data):
        self.shared_secret = data.read(data.read_varint())
        self.verify_token = data.read(data.read_varint())

    def handle(self, conn):
        conn.on_login_encryption_response(self)
