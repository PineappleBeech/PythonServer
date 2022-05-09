import zlib

import buffer
import gzip


class NBT_Tag:
    def __init__(self, value):
        if type(value) is buffer.Buffer:
            self.read(value)
        else:
            self.value = value

    def read(self, buffer):
        self.read_value(buffer)

    def read_value(self, buffer):
        raise NotImplementedError

    def write(self, buffer):
        self.write_value(buffer)

    def write_value(self, buffer):
        raise NotImplementedError

    def __str__(self):
        raise NotImplementedError


class NBT_BaseList(NBT_Tag):
    def __getitem__(self, item):
        return self.value[item]

    def __setitem__(self, key, value):
        self.value[key] = value

    def __len__(self):
        return len(self.value)

    def __iter__(self):
        return iter(self.value)


class NBT_End(NBT_Tag):
    id = 0

    def __init__(self):
        pass

    def read_value(self, f):
        raise NotImplementedError

    def write_value(self, f):
        raise NotImplementedError

    def __str__(self):
        raise NotImplementedError


class NBT_Byte(NBT_Tag):
    id = 1

    def write_value(self, buf):
        buf.write_byte(self.value)

    def read_value(self, buf):
        self.value = buf.read_byte()

    def __str__(self):
        return "Byte({})".format(self.value)


class NBT_Short(NBT_Tag):
    id = 2

    def write_value(self, buf):
        buf.write_short(self.value)

    def read_value(self, buf):
        self.value = buf.read_short()

    def __str__(self):
        return "Short({})".format(self.value)


class NBT_Int(NBT_Tag):
    id = 3

    def write_value(self, buf):
        buf.write_int(self.value)

    def read_value(self, buf):
        self.value = buf.read_int()

    def __str__(self):
        return "Int({})".format(self.value)


class NBT_Long(NBT_Tag):
    id = 4

    def write_value(self, buf):
        buf.write_long(self.value)

    def read_value(self, buf):
        self.value = buf.read_long()

    def __str__(self):
        return "Long({})".format(self.value)


class NBT_Float(NBT_Tag):
    id = 5

    def write_value(self, buf):
        buf.write_float(self.value)

    def read_value(self, buf):
        self.value = buf.read_float()

    def __str__(self):
        return "Float({})".format(self.value)


class NBT_Double(NBT_Tag):
    id = 6

    def write_value(self, buf):
        buf.write_double(self.value)

    def read_value(self, buf):
        self.value = buf.read_double()

    def __str__(self):
        return "Double({})".format(self.value)


class NBT_Byte_Array(NBT_BaseList):
    id = 7

    def write_value(self, buf):
        buf.write_int(len(self.value))
        for i in self.value:
            buf.write_byte(i)

    def read_value(self, buf):
        length = buf.read_int()
        self.value = list([buf.read_byte() for i in range(length)])

    def __str__(self):
        return "Byte_Array({})".format(self.value)


class NBT_String(NBT_Tag):
    id = 8

    def write_value(self, buf):
        s = self.value.encode('utf-8')
        buf.write_ushort(len(s))
        buf.write(s)

    def read_value(self, buf):
        length = buf.read_ushort()
        self.value = buf.read(length).decode('utf-8')

    def __str__(self):
        return "String({})".format(self.value)


class NBT_List(NBT_BaseList):
    id = 9

    def write_value(self, buf):
        buf.write_byte(self.value[0].id)
        buf.write_int(len(self.value))
        for i in self.value:
            i.write(buf)

    def read_value(self, buf):
        type_id = buf.read_byte()
        length = buf.read_int()
        self.value = list([tags[type_id](buf) for i in range(length)])

    def __str__(self):
        return "List([\n  " + (",\n".join([str(i) for i in self.value])).replace("\n", "\n  ") + "\n])"


class NBT_Compound(NBT_Tag):
    id = 10

    def __getitem__(self, item):
        return self.value[item]

    def __setitem__(self, key, value):
        self.value[key] = value

    def write_value(self, buf):
        for k, v in self.value.items():
            buf.write_byte(v.id)
            buf.write_ushort(len(k))
            buf.write(k.encode('utf-8'))
            v.write(buf)

        buf.write_byte(0)

    def read_value(self, buf):
        self.value = {}

        while True:
            type_id = buf.read_byte()
            if type_id == 0:
                break
            length = buf.read_ushort()
            name = buf.read(length).decode('utf-8')
            self.value[name] = tags[type_id](buf)

    def __str__(self):
        return "Compound({\n  " + (",\n".join([": ".join([k, str(v)]) for k, v in self.value.items()])).replace("\n", "\n  ") + "\n})"


class NBT_Int_Array(NBT_BaseList):
    id = 11

    def write_value(self, buf):
        buf.write_int(len(self.value))
        for i in self.value:
            buf.write_int(i)

    def read_value(self, buf):
        length = buf.read_int()
        self.value = list([buf.read_int() for i in range(length)])

    def __str__(self):
        return "Int_Array({})".format(self.value)


class NBT_Long_Array(NBT_BaseList):
    id = 12

    def write_value(self, buf):
        buf.write_int(len(self.value))
        for i in self.value:
            buf.write_long(i)

    def read_value(self, buf):
        length = buf.read_int()
        self.value = list([buf.read_long() for i in range(length)])

    def __str__(self):
        return "Long_Array({})".format(self.value)


tags = {
    0: NBT_End,
    1: NBT_Byte,
    2: NBT_Short,
    3: NBT_Int,
    4: NBT_Long,
    5: NBT_Float,
    6: NBT_Double,
    7: NBT_Byte_Array,
    8: NBT_String,
    9: NBT_List,
    10: NBT_Compound,
    11: NBT_Int_Array,
    12: NBT_Long_Array
}

def read_nbt(buf, compressed=False):
    if compressed:
        bytes = gzip.decompress(buf.read())
        buf = buffer.from_bytes(bytes)
    return buf.read_nbt()

def write_nbt(buf, nbt, name="", compress=False):
    if compress:
        temp_buf = buffer.Buffer()
        temp_buf.write_nbt(nbt)
        buf.write(gzip.compress(temp_buf.getvalue()))
    else:
        buf.write_nbt(nbt, name)

def to_json(nbt):
    if isinstance(nbt, NBT_Compound):
        return {k: to_json(v) for k, v in nbt.value.items()}
    elif isinstance(nbt, NBT_List):
        return [to_json(i) for i in nbt.value]
    else:
        return nbt.value
