import gzip
import unittest
import nbt
import io
import buffer


class ByteTest(unittest.TestCase):
    def test_byte_read(self):
        self.assertEqual(0, nbt.NBT_Byte(buffer.from_bytes(b'\x00')).value)
        self.assertEqual(1, nbt.NBT_Byte(buffer.from_bytes(b'\x01')).value)
        self.assertEqual(-1, nbt.NBT_Byte(buffer.from_bytes(b'\xff')).value)

    def test_byte_write(self):
        buf = buffer.Buffer()
        nbt.NBT_Byte(0).write(buf)
        self.assertEqual(b"\x00", buf.getvalue())
        buf = buffer.Buffer()
        nbt.NBT_Byte(1).write(buf)
        self.assertEqual(b"\x01", buf.getvalue())
        buf = buffer.Buffer()
        nbt.NBT_Byte(-1).write(buf)
        self.assertEqual(b"\xff", buf.getvalue())


class ShortTest(unittest.TestCase):
    def test_short_read(self):
        self.assertEqual(0, nbt.NBT_Short(buffer.from_bytes(b'\x00\x00')).value)
        self.assertEqual(1, nbt.NBT_Short(buffer.from_bytes(b'\x00\x01')).value)
        self.assertEqual(-1, nbt.NBT_Short(buffer.from_bytes(b'\xff\xff')).value)

    def test_short_write(self):
        buf = buffer.Buffer()
        nbt.NBT_Short(0).write(buf)
        self.assertEqual(b"\x00\x00", buf.getvalue())
        buf = buffer.Buffer()
        nbt.NBT_Short(1).write(buf)
        self.assertEqual(b"\x00\x01", buf.getvalue())
        buf = buffer.Buffer()
        nbt.NBT_Short(-1).write(buf)
        self.assertEqual(b"\xff\xff", buf.getvalue())


class IntTest(unittest.TestCase):
    def test_int_read(self):
        self.assertEqual(0, nbt.NBT_Int(buffer.from_bytes(b'\x00\x00\x00\x00')).value)
        self.assertEqual(1, nbt.NBT_Int(buffer.from_bytes(b'\x00\x00\x00\x01')).value)
        self.assertEqual(-1, nbt.NBT_Int(buffer.from_bytes(b'\xff\xff\xff\xff')).value)

    def test_int_write(self):
        buf = buffer.Buffer()
        nbt.NBT_Int(0).write(buf)
        self.assertEqual(b"\x00\x00\x00\x00", buf.getvalue())
        buf = buffer.Buffer()
        nbt.NBT_Int(1).write(buf)
        self.assertEqual(b"\x00\x00\x00\x01", buf.getvalue())
        buf = buffer.Buffer()
        nbt.NBT_Int(-1).write(buf)
        self.assertEqual(b"\xff\xff\xff\xff", buf.getvalue())


class LongTest(unittest.TestCase):
    def test_long_read(self):
        self.assertEqual(0, nbt.NBT_Long(buffer.from_bytes(b'\x00\x00\x00\x00\x00\x00\x00\x00')).value)
        self.assertEqual(1, nbt.NBT_Long(buffer.from_bytes(b'\x00\x00\x00\x00\x00\x00\x00\x01')).value)
        self.assertEqual(-1, nbt.NBT_Long(buffer.from_bytes(b'\xff\xff\xff\xff\xff\xff\xff\xff')).value)

    def test_long_write(self):
        buf = buffer.Buffer()
        nbt.NBT_Long(0).write(buf)
        self.assertEqual(b"\x00\x00\x00\x00\x00\x00\x00\x00", buf.getvalue())
        buf = buffer.Buffer()
        nbt.NBT_Long(1).write(buf)
        self.assertEqual(b"\x00\x00\x00\x00\x00\x00\x00\x01", buf.getvalue())
        buf = buffer.Buffer()
        nbt.NBT_Long(-1).write(buf)
        self.assertEqual(b"\xff\xff\xff\xff\xff\xff\xff\xff", buf.getvalue())


class FloatTest(unittest.TestCase):
    def test_float_read(self):
        self.assertEqual(0, nbt.NBT_Float(buffer.from_bytes(b'\x00\x00\x00\x00')).value)
        self.assertEqual(1, nbt.NBT_Float(buffer.from_bytes(b'\x3f\x80\x00\x00')).value)
        self.assertEqual(-1, nbt.NBT_Float(buffer.from_bytes(b'\xbf\x80\x00\x00')).value)

    def test_float_write(self):
        buf = buffer.Buffer()
        nbt.NBT_Float(0).write(buf)
        self.assertEqual(b"\x00\x00\x00\x00", buf.getvalue())
        buf = buffer.Buffer()
        nbt.NBT_Float(1).write(buf)
        self.assertEqual(b"\x3f\x80\x00\x00", buf.getvalue())
        buf = buffer.Buffer()
        nbt.NBT_Float(-1).write(buf)
        self.assertEqual(b"\xbf\x80\x00\x00", buf.getvalue())


class DoubleTest(unittest.TestCase):
    def test_double_read(self):
        self.assertEqual(0, nbt.NBT_Double(buffer.from_bytes(b'\x00\x00\x00\x00\x00\x00\x00\x00')).value)
        self.assertEqual(1, nbt.NBT_Double(buffer.from_bytes(b'\x3f\xf0\x00\x00\x00\x00\x00\x00')).value)
        self.assertEqual(-1, nbt.NBT_Double(buffer.from_bytes(b'\xbf\xf0\x00\x00\x00\x00\x00\x00')).value)

    def test_double_write(self):
        buf = buffer.Buffer()
        nbt.NBT_Double(0).write(buf)
        self.assertEqual(b"\x00\x00\x00\x00\x00\x00\x00\x00", buf.getvalue())
        buf = buffer.Buffer()
        nbt.NBT_Double(1).write(buf)
        self.assertEqual(b"\x3f\xf0\x00\x00\x00\x00\x00\x00", buf.getvalue())
        buf = buffer.Buffer()
        nbt.NBT_Double(-1).write(buf)
        self.assertEqual(b"\xbf\xf0\x00\x00\x00\x00\x00\x00", buf.getvalue())


class ByteArrayTest(unittest.TestCase):
    def test_byte_array_read(self):
        self.assertEqual([0, 1, 2, 3], nbt.NBT_Byte_Array(buffer.from_bytes(b"\x00\x00\x00\x04\x00\x01\x02\x03")).value)
        self.assertEqual([], nbt.NBT_Byte_Array(buffer.from_bytes(b"\x00\x00\x00\x00")).value)
        self.assertEqual([0], nbt.NBT_Byte_Array(buffer.from_bytes(b"\x00\x00\x00\x01\x00")).value)

    def test_byte_array_write(self):
        buf = buffer.Buffer()
        nbt.NBT_Byte_Array([0, 1, 2, 3]).write(buf)
        self.assertEqual(b"\x00\x00\x00\x04\x00\x01\x02\x03", buf.getvalue())
        buf = buffer.Buffer()
        nbt.NBT_Byte_Array([]).write(buf)
        self.assertEqual(b"\x00\x00\x00\x00", buf.getvalue())
        buf = buffer.Buffer()
        nbt.NBT_Byte_Array([0]).write(buf)
        self.assertEqual(b"\x00\x00\x00\x01\x00", buf.getvalue())


class StringTest(unittest.TestCase):
    def test_string_read(self):
        self.assertEqual("Hi", nbt.NBT_String(buffer.from_bytes(b"\x00\x02\x48\x69")).value)
        self.assertEqual("", nbt.NBT_String(buffer.from_bytes(b"\x00\x00")).value)

    def test_string_write(self):
        buf = buffer.Buffer()
        nbt.NBT_String("Hi").write(buf)
        self.assertEqual(b"\x00\x02\x48\x69", buf.getvalue())
        buf = buffer.Buffer()
        nbt.NBT_String("").write(buf)
        self.assertEqual(b"\x00\x00", buf.getvalue())


class FileTest(unittest.TestCase):
    def test_hello_world(self):
        with buffer.Buffer(open("nbt_examples/hello_world.nbt", "rb")) as f:
            nbt.read_nbt(f)

    def test_big(self):
        with buffer.Buffer(open("nbt_examples/bigtest.nbt", "rb")) as f:
            data = f.read()

            data = gzip.decompress(data)

            tag = nbt.read_nbt(buffer.from_bytes(data))
            new_data = buffer.Buffer()
            nbt.write_nbt(new_data, tag, name="Level")

            print(data)
            print(new_data.getvalue())

            self.assertEqual(data, new_data.read())

            a = str(tag)
            b = nbt.to_json(tag)
            print(b)

            #print(a)


if __name__ == '__main__':
    unittest.main()
