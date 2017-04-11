from collections import namedtuple
from lexer import Types


MEMORY_SECTORS = (
    ('global_', 10_000),
    ('local', 50_000),
    ('temporal', 170_000),
    ('constant', 200_000),
    ('end', 240_000),
)
sector_iterator = iter(MEMORY_SECTORS[:-1])
ADDRESS_TUPLE = namedtuple('ADDRESSES', [address[0] for address
                                         in sector_iterator])

def generate_memory_addresses():
    sector_iterator = iter(MEMORY_SECTORS)
    current_address = sector_iterator.__next__()[1]
    addresses = []
    for sector in sector_iterator:
        next_address = sector[1]
        sector_size = next_address - current_address

        type_addresses = [starting_address for starting_address in
                          range(current_address, next_address,
                                int(sector_size / len(Types)))]
        type_addresses = dict(zip(Types, type_addresses))

        addresses.append(type_addresses)
        current_address = next_address

    return ADDRESS_TUPLE._make(addresses)

#memory = ADDRESS_TUPLE._make(meh)


def assign():
    pass


def assign_literal():
    pass


OPERATIONS = {
    '=' : assign,
    'ASSIGN_LITERAL' : assign_literal,
}
