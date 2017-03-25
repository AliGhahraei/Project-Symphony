from collections import namedtuple
from lexer import Types

MEMORY_SECTORS = [
    ('global_', 10_000),
    ('local', 50_000),
    ('temporal', 170_000),
    ('constant', 200_000),
    ('end', 240_000),
]
sector_iterator = iter(MEMORY_SECTORS[:-1])
ADDRESS_TUPLE = namedtuple('ADDRESSES', [address[0] for address
                                         in sector_iterator])
