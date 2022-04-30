import unittest
from block import block
import os


class BlockTypeTestCase(unittest.TestCase):
    def test_air(self):
        block.load_blocks()
        b = block.Block("minecraft:air")
        self.assertEqual(0, b.get_id())

    def test_stone(self):
        block.load_blocks()
        b = block.Block("minecraft:stone")
        self.assertEqual(1, b.get_id())

    def test_sapling(self):
        block.load_blocks()
        b = block.Block("minecraft:oak_sapling")
        self.assertEqual(21, b.get_id())

    def test_grown_sapling(self):
        block.load_blocks()
        b = block.Block("minecraft:oak_sapling", {"stage": "1"})
        self.assertEqual(22, b.get_id())


    def test_leaves(self):
        block.load_blocks()
        b = block.Block("minecraft:oak_leaves", {"persistent": "false"})
        self.assertEqual(161, b.get_id())

    def test_leaves_persistent(self):
        block.load_blocks()
        b = block.Block("minecraft:oak_leaves", {"persistent": "true"})
        self.assertEqual(160, b.get_id())

    def test_leaves_no_info(self):
        block.load_blocks()
        b = block.Block("minecraft:oak_leaves")
        self.assertEqual(161, b.get_id())


if __name__ == '__main__':
    unittest.main()
