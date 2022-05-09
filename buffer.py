import io
import struct
import uuid

from line_profiler_pycharm import profile

import nbt

continue_bit = 0x80
segment_bit = 0x7F

class Buffer:
    def __init__(self, buffer=None):
        if buffer is None:
            self.buffer: bytearray = bytearray()
        else:
            self.buffer: bytearray = bytearray(buffer.read())
            buffer.close()

        self.read_index = 0

    def write(self, data):
        self.buffer.extend(bytes(data))

    def read(self, length=-1):
        if length == -1:
            return self.buffer[self.read_index:]
        else:
            while len(self.buffer) - self.read_index < length:
                pass
            data = self.buffer[self.read_index:self.read_index + length]
            self.read_index += length
            return data

        if self.read_index > 1024:
            self.buffer = self.buffer[self.read_index:]
            self.read_index = 0

    def getvalue(self):
        return self.buffer[self.read_index:]

    def seek(self, offset, whence=0):
        if offset == 0:
            pass
        else:
            raise NotImplementedError()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return
        self.buffer.close()

    def __len__(self):
        return len(self.getvalue())

    def write_int(self, integer):
        self.write(struct.pack("!i", integer))

    def read_int(self):
        return struct.unpack("!i", self.read(4))[0]

    def write_uint(self, integer):
        self.write(struct.pack("!I", integer))

    def read_uint(self):
        return struct.unpack("!I", self.read(4))[0]

    def write_bool(self, boolean):
        self.write(struct.pack("!?", boolean))

    def read_bool(self):
        return struct.unpack("!?", self.read(1))[0]

    def write_byte(self, byte):
        self.write(struct.pack("!b", byte))

    def read_byte(self):
        return struct.unpack("!b", self.read(1))[0]

    def write_ubyte(self, byte):
        self.write(struct.pack("!B", byte))

    def read_ubyte(self):
        return struct.unpack("!B", self.read(1))[0]

    def write_short(self, short):
        self.write(struct.pack("!h", short))

    def read_short(self):
        return struct.unpack("!h", self.read(2))[0]

    def write_ushort(self, short):
        self.write(struct.pack("!H", short))

    def read_ushort(self):
        return struct.unpack("!H", self.read(2))[0]

    def write_long(self, long):
        self.write(struct.pack("!q", long))

    def read_long(self):
        return struct.unpack("!q", self.read(8))[0]

    def write_ulong(self, long):
        self.write(struct.pack("!Q", long))

    def read_ulong(self):
        return struct.unpack("!Q", self.read(8))[0]

    def write_float(self, float):
        self.write(struct.pack("!f", float))

    def read_float(self):
        return struct.unpack("!f", self.read(4))[0]

    def write_double(self, double):
        self.write(struct.pack("!d", double))

    def read_double(self):
        return struct.unpack("!d", self.read(8))[0]

    def write_varint(self, integer):
        if integer < 0:
            integer = (1 << 32) + integer

        if integer >= (1 << 32):
            raise ValueError("Integer too large")

        while integer > 0x7F:
            self.write_ubyte(integer & 0x7F | continue_bit)
            integer >>= 7

        self.write_ubyte(integer & 0x7F)

    def read_varint(self):
        integer = 0
        shift = 0
        while True:
            byte = self.read_ubyte()
            integer |= (byte & segment_bit) << shift
            shift += 7
            if not byte & continue_bit:
                break

        if integer & (1 << 31):
            integer = integer - (1 << 32)

        return integer

    def write_varlong(self, long):
        if long < 0:
            long = (1 << 64) + long

        if long >= (1 << 64):
            raise ValueError("Long too large")

        while long > 0x7F:
            self.write_ubyte(long & 0x7F | continue_bit)
            long >>= 7

        self.write_ubyte(long & 0x7F)

    def read_varlong(self):
        long = 0
        shift = 0
        while True:
            byte = self.read_ubyte()
            long |= (byte & segment_bit) << shift
            shift += 7
            if not byte & continue_bit:
                break

        if long & (1 << 63):
            long = long - (1 << 64)

        return long

    def write_string(self, string):
        s = string.encode("utf-8")
        self.write_varint(len(s))
        self.write(s)

    def read_string(self):
        length = self.read_varint()
        return self.read(length).decode("utf-8")

    def write_nbt(self, tag, name=""):
        assert isinstance(tag, nbt.NBT_Compound)

        self.write_byte(tag.id)
        self.write_ushort(len(name))
        self.write(name.encode("utf-8"))
        tag.write(self)

    def read_nbt(self):
        tag_id = self.read_byte()
        assert tag_id == nbt.NBT_Compound.id

        name_length = self.read_ushort()
        name = self.read(name_length).decode("utf-8")
        tag = nbt.NBT_Compound(self)
        return tag

    def write_uuid(self, uuid):
        self.write(uuid.bytes)

    def read_uuid(self):
        return uuid.UUID(bytes=self.read(16))

    def write_position(self, position):
        pos = ((position[0] & 0x3FFFFFFF) << 38) | ((position[2] & 0x3FFFFFF) << 12) | (position[1] & 0xFFF)
        self.write_long(pos)

    def read_position(self):
        pos = self.read_long()
        x = (pos >> 38) & 0x3FFFFFFF
        y = pos & 0xFFF
        z = (pos >> 12) & 0x3FFFFFF

        if x >= 0x20000000:
            x -= 0x40000000
        if z >= 0x20000000:
            z -= 0x40000000
        if y >= 0x800:
            y -= 0x1000

        return (x, y, z)


class PackedDataArray:
    def __init__(self, array, bits_per_value):
        self.array = array
        self.bits_per_value = bits_per_value

    def __len__(self):
        return len(self.array)

    def get_long_array(self):
        array = []

        values_per_long = 64 // self.bits_per_value
        long_count = -(-len(self.array) // values_per_long)

        for i in range(long_count):
            long = 0
            for j in range(values_per_long):
                try:
                    long |= self.array[i * values_per_long + j] << (j * self.bits_per_value)
                except IndexError:
                    break

            if long & (1 << 63):
                long = long - (1 << 64)

            try:
                struct.pack("!q", long)
            except struct.error as e:
                print("Long too large:", long)
                raise e

            array.append(long)

        return array

    def write(self, buf):
        values_per_long = 64 // self.bits_per_value
        long_count = -(-len(self.array) // values_per_long)

        buf.write_varint(long_count)

        for i in range(long_count):
            long = 0
            for j in range(values_per_long):
                try:
                    long |= self.array[i * values_per_long + j] << (j * self.bits_per_value)
                except IndexError:
                    break

            buf.write_ulong(long)


    @classmethod
    def read(cls, buf, bits_per_value, length):
        values_per_long = 64 // bits_per_value
        long_count = buf.read_varint()

        array = []
        for i in range(long_count):
            long = buf.read_long()
            for j in range(values_per_long):
                array.append(long & ((1 << bits_per_value) - 1))
                long >>= bits_per_value

        return cls(array[:length], bits_per_value)





def from_bytes(bytes):
    return Buffer(io.BytesIO(bytes))
