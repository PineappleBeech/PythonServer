from util.util import AtomicInteger
from util.raycasting import path, path_to_list, follow_directions

class Entity:
    id_counter = AtomicInteger()
    def __init__(self, world):
        self.world = world
        self.id = Entity.id_counter.increment_and_get()
        self.position = (0.5, 0.5, 0.5)
        self.rotation = (0, 0)
        self.velocity = (0.0, 0.0, 0.0)
        self.block = None

    def move(self, x, y, z):
        new_position = (self.position[0] + x, self.position[1] + y, self.position[2] + z)
        self.block = follow_directions(self.block, path_to_list(path(self.position, new_position)))
        self.position = (new_position[0] % 1, new_position[1] % 1, new_position[2] % 1)



class LivingEntity(Entity):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)