

SERVERBOUND_PACKETS = {
    0: {},
    1: {},
    2: {},
    3: {}
}

CLIENTBOUND_PACKETS = {
    1: {},
    2: {},
    3: {}
}


class Packet:
    pass


class ServerBoundPacket(Packet):
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        try:
            SERVERBOUND_PACKETS[cls.state][cls.packet_id] = cls
        except NameError:
            pass
        except AttributeError:
            pass


class ServerBoundHandshakePacket(ServerBoundPacket):
    state = 0x00
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)


class ServerBoundStatusPacket(ServerBoundPacket):
    state = 0x01
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)


class ServerBoundLoginPacket(ServerBoundPacket):
    state = 0x02
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)


class ServerBoundPlayPacket(ServerBoundPacket):
    state = 0x03
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)


class ClientBoundPacket(Packet):
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        try:
            CLIENTBOUND_PACKETS[cls.state][cls.packet_id] = cls
        except AttributeError:
            pass
        except KeyError:
            pass


class ClientBoundHandshakePacket(ClientBoundPacket):
    state = 0x00


class ClientBoundStatusPacket(ClientBoundPacket):
    state = 0x01


class ClientBoundLoginPacket(ClientBoundPacket):
    state = 0x02


class ClientBoundPlayPacket(ClientBoundPacket):
    state = 0x03


