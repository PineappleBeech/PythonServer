import network.connection
import time
import world.world
from block import block
from util import raycasting

class Server:
    def __init__(self):
        block.load_blocks()
        raycasting.gen_paths(world.world.WorldView.block_render_distance)

        self.world = world.world.World()

        self.listener = network.connection.ServerListener(self)

        print("Server started")

        self.tick_loop()

    def tick_loop(self):
        while True:
            start_time = time.time()
            self.tick()
            time.sleep(max(0, 1.0 / 20 - (time.time() - start_time)))

    def tick(self):
        self.listener.tick()
        self.world.tick()