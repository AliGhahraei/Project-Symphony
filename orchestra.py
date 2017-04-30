from collections import namedtuple
from copy import deepcopy
from functools import partial
from lexer import Types, DUPLICATED_OPERATORS
from math import sqrt, log, floor, ceil
from random import random
from operator import (add, sub, mul, truediv, mod, eq, gt, lt, ge, le, and_,
                      or_, pos, neg, not_)


MEMORY_SECTORS = (
    ('global_', 10_000),
    ('temporal', 130_000),
    ('constant', 200_000),
    ('local', 250_000),
    ('end', 350_000),
)


memory = {sector[0]: {type_ : {} for type_ in Types}
          for sector in MEMORY_SECTORS[:-1]}

activation_records = []
stored_program_counters = []

parameters = []
output = []

class UninitializedError(Exception):
    pass


class ChangeContext(Exception):
    def __init__(self, goto_line):
        self.goto_line = goto_line


def generate_memory_addresses(end_addresses=False):
    ADDRESS_TUPLE = namedtuple('ADDRESSES', [address[0] for address
                                             in MEMORY_SECTORS[:-1]])

    current_address = MEMORY_SECTORS[0][1]
    addresses = []
    for sector in MEMORY_SECTORS[1:]:
        next_address = sector[1]
        sector_size = next_address - current_address

        type_start_addresses = [starting_address for starting_address in
                                range(current_address, next_address,
                                      int(sector_size / len(Types)))]

        if end_addresses:
            type_end_addresses = type_start_addresses[1:] + [next_address]

            type_addresses = dict(zip(Types, zip(type_start_addresses,
                                                 type_end_addresses)))
        else:
            type_addresses = dict(zip(Types, type_start_addresses))

        addresses.append(type_addresses)
        current_address = next_address

    return ADDRESS_TUPLE._make(addresses)


addresses = generate_memory_addresses(end_addresses=True)


def value(address):
    try:
        address = int(address)
    except ValueError:
        # Array pointer was found, so remove '&' at the beginning
        address = value(address[1:])

    try:
        return get_address_container(address)[address]
    except KeyError as e:
        raise UninitializedError(f'Sorry, but you tried to use a variable '
                                 f'before assignment. Please check your program')


def store(value_to_store, address):
    try:
        address = int(address)
    except ValueError:
        # Array pointer was found, so remove '&' at the beginning
        address = value(address[1:])

    get_address_container(address)[address] = value_to_store


def get_address_container(address):
    for i, sector in enumerate(MEMORY_SECTORS[-2::-1], start=1):
        sector_name, sector_address = sector
        if address >= sector_address:
            for type_address in addresses[-i].items():
                type_, (start_address, end_address) = type_address
                if start_address <= address < end_address:
                    return memory[sector_name][type_]


def store_param(address):
    parameters.append(address)


def print_(end='\n'):
    parameter = value(parameters.pop())

    if isinstance(parameter, bool):
        parameter = str(parameter).lower()
    else:
        parameter = str(parameter)

    output.append(parameter + end)
    # print(printed_value, end=end)


def get(return_address):
    index = value(parameters.pop())
    string = value(parameters.pop())
    char = string[index]
    store(char, return_address)


def copy():
    destination_address = parameters.pop()
    source_value = value(parameters.pop())
    store(source_value, destination_address)


def length(return_address):
    store(len(value(parameters.pop())), return_address)


def sqrt_(return_address):
    store(sqrt(value(parameters.pop())), return_address)


def goto(jump):
    return int(jump)


def gotof(address, jump):
    if not value(address):
        return goto(jump)


def verify_limits(offset_address, min_, array_size):
    offset = value(offset_address)
    array_size = int(array_size)
    min_ = int(min_)

    if not min_ <= offset < array_size:
        raise IndexError(f"Index out of bounds: {offset}. This one should be "
                         f"greater than or equal to {min_} and smaller than "
                         f"{array_size}")

def array_access(base_dir, offset_address, address_pointer):
    offset = value(offset_address)
    base_dir = int(base_dir)
    store(base_dir + offset, address_pointer)


def end_proc(function_name):
    return_address = directory.functions[function_name].return_address
    if return_address != None:
        return_type = directory.functions[function_name].return_type
        try:
            return_value = memory['local'][return_type][return_address]
            activation_records[-1][return_type][return_address] = return_value
        except KeyError:
            pass

    memory['local'] = activation_records.pop()
    return stored_program_counters.pop() + 1


def gosub(function_name):
    activation_records.append(deepcopy(memory['local']))

    global directory
    function = directory.functions[function_name]
    for type_, address, argument in zip(function.parameter_types,
                                        function.parameter_addresses,
                                        parameters):
        memory['local'][type_][address] = value(argument)

    parameters.clear()
    raise ChangeContext(function.starting_quad)


def log_(return_address):
    store(log(value(parameters.pop())), return_address)


def random_(return_address):
    store(random(), return_address)


def little_star():
    pass


def A():
    pass


def B():
    pass


def C():
    pass


def D():
    pass


def E():
    pass


def F():
    pass


def G():
    pass


def to_str(return_address):
    store(str(value(parameters.pop())), return_address)


def floor_(return_address):
    store(floor(value(parameters.pop())), return_address)


def ceil_(return_address):
    store(ceil(value(parameters.pop())), return_address)


def input_(return_address):
    store("proximamente", return_address)


OPERATIONS = {
    '+' : add,
    '-' : sub,
    '*' : mul,
    '/' : truediv,
    '**' : pow,
    'mod' : mod,
    'equals' : eq,
    '>' : gt,
    '<' : lt,
    '>=' : ge,
    '<=' : le,
    'and' : and_,
    'or' : or_,
    '++' : partial(add, 1),
    '--' : lambda value: sub(value, 1),
    DUPLICATED_OPERATORS['+'] : pos,
    DUPLICATED_OPERATORS['-'] : neg,
    'not' : not_,
    '=' : lambda value: value,
}

VM_FUNCTIONS = {
    'PARAM' : store_param,
    'print' : partial(print_, end=''),
    'println' : print_,
    'sqrt' : sqrt_,
    'log' : log_,
    'get' : get,
    'little_star' : little_star,
    'A' : A,
    'B' : B,
    'C' : C,
    'D' : D,
    'E' : E,
    'F' : F,
    'G' : G,
    'length' : length,
    'copy' : copy,
    'random' : random_,
    'to_str' : to_str,
    'input' : input_,
    'floor' : floor_,
    'ceil' : ceil_,
    'GOTO' : goto,
    'GOTOF': gotof,
    'ACCESS' : array_access,
    'VER' : verify_limits,
    'GOSUB' : gosub,
    'ENDPROC' : end_proc,
}

SPECIAL_SIGNATURES = {
    'print' : (None, [{type_ for type_ in Types}]),
    'println' : (None, [{type_ for type_ in Types}]),
    'to_str' : (Types.STR, [{type_ for type_ in Types}]),
    'get' : (Types.CHAR, [{Types.STR}, {Types.INT}]),
    'sqrt' : (Types.DEC, [{Types.INT, Types.DEC}]),
    'log' : (Types.DEC, [{Types.INT, Types.DEC}]),
    'random' : (Types.DEC, []),
    'little_star' : (None, []),
    'A' : (None, []),
    'B' : (None, []),
    'C' : (None, []),
    'D' : (None, []),
    'E' : (None, []),
    'F' : (None, []),
    'G' : (None, []),
    'length' : (Types.INT, [{Types.STR}]),
    'copy' : (None, [{Types.STR}, {Types.STR}]),
    'to_str' : (Types.STR, [{type_ for type_ in Types}]),
    'input' : (Types.STR, []),
    'floor' : (Types.INT, [{Types.DEC}]),
    'ceil' : (Types.INT, [{Types.DEC}]),
}


def handle_vm_function(quad, current_quad_idx):
    try:
        operation = VM_FUNCTIONS[quad[0]]
        address1 = quad[1]
        return operation(address1)
    except TypeError:
        # Thrown if function needs two parameters
        address2 = quad[2]

        try:
            return operation(address1, address2)
        except TypeError:
            address3 = quad[3]
            return operation(address1, address2, address3)
    except IndexError:
        # No quad 0: parameterless
        return operation()
    except ChangeContext as e:
        stored_program_counters.append(current_quad_idx)

        return e.goto_line
    except KeyError:
        raise NotImplementedError(f"This operation isn't supported yet "
                                  f"({quad[0]})")


def handle_operation(operation, quad):
    address1 = quad[1]
    address2 = quad[2]

    try:
        address3 = quad[3]
    except IndexError:
        # Only 1 operand and 1 address to store the result
        result = operation(value(address1))
        store(result, address2)
    else:
        try:
            # 2 operands and 1 address to store the result
            value1 = value(address1)
            value2 = value(address2)
            result = operation(value1, value2)
            store(result, address3)
        except ZeroDivisionError as e:
            raise ZeroDivisionError(f'Oops! You tried to divide {value1} by 0. '
                                    f'Please correct your program') from e


def play_note(lines, constants, directory_):
    global directory
    directory = directory_

    memory['constant'] = constants
    output.clear()

    line_list = [line.split() for line in lines.split('\n')]

    current_quad_idx = 0
    while current_quad_idx < len(line_list):
        try:
            quad = line_list[current_quad_idx]
        except IndexError:
            # Finish when accessing non-existent quadruple (naive GOTO did it)
            return output

        try:
            operation = OPERATIONS[quad[0]]
        except KeyError:
            vm_result = handle_vm_function(quad, current_quad_idx)

            if vm_result is not None:
                current_quad_idx = vm_result
            else:
                current_quad_idx += 1
        except IndexError:
            # Empty operation (empty line) might only be found at the end
            return output
        else:
            handle_operation(operation, quad)
            current_quad_idx += 1

    return output
