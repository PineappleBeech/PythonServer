from network.packets import ClientBoundLoginPacket
import json


class EncryptionRequest(ClientBoundLoginPacket):
    packet_id = 0x01

    def __init__(self, server_id, public_key, verify_token):
        self.server_id = server_id
        self.public_key = public_key
        self.verify_token = verify_token

    def write(self, buf):
        buf.write_string(self.server_id)
        buf.write_varint(len(self.public_key))
        buf.write(self.public_key)
        buf.write_varint(len(self.verify_token))
        buf.write(self.verify_token)


class LoginSuccess(ClientBoundLoginPacket):
    packet_id = 0x02

    def __init__(self, uuid, username):
        self.uuid = uuid
        self.username = username

    def write(self, buf):
        buf.write_uuid(self.uuid)
        buf.write_string(self.username)
