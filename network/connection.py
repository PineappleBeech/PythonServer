import io
import os
import random
import socket
import threading
import time
import uuid

import cryptography
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher
from cryptography.hazmat.primitives.ciphers import algorithms
from cryptography.hazmat.primitives.ciphers import modes
import requests
import hashlib

import buffer
import network.packet_handler as packet_handler
import network.clientbound.status as status
import network.clientbound.login as login
import network.clientbound.play as play
from entity.player import Player
from network import playpackethandler
import nbt
from world import world

class ServerListener:
    def __init__(self, server):
        self.connections = []
        self.server = server

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(("0.0.0.0", 25565))
        self.sock.listen(3)

        self.accept_thread = threading.Thread(target=self.accept_loop, daemon=True)
        self.accept_thread.start()

    def accept_loop(self):
        while True:
            self.accept()

    def accept(self):
        conn, addr = self.sock.accept()
        self.connections.append(Connection(conn, addr, self.server))

    def tick(self):
        for connection in self.connections:
            connection.tick()



class Connection:
    def __init__(self, sock, addr, server):
        self.server = server
        self.sock: socket.socket = sock
        self.sock.setblocking(False)
        self.addr = addr
        self.buffer = buffer.Buffer()
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.compress = False

        self.encrypt = False
        self.encryption_cipher = None
        self.encryptor = None
        self.decryptor = None

        self.last_keep_alive = None
        self.current_keep_alive_id = None

        self.handler = packet_handler.PacketHandler(self)
        self.play_packet_handler = None

        self.state = 0
        self.is_open = True

        self.thread.start()

    def run(self):
        self.next_packet_length = None

        while self.is_open:
            try:
                data = self.sock.recv(1024)
            except BlockingIOError:
                pass
            except ConnectionAbortedError:
                self.dissconnect()
                return
            except OSError:
                self.dissconnect()
                return
            else:
                if self.encrypt:
                    data = self.decryptor.update(data)
                self.buffer.write(data)

            if self.buffer.getvalue() == b'':
                continue

            if self.next_packet_length is None:
                self.next_packet_length = self.buffer.read_varint()

            if len(self.buffer.getvalue()) >= self.next_packet_length:
                packet = buffer.from_bytes(self.buffer.read(self.next_packet_length))
                self.next_packet_length = None
                self.handler.handle(packet)

    def tick(self):
        if self.last_keep_alive is not None:
            if time.time() - self.last_keep_alive > 15:
                if self.current_keep_alive_id is not None:
                    print("Keep alive timeout")
                    self.dissconnect()
                    return
                else:
                    self.send_keep_alive()


    def send_packet(self, packet):
        if type(packet) not in [play.ChunkData, play.KeepAlive, play.BlockChange]:
            print("Sending packet:", packet)
        data = buffer.Buffer()
        data.write_varint(packet.packet_id)
        packet.write(data)
        if self.compress:
            pass
        send_buffer = buffer.Buffer()
        send_buffer.write_varint(len(data.getvalue()))
        send_buffer.write(data.getvalue())
        if self.encrypt:
            self.sock.send(self.encryptor.update(send_buffer.getvalue()))
        else:
            self.sock.send(send_buffer.getvalue())


    def dissconnect(self):
        self.is_open = False
        self.sock.close()
        self.server.listener.connections.remove(self)


    def send_keep_alive(self):
        self.current_keep_alive_id = random.randint(0, 0xFFFFFFFF)
        self.send_packet(play.KeepAlive(self.current_keep_alive_id))
        self.last_keep_alive = time.time()


    def on_handshake(self, packet):
        self.protocol_version = packet.protocol_version
        self.state = packet.next_state

    def on_server_status_request(self, packet):
        payload = {
            "version": {
                "name": "1.18.2",
                "protocol": 758
            },
            "players": {
                "max": 100,
                "online": 0,
                "sample": []
            },
            "description": {
                "text": "A Minecraft Server"
            },
            "favicon": ""
        }
        self.send_packet(status.Response(payload))

    def on_server_status_ping(self, packet):
        self.send_packet(status.Pong(packet.time))
        self.dissconnect()

    def on_login_start(self, packet):
        self.player = Player(self, packet.username)

        self.private_key = cryptography.hazmat.primitives.asymmetric.rsa.generate_private_key(key_size=2048,
                                                                                              public_exponent=65537)

        self.public_key = self.private_key.public_key()
        self.verify_token = os.urandom(4)

        self.send_packet(login.EncryptionRequest("",
                                                 self.public_key.public_bytes(encoding=serialization.Encoding.DER,
                                                            format=serialization.PublicFormat.SubjectPublicKeyInfo),
                                                 self.verify_token))

    def on_login_encryption_response(self, packet):
        self.shared_secret = self.private_key.decrypt(bytes(packet.shared_secret),
                                                      cryptography.hazmat.primitives.asymmetric.padding.PKCS1v15())

        assert self.verify_token == self.private_key.decrypt(bytes(packet.verify_token),
                                                             cryptography.hazmat.primitives.asymmetric.padding.PKCS1v15())

        hash = hashlib.sha1()
        hash.update("".encode("utf-8"))
        hash.update(self.shared_secret)
        hash.update(self.public_key.public_bytes(encoding=serialization.Encoding.DER,
                                                 format=serialization.PublicFormat.SubjectPublicKeyInfo))

        hash_number = format(int.from_bytes(hash.digest(), byteorder="big", signed=True), "x")


        request_params = {"username": self.player.username,
                          "serverId": hash_number}
        response = requests.get("https://sessionserver.mojang.com/session/minecraft/hasJoined", params=request_params).json()

        self.player.uuid = uuid.UUID(response["id"])
        assert response["name"] == self.player.username

        self.encrypt = True
        self.encryption_cipher = cryptography.hazmat.primitives.ciphers.Cipher(algorithm=algorithms.AES(self.shared_secret),
                                                                               mode=modes.CFB8(self.shared_secret))

        self.encryptor = self.encryption_cipher.encryptor()
        self.decryptor = self.encryption_cipher.decryptor()


        self.send_packet(login.LoginSuccess(self.player.uuid, self.player.username))
        self.state = 3
        self.play_packet_handler = playpackethandler.PlayPacketHandler(self, self.server, self.player)
        self.player.thread.add_task(self.player.spawn_player, self.server.world)

        #self.send_play_packets()

    def send_play_packets(self):
        self.send_keep_alive()

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
        self.send_packet(play.JoinGame(self.player.id,
                                       self.server.world.hardcore,
                                       self.player.gamemode,
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
        self.send_packet(play.PluginMessage("minecraft:brand", bytes("Peter"*17, "utf-8")))

        self.send_packet(play.SpawnPosition(0, 0, 0, 0))
        self.send_packet(play.PlayerPositionAndLook(0, 0, 0, 0, 0, 0))
