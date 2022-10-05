
import time
from random import randint


def generate_node_id():
    millis = int(round(time.time() * 1000))
    node_id = millis + randint(800000000000, 900000000000)
    return node_id