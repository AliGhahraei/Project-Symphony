from collections import namedtuple
from lexer import Types


MEMORY_SECTORS = [
    ('global_', 10_000),
    ('local', 50_000),
    ('temporal', 170_000),
    ('constant', 200_000),
    ('end', 240_000),
]
ADDRESS_TUPLE = namedtuple('ADDRESSES', [address[0] for address
                                         in MEMORY_SECTORS[:-1]])

def generate_memory_addresses():
    current_address = MEMORY_SECTORS[0][1]
    addresses = []
    for sector in MEMORY_SECTORS[1:]:
        next_address = sector[1]
        sector_size = next_address - current_address

        type_addresses = [starting_address for starting_address in
                          range(current_address, next_address,
                                int(sector_size / len(Types)))]
        type_addresses = dict(zip(Types, type_addresses))

        addresses.append(type_addresses)
        current_address = next_address

    return ADDRESS_TUPLE._make(addresses)



def assign():
    pass


def assign_literal():
    pass


OPERATIONS = {
    '=' : assign,
    'ASSIGN_LITERAL' : assign_literal,
}
