import unittest
import buffer
import io


class IntTestCase(unittest.TestCase):
    def test_one(self):
        buf = buffer.Buffer(io.BytesIO())
        buf.write_int(1)
        self.assertEqual(b"\x00\x00\x00\x01", buf.getvalue())
        buf.seek(0)
        self.assertEqual(1, buf.read_int())

    def test_minus_one(self):
        buf = buffer.Buffer(io.BytesIO())
        buf.write_int(-1)
        self.assertEqual(b"\xff\xff\xff\xff", buf.getvalue())
        buf.seek(0)
        self.assertEqual(-1, buf.read_int())

    def test_zero(self):
        buf = buffer.Buffer(io.BytesIO())
        buf.write_int(0)
        self.assertEqual(b"\x00\x00\x00\x00", buf.getvalue())
        buf.seek(0)
        self.assertEqual(0, buf.read_int())

    def test_max_int(self):
        buf = buffer.Buffer(io.BytesIO())
        buf.write_int(2**31-1)
        self.assertEqual(b"\x7f\xff\xff\xff", buf.getvalue())
        buf.seek(0)
        self.assertEqual(2**31-1, buf.read_int())

    def test_min_int(self):
        buf = buffer.Buffer(io.BytesIO())
        buf.write_int(-2**31)
        self.assertEqual(b"\x80\x00\x00\x00", buf.getvalue())
        buf.seek(0)
        self.assertEqual(-2**31, buf.read_int())


class BooleanTestCase(unittest.TestCase):
    def test_true(self):
        buf = buffer.Buffer(io.BytesIO())
        buf.write_bool(True)
        self.assertEqual(b"\x01", buf.getvalue())
        buf.seek(0)
        self.assertEqual(True, buf.read_bool())

    def test_false(self):
        buf = buffer.Buffer(io.BytesIO())
        buf.write_bool(False)
        self.assertEqual(b"\x00", buf.getvalue())
        buf.seek(0)
        self.assertEqual(False, buf.read_bool())


class ByteTestCase(unittest.TestCase):
    def test_one(self):
        buf = buffer.Buffer(io.BytesIO())
        buf.write_byte(1)
        self.assertEqual(b"\x01", buf.getvalue())
        buf.seek(0)
        self.assertEqual(1, buf.read_byte())

    def test_zero(self):
        buf = buffer.Buffer(io.BytesIO())
        buf.write_byte(0)
        self.assertEqual(b"\x00", buf.getvalue())
        buf.seek(0)
        self.assertEqual(0, buf.read_byte())

    def test_minus_one(self):
        buf = buffer.Buffer(io.BytesIO())
        buf.write_byte(-1)
        self.assertEqual(b"\xff", buf.getvalue())
        buf.seek(0)
        self.assertEqual(-1, buf.read_byte())

    def test_max_byte(self):
        buf = buffer.Buffer(io.BytesIO())
        buf.write_byte(2**7-1)
        self.assertEqual(b"\x7f", buf.getvalue())
        buf.seek(0)
        self.assertEqual(2**7-1, buf.read_byte())

    def test_min_byte(self):
        buf = buffer.Buffer(io.BytesIO())
        buf.write_byte(-2**7)
        self.assertEqual(b"\x80", buf.getvalue())
        buf.seek(0)
        self.assertEqual(-2**7, buf.read_byte())


class ShortTestCase(unittest.TestCase):
    def test_one(self):
        buf = buffer.Buffer(io.BytesIO())
        buf.write_short(1)
        self.assertEqual(b"\x00\x01", buf.getvalue())
        buf.seek(0)
        self.assertEqual(1, buf.read_short())

    def test_zero(self):
        buf = buffer.Buffer(io.BytesIO())
        buf.write_short(0)
        self.assertEqual(b"\x00\x00", buf.getvalue())
        buf.seek(0)
        self.assertEqual(0, buf.read_short())

    def test_minus_one(self):
        buf = buffer.Buffer(io.BytesIO())
        buf.write_short(-1)
        self.assertEqual(b"\xff\xff", buf.getvalue())
        buf.seek(0)
        self.assertEqual(-1, buf.read_short())

    def test_max_short(self):
        buf = buffer.Buffer(io.BytesIO())
        buf.write_short(2**15-1)
        self.assertEqual(b"\x7f\xff", buf.getvalue())
        buf.seek(0)
        self.assertEqual(2**15-1, buf.read_short())

    def test_min_short(self):
        buf = buffer.Buffer(io.BytesIO())
        buf.write_short(-2**15)
        self.assertEqual(b"\x80\x00", buf.getvalue())
        buf.seek(0)
        self.assertEqual(-2**15, buf.read_short())


class LongTestCase(unittest.TestCase):
    def test_one(self):
        buf = buffer.Buffer(io.BytesIO())
        buf.write_long(1)
        self.assertEqual(b"\x00\x00\x00\x00\x00\x00\x00\x01", buf.getvalue())
        buf.seek(0)
        self.assertEqual(1, buf.read_long())

    def test_zero(self):
        buf = buffer.Buffer(io.BytesIO())
        buf.write_long(0)
        self.assertEqual(b"\x00\x00\x00\x00\x00\x00\x00\x00", buf.getvalue())
        buf.seek(0)
        self.assertEqual(0, buf.read_long())

    def test_minus_one(self):
        buf = buffer.Buffer(io.BytesIO())
        buf.write_long(-1)
        self.assertEqual(b"\xff\xff\xff\xff\xff\xff\xff\xff", buf.getvalue())
        buf.seek(0)
        self.assertEqual(-1, buf.read_long())

    def test_max_long(self):
        buf = buffer.Buffer(io.BytesIO())
        buf.write_long(2**63-1)
        self.assertEqual(b"\x7f\xff\xff\xff\xff\xff\xff\xff", buf.getvalue())
        buf.seek(0)
        self.assertEqual(2**63-1, buf.read_long())

    def test_min_long(self):
        buf = buffer.Buffer(io.BytesIO())
        buf.write_long(-2**63)
        self.assertEqual(b"\x80\x00\x00\x00\x00\x00\x00\x00", buf.getvalue())
        buf.seek(0)
        self.assertEqual(-2**63, buf.read_long())


class FloatTestCase(unittest.TestCase):
    def test_one(self):
        buf = buffer.Buffer(io.BytesIO())
        buf.write_float(1.0)
        self.assertEqual(b"\x3f\x80\x00\x00", buf.getvalue())
        buf.seek(0)
        self.assertEqual(1.0, buf.read_float())

    def test_zero(self):
        buf = buffer.Buffer(io.BytesIO())
        buf.write_float(0.0)
        self.assertEqual(b"\x00\x00\x00\x00", buf.getvalue())
        buf.seek(0)
        self.assertEqual(0.0, buf.read_float())

    def test_minus_one(self):
        buf = buffer.Buffer(io.BytesIO())
        buf.write_float(-1.0)
        self.assertEqual(b"\xbf\x80\x00\x00", buf.getvalue())
        buf.seek(0)
        self.assertEqual(-1.0, buf.read_float())

    def test_max_float(self):
        buf = buffer.Buffer(io.BytesIO())
        buf.write_float(2**127-1)
        self.assertEqual(b"\x7f\x00\x00\x00", buf.getvalue())
        buf.seek(0)
        self.assertEqual(float(2**127-1), buf.read_float())

    def test_min_float(self):
        buf = buffer.Buffer(io.BytesIO())
        buf.write_float(-2**127)
        self.assertEqual(b"\xff\x00\x00\x00", buf.getvalue())
        buf.seek(0)
        self.assertEqual(float(-2**127), buf.read_float())


class DoubleTestCase(unittest.TestCase):
    def test_one(self):
        buf = buffer.Buffer(io.BytesIO())
        buf.write_double(1.0)
        self.assertEqual(b"\x3f\xf0\x00\x00\x00\x00\x00\x00", buf.getvalue())
        buf.seek(0)
        self.assertEqual(1.0, buf.read_double())

    def test_zero(self):
        buf = buffer.Buffer(io.BytesIO())
        buf.write_double(0.0)
        self.assertEqual(b"\x00\x00\x00\x00\x00\x00\x00\x00", buf.getvalue())
        buf.seek(0)
        self.assertEqual(0.0, buf.read_double())

    def test_minus_one(self):
        buf = buffer.Buffer(io.BytesIO())
        buf.write_double(-1.0)
        self.assertEqual(b"\xbf\xf0\x00\x00\x00\x00\x00\x00", buf.getvalue())
        buf.seek(0)
        self.assertEqual(-1.0, buf.read_double())

    def test_max_double(self):
        buf = buffer.Buffer(io.BytesIO())
        buf.write_double(2**1023-1)
        self.assertEqual(b"\x7f\xe0\x00\x00\x00\x00\x00\x00", buf.getvalue())
        buf.seek(0)
        self.assertEqual(float(2**1023-1), buf.read_double())

    def test_min_double(self):
        buf = buffer.Buffer(io.BytesIO())
        buf.write_double(-2**1023)
        self.assertEqual(b"\xff\xe0\x00\x00\x00\x00\x00\x00", buf.getvalue())
        buf.seek(0)
        self.assertEqual(float(-2**1023), buf.read_double())


class VarIntTestCase(unittest.TestCase):
    def test_one(self):
        buf = buffer.Buffer(io.BytesIO())
        buf.write_varint(1)
        self.assertEqual(b"\x01", buf.getvalue())
        buf.seek(0)
        self.assertEqual(1, buf.read_varint())

    def test_zero(self):
        buf = buffer.Buffer(io.BytesIO())
        buf.write_varint(0)
        self.assertEqual(b"\x00", buf.getvalue())
        buf.seek(0)
        self.assertEqual(0, buf.read_varint())

    def test_minus_one(self):
        buf = buffer.Buffer(io.BytesIO())
        buf.write_varint(-1)
        self.assertEqual(b"\xff\xff\xff\xff\x0f", buf.getvalue())
        buf.seek(0)
        self.assertEqual(-1, buf.read_varint())

    def test_max_varint(self):
        buf = buffer.Buffer(io.BytesIO())
        buf.write_varint(2**31-1)
        self.assertEqual(b"\xff\xff\xff\xff\x07", buf.getvalue())
        buf.seek(0)
        self.assertEqual(2**31-1, buf.read_varint())

    def test_min_varint(self):
        buf = buffer.Buffer(io.BytesIO())
        buf.write_varint(-2**31)
        self.assertEqual(b"\x80\x80\x80\x80\x08", buf.getvalue())
        buf.seek(0)
        self.assertEqual(-2**31, buf.read_varint())


class VarLongTestCase(unittest.TestCase):
    def test_one(self):
        buf = buffer.Buffer(io.BytesIO())
        buf.write_varlong(1)
        self.assertEqual(b"\x01", buf.getvalue())
        buf.seek(0)
        self.assertEqual(1, buf.read_varlong())

    def test_zero(self):
        buf = buffer.Buffer(io.BytesIO())
        buf.write_varlong(0)
        self.assertEqual(b"\x00", buf.getvalue())
        buf.seek(0)
        self.assertEqual(0, buf.read_varlong())

    def test_minus_one(self):
        buf = buffer.Buffer(io.BytesIO())
        buf.write_varlong(-1)
        self.assertEqual(b"\xff\xff\xff\xff\xff\xff\xff\xff\xff\x01", buf.getvalue())
        buf.seek(0)
        self.assertEqual(-1, buf.read_varlong())

    def test_max_varlong(self):
        buf = buffer.Buffer(io.BytesIO())
        buf.write_varlong(2**63-1)
        self.assertEqual(b"\xff\xff\xff\xff\xff\xff\xff\xff\x7f", buf.getvalue())
        buf.seek(0)
        self.assertEqual(2**63-1, buf.read_varlong())

    def test_min_varlong(self):
        buf = buffer.Buffer(io.BytesIO())
        buf.write_varlong(-2**63)
        self.assertEqual(b"\x80\x80\x80\x80\x80\x80\x80\x80\x80\x01", buf.getvalue())
        buf.seek(0)
        self.assertEqual(-2**63, buf.read_varlong())


class PackedDataTestCase(unittest.TestCase):
    def test_normal(self):
        buf = buffer.Buffer(io.BytesIO())
        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        array = buffer.PackedDataArray(data, 4)
        array.write(buf)
        self.assertEqual(b"\x01\x00\x00\x00\xa9\x87\x65\x43\x21", buf.getvalue())
        array = buffer.PackedDataArray.read(buf, 4, 10)
        self.assertEqual(data, array.array)

    def test_empty(self):
        buf = buffer.Buffer(io.BytesIO())
        data = []
        array = buffer.PackedDataArray(data, 4)
        array.write(buf)
        self.assertEqual(b"\x00", buf.getvalue())
        array = buffer.PackedDataArray.read(buf, 4, 0)
        self.assertEqual(data, array.array)

    def test_multiple_longs(self):
        buf = buffer.Buffer(io.BytesIO())
        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        array = buffer.PackedDataArray(data, 8)
        array.write(buf)
        self.assertEqual(b"\x02\x08\x07\x06\x05\x04\x03\x02\x01\x00\x00\x00\x00\x00\x00\x0a\x09", buf.getvalue())
        array = buffer.PackedDataArray.read(buf, 8, 10)
        self.assertEqual(data, array.array)

if __name__ == '__main__':
    unittest.main()
