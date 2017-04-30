#!/usr/bin/python3.6

from collections import deque
from lexer import (tokens, Types, NonUserTypes, OPERATORS, UNARY_OPERATORS,
                   CONSTANT_VALS, DUPLICATED_OPERATORS, SELF_UPDATE_OPERATORS)
from ply.yacc import yacc
from sys import exit, argv

from print_colors import print_red, print_green
from orchestra import (generate_memory_addresses, play_note,
                       SPECIAL_PARAMETER_TYPES)


CUBE = [
    [
        [Types.INT] * 3 + [Types.DEC] + [Types.INT] * 2 + [Types.BOOL] * 5,
        [],
        [],
        [],
        [Types.DEC] * 6 + [Types.BOOL] * 5,
    ],
    [
        [],
        [Types.STR] + [None] * 5 + [Types.BOOL] * 5,
        [Types.STR],
        [],
        [],
    ],
    [
        [],
        [Types.STR],
        [Types.STR] + [None] * 5 + [Types.BOOL] * 5,
        [],
        [],
    ],
    [
        [],
        [],
        [],
        [None] * 6 + [Types.BOOL] * 8,
        [],
    ],
    [
        [Types.DEC] * 6 + [Types.BOOL] * 5,
        [],
        [],
        [],
        [Types.DEC] * 6 + [Types.BOOL] * 5,
    ],
]

UNARY_TABLE = [
    [Types.INT.value] * 4,
    [],
    [],
    [None] *4 + [Types.BOOL.value],
    [Types.DEC.value] *4,
]

directory = None
quadruple_generator = None


class FunctionScope():
    def __init__(self, return_type, name, starting_quad):
        self.name = name
        self.return_type = return_type
        self.variables = {}
        self.parameter_types = deque()
        self.parameter_addresses = deque()
        self.first_quadruple = None
        self.return_address = None
        self.starting_quad = starting_quad


class Directory():
    GLOBAL_SCOPE = None

    def __init__(self):
        self.current_scope = None
        self.functions = {}
        self.define_function('VOID', Directory.GLOBAL_SCOPE, 0)


    def end_definition(self, line_number):
        current_function = self.functions[self.current_scope]

        if (current_function.return_type != 'VOID'
          and current_function.return_address is None):
            raise ReturnError(f'Error on line {line_number}: This function '
                              f'was supposed to return a(n) '
                              f'{current_function.return_type.name}, but it '
                              f'does not return anything')

        self.functions[self.current_scope].variables.clear()
        self.current_scope = Directory.GLOBAL_SCOPE
        quadruple_generator.generate_quad('ENDPROC', current_function.name)


    def declare_variables(self, parameters, variables, line_number,
                          is_global=False):
        self.functions[self.current_scope].first_quadruple = len(
            quadruple_generator.quadruples)

        for parameter in parameters:
            self.functions[self.current_scope].parameter_types.appendleft(
                parameter[0])

            self._declare_variable(parameter, is_global, line_number)
            self.functions[self.current_scope].parameter_addresses.appendleft(
                self.functions[self.current_scope].variables[parameter[1]][1])

        for variable in variables:
            self._declare_variable(variable, is_global, line_number)


    def define_function(self, return_type, function, line_number):
        if function in self.functions:
            raise RedeclarationError(f'Error on line {line_number}: you are'
                                     f' defining your {function} function more'
                                     f' than once')

        starting_quad = len(quadruple_generator.quadruples)
        self.current_scope = function
        self.functions[function] = FunctionScope(return_type, function,
                                                 starting_quad)


    def _declare_variable(self, variable, is_global, line_number):
        current_function_vars = self.functions[self.current_scope].variables

        try:
            variable_type, (variable_name, array_size) = variable
            array_size_type, array_size_value = array_size
        except ValueError:
            variable_type, variable_name = variable

            if variable_name in current_function_vars:
                raise RedeclarationError(f'Error on line {line_number}: you are '
                                         f'declaring your {variable_name} '
                                         f' variable more than once')

            current_function_vars[variable_name] = (
                variable_type,
                quadruple_generator.generate_variable_address(variable_type,
                                                              is_global),
                variable_name,
            )
        else:
            if variable_name in current_function_vars:
                raise RedeclarationError(f'Error on line {line_number}: you are '
                                         f'declaring your {variable_name} variable '
                                         f'more than once')

            if array_size_type != Types.INT:
                raise TypeError(f'Error on line {line_number}: you are trying to'
                                f' declare an array size using a(n) '
                                f'{array_size_type.name}, but you should use '
                                f'a(n) {Types.INT.name} instead')

            current_function_vars[variable_name] = (
                NonUserTypes.ARRAY,
                quadruple_generator.generate_variable_address(
                    variable_type,
                    is_global,
                    array_size_value
                ),
                variable_name,
                variable_type,
                array_size_value
            )


    def get_variable(self, name, line_number):
        try:
            variable = self.functions[self.current_scope].variables[name]
        except KeyError:
            try:
                variable = self.functions[Directory.GLOBAL_SCOPE].variables[name]
            except KeyError:
                raise NameError(f'Error on line {line_number}: You tried'
                                f' to use the variable {name}, but it was'
                                f' not declared beforehand. Check if you'
                                f' wrote the name correctly and if you are'
                                f' trying to use a variable defined inside'
                                f' another function')
        return variable


class QuadrupleGenerator():
    def __init__(self, filepath):
        self.ADDRESSES = generate_memory_addresses()
        self.filepath = filepath
        self.operands = []
        self.CONSTANT_ADDRESS_DICT = {type_: {} for type_ in Types}
        self.quadruples = []
        self.pending_jumps = []
        self.called_functions = []
        self.arguments = deque()
        self.chained_operators = []
        self.recursive_calls = []
        self.pending_breaks = []


    def pop_operand(self, line_number):
        try:
            return self.operands.pop()
        except IndexError:
            self.empty_operand_error(line_number)


    def empty_operand_error(self, line_number):
        raise TypeError(f"Error on line {line_number}: You can't use a "
                        f"void function here because it does not return a "
                        f"value")


    def operate_right(self, operator_symbol, line_number):
        right_type, right_address = self.pop_operand(line_number)
        left_type, left_address = self.pop_operand(line_number)

        try:
            result_type = CUBE[left_type][right_type][OPERATORS[operator_symbol]]
            if result_type == None:
                raise IndexError('Result is None')

            result_address = self.generate_temporal_address(
                result_type)

            self.generate_quad(operator_symbol, left_address,
                                             right_address, result_address)
            self.operands.append((result_type, result_address))
        except IndexError:
            raise TypeError(
                f'Error on line {line_number}: The {operator_symbol} operation'
                f' cannot be used for types {left_type.name} and '
                f'{right_type.name}')


    def operate_left(self, operator_symbol, line_number):
        self.chained_operators.append(operator_symbol)
        operators = self.chained_operators[::-1]

        right_operands_start = -len(self.chained_operators)
        first_operand_idx = right_operands_start  - 1

        try:
            left_operand = self.operands[first_operand_idx]
            right_operands = self.operands[right_operands_start:]
        except IndexError:
            self.empty_operand_error(line_number)

        for right_operand, operator in zip(right_operands, operators):
            right_type, right_address = right_operand
            left_type, left_address = left_operand

            try:
                result_type = CUBE[left_type][right_type][OPERATORS[operator]]
                if result_type == None:
                    raise IndexError('Result is None')

                result_address = self.generate_temporal_address(
                    result_type)

                self.generate_quad(operator, left_address, right_address,
                                   result_address)
                left_operand = (result_type, result_address)
            except IndexError:
                raise TypeError(
                    f'Error on line {line_number}: The {operator} operation'
                    f' cannot be used for types {left_type.name} and '
                    f'{right_type.name}')

        self.chained_operators.clear()
        del self.operands[first_operand_idx:]

        self.operands.append(left_operand)

    def operate_unary(self, operator_symbol, line_number):
        type_, address = self.pop_operand(line_number)

        try:
            result_type = UNARY_TABLE[type_][UNARY_OPERATORS[operator_symbol]]
            if result_type == None:
                raise IndexError('Result is None')

            if operator_symbol in SELF_UPDATE_OPERATORS:
                result_address = address
            else:
                result_address = self.generate_temporal_address(result_type)

            if operator_symbol in DUPLICATED_OPERATORS:
                operator_symbol = DUPLICATED_OPERATORS[operator_symbol]

            self.generate_quad(operator_symbol, address, result_address)
            self.operands.append((result_type, result_address))
        except IndexError:
            raise TypeError(
                f'Error on line {line_number}: The {operator_symbol} operation'
                f' cannot be used for type {type_.name}')


    def generate_boolean_structure(self, line_number, structure_name):
        type_, address = self.pop_operand(line_number)

        if type_ != Types.BOOL:
            raise TypeError(
                f'Error on line {line_number}: The code inside your '
                f'{structure_name} must receive a {Types.BOOL.name} inside its '
                f'parenthesis, but a(n) {type_.name} was found.')

        self.pending_jumps.append(len(self.quadruples))
        self.generate_quad('GOTOF', address)


    def add_pending_if(self):
        self.quadruples[self.pending_jumps.pop()] += ' ' + str(len(
            self.quadruples))


    def add_pending_while(self):
        gotof_quad = self.pending_jumps.pop()
        expression_quad = self.pending_jumps.pop()

        self.generate_quad('GOTO', expression_quad)

        quad_after_while = len(self.quadruples)
        self.quadruples[gotof_quad] += ' ' + str(quad_after_while)

        for pending_break_quad in self.pending_breaks:
            self.quadruples[pending_break_quad] += ' ' + str(quad_after_while)
        self.pending_breaks.clear()


    def generate_break(self, line_number):
        self.pending_breaks.append(len(self.quadruples))
        self.generate_quad('GOTO')


    def add_else_jumps(self):
        pending_if_jump = self.pending_jumps.pop()
        self.pending_jumps.append(len(self.quadruples))
        self.generate_quad('GOTO')
        self.quadruples[pending_if_jump] += ' ' + str(len(self.quadruples))


    def assign(self, name, line_number):
        variable = directory.get_variable(name, line_number)

        try:
            offset_type, offset_value = directory.current_array_offset
            del directory.current_array_offset
        except AttributeError:
            left_type = variable[0]
            left_address = variable[1]

            if left_type == NonUserTypes.ARRAY:
                raise TypeError(f"Error on line {line_number}: You can't assign "
                                f"an array directly. You can, however, assign "
                                f"each element individually using the '[]' "
                                f"symbols")
        else:
            if offset_type != Types.INT:
                raise TypeError(f'Error on line {line_number}: you are trying to'
                                f' access an array using a(n) '
                                f'{offset_type.name}, but you should use '
                                f'a(n) {Types.INT.name}')

            if variable[0] != NonUserTypes.ARRAY:
                raise TypeError(f"Error on line {line_number}: you tried to access "
                                f"your {name} variable, but it's not an array")

            # The array's real type
            left_type = variable[3]

            array_size_value = variable[4]
            self.generate_quad('VER', offset_value, 0, array_size_value)

            base_address = variable[1]
            left_address = self.generate_temporal_address(left_type)
            self.generate_quad('ACCESS', base_address, offset_value, left_address)
            left_address = "&" + str(left_address)

        right_type, right_address = self.pop_operand(line_number)
        if left_type == right_type:
            self.generate_quad('=', right_address, left_address)
        else:
            raise TypeError(f'Error on line {line_number}: you are trying '
                            f'to assign a(n) {right_type.name} value to '
                            f'a(n) {left_type.name} type')


    def generate_quad(self, *args):
        self.quadruples.append(' '.join(str(arg) for arg in args))


    def generate_main_goto(self):
        self.quadruples[0] += ' ' + str(len(self.quadruples))


    def read_parameter(self, line_number):
        self.arguments.appendleft(self.pop_operand(line_number))


    def call(self, function, line_number):
        called_function_name = self.called_functions.pop()
        called_function = directory.functions[called_function_name]
        parameter_types = called_function.parameter_types

        if len(self.arguments) != len(parameter_types):
            raise ArityError(f'Error on line {line_number}: You are sending '
                             f'the wrong number of arguments '
                             f'({len(self.arguments)}) to '
                             f'{called_function_name}. It needs '
                             f'{len(parameter_types)}')

        for i, (argument, parameter_type) in enumerate(
          zip(self.arguments, parameter_types), start=1):
            argument_type, argument_address = argument

            if argument_type != parameter_type:
                raise TypeError(f'Error on line {line_number}: Your call to '
                                f'{called_function_name} sent a(n) '
                                f'{argument_type.name} as the argument number '
                                f'{i}, but a(n) {parameter_type.name} was '
                                f'expected')

            self.generate_quad('PARAM', argument_address, i)

        self.generate_quad('GOSUB', called_function_name)
        self.arguments.clear()

        if called_function.return_type != 'VOID':
            is_global = directory.current_scope == directory.GLOBAL_SCOPE

            result_address = self.generate_variable_address(
                called_function.return_type, is_global)
            self.operands.append((called_function.return_type, result_address))

            if called_function.return_address == None:
                self.recursive_calls.append((len(self.quadruples),
                                             result_address))
                self.generate_quad('=')
            else:
                self.generate_quad('=', called_function.return_address,
                                   result_address)


    def special_call(self, function, line_number):
        called_function_name = self.called_functions.pop()
        parameter_types = SPECIAL_PARAMETER_TYPES[called_function_name]

        if len(self.arguments) != len(parameter_types):
            raise ArityError(f'Error on line {line_number}: You are sending '
                             f'the wrong number of arguments '
                             f'({len(self.arguments)}) to '
                             f'{called_function_name}. It needs '
                             f'{len(parameter_types)}')

        for i, (argument, allowed_types) in enumerate(
          zip(self.arguments, parameter_types), start=1):
            argument_type, argument_address = argument

            if argument_type not in allowed_types:
                allowed_list = ', '.join([type_name.name for type_name
                                         in allowed_types])

                raise TypeError(f'Error on line {line_number}: Your call to '
                                f'{called_function_name} sent a(n) '
                                f'{argument_type.name} as the argument number '
                                f'{i}, but one of these was expected: '
                                f'{allowed_list}')

            self.generate_quad('PARAM', argument_address, i)

        self.generate_quad(called_function_name)
        self.arguments.clear()


    def generate_variable_address(self, variable_type, is_global, reserved=1):
        if is_global:
            new_address = self.ADDRESSES.global_[variable_type]
            self.ADDRESSES.global_[variable_type] = new_address + reserved
        else:
            new_address = self.ADDRESSES.local[variable_type]
            self.ADDRESSES.local[variable_type] = new_address + reserved

        return new_address


    def push_constant(self, type_, value):
        try:
            address = self.CONSTANT_ADDRESS_DICT[type_][value]
        except KeyError:
            address = self.ADDRESSES.constant[type_]
            self.ADDRESSES.constant[type_] = address + 1

            self.CONSTANT_ADDRESS_DICT[type_][value] = address

        self.operands.append((type_, address))


    def generate_temporal_address(self, variable_type):
        new_address = self.ADDRESSES.temporal[variable_type]
        self.ADDRESSES.temporal[variable_type] = new_address + 1
        return new_address


    def write_quads(self):
        self.filepath = self.filepath[:-4] + '.note'

        with open(self.filepath, 'w') as file:
            file.write('\n'.join(self.quadruples))


    def store_expression_position(self):
        self.pending_jumps.append(len(self.quadruples))

    def init_call(self, function, line_number):
        try:
            directory.functions[function]
        except KeyError:
            raise NameError(f'Error on line {line_number}: You tried'
                            f' to use the function {function}, but it was'
                            f' not defined beforehand. Check if you'
                            f' wrote the name correctly.')

        self.called_functions.append(function)

    def init_special(self, function, line_number):
        self.called_functions.append(function)

    def generate_return(self, line_number):
        current_function = directory.functions[directory.current_scope]

        if current_function.return_address is not None:
            raise ReturnError('You cannot have multiple returns inside a '
                              'function')

        if directory.current_scope == directory.GLOBAL_SCOPE:
            raise ReturnError(f'Error on line {line_number}: You cannot use '
                              f'return if you are not inside a function')

        return_type, return_address = self.pop_operand(line_number)
        expected_type = current_function.return_type

        if expected_type == 'VOID':
            raise ReturnError(f'Error on line {line_number}: This function was '
                            f'declared with a VOID return type, so it should '
                            f'not have a return here')

        if return_type != expected_type:
            raise TypeError(f'Error on line {line_number}: Your '
                            f'{current_function.name} should return a(n) '
                            f'{expected_type.name}, but it tried to return a(n) '
                            f'{return_type.name}')

        current_function.return_address = return_address
        for quad_idx, result_address in self.recursive_calls:
            self.quadruples[quad_idx] += f' {return_address} {result_address}'


    def generate_access(self, array_name, line_number):
        offset_type, offset_value = self.pop_operand(line_number)

        if offset_type != Types.INT:
            raise TypeError(f'Error on line {line_number}: you are trying to'
                            f' access an array using a(n) '
                            f'{offset_type.name}, but you should use '
                            f'a(n) {Types.INT.name} instead')

        variable = directory.get_variable(array_name, line_number)

        type_ = variable[0]

        if type_ != NonUserTypes.ARRAY:
            raise TypeError(f"Error on line {line_number}: you tried to access "
                            f"your {array_name} variable, but it's not an array")

        array_size_value = variable[4]
        self.generate_quad('VER', offset_value, 0, array_size_value)

        base_address = variable[1]
        real_type = variable[3]
        result_address = self.generate_temporal_address(real_type)

        self.generate_quad('ACCESS', base_address, offset_value, result_address)
        return real_type, "&" + str(result_address)


class GrammaticalError(Exception):
    pass


class RedeclarationError(Exception):
    pass


class ReturnError(Exception):
    pass


class ArityError(Exception):
    pass


def finalize():
    quadruple_generator.write_quads()


def p_program(p):
    ''' program : PROGRAM ID ';' global_declarations function_declaration main_goto statements '''
    finalize()


def p_main_goto(p):
    ''' main_goto : empty '''
    quadruple_generator.generate_main_goto()


def p_global_declarations(p):
    ''' global_declarations : variable_declaration '''
    quadruple_generator.generate_quad('GOTO')
    directory.declare_variables([], p[1], p.lexer.lineno, is_global=True)


def p_empty(p):
    ''' empty : '''
    p[0] = None


def p_variable_declaration(p):
    ''' variable_declaration : variable_group variable_declaration
                             | empty '''
    if p[1] is not None:
        p[0] = p[1] + p[2]
    else:
        p[0] = []


def p_variable_group(p):
    ''' variable_group : type declaration_ids ';' '''
    p[0] = []
    for variable_id in p[2]:
        p[0].append((p[1], variable_id))


def p_declaration_ids(p):
    ''' declaration_ids : declaration_id other_declaration_ids '''
    if p[2]:
        p[2].append(p[1])
        p[0] = p[2]
    else:
        p[0] = [p[1]]


def p_other_declaration_ids(p):
    ''' other_declaration_ids : ',' declaration_ids
                              | empty '''
    if p[1] is None:
        p[0] = []
    else:
        p[0] = p[2]


def p_declaration_id(p):
    ''' declaration_id : non_array_id
                       | array_declaration '''
    p[0] = p[1]


def p_usage_id(p):
    ''' usage_id : non_array_usage
                 | array_usage '''
    p[0] = p[1]


def p_assignment_id(p):
    ''' assignment_id : non_array_id
                      | array_assignment '''
    p[0] = p[1]


def p_non_array_id(p):
    ''' non_array_id : ID '''
    p[0] = p[1]


def p_array_declaration(p):
    ''' array_declaration : ID '[' int_val ']' '''
    p[0] = p[1], p[3]
    # The array size won't be used by anyone else
    quadruple_generator.operands.pop()


def p_non_array_usage(p):
    ''' non_array_usage : ID '''
    # return type and address from vartable
    p[0] = directory.get_variable(p[1], p.lexer.lineno)[0:2]


def p_array_usage(p):
    ''' array_usage : ID '[' expression ']' '''
    p[0] = quadruple_generator.generate_access(p[1], p.lexer.lineno)


def p_array_assignment(p):
    ''' array_assignment : ID '[' expression ']' '''
    directory.current_array_offset = quadruple_generator.operands.pop()
    p[0] = p[1]


def p_expression(p):
    ''' expression : level1
                   | exp_op '''


def p_exp_op(p):
    ''' exp_op : level1 EXPONENTIATION expression '''
    quadruple_generator.operate_right(p[2], p.lexer.lineno)


def p_level1(p):
    ''' level1 : level2
               | plus_minus_op '''


def p_plus_minus_op(p):
    ''' plus_minus_op : '+' level2
                      | '-' level2 '''
    quadruple_generator.operate_unary(p[1], p.lexer.lineno)


def p_level2(p):
    ''' level2 : level3
               | logical_op '''


def p_logical_op(p):
    ''' logical_op : level3 OR level3 chained_logical_ops
                   | level3 AND level3 chained_logical_ops '''
    quadruple_generator.operate_left(p[2], p.lexer.lineno)


def p_chained_logical_ops(p):
    ''' chained_logical_ops : chained_logical_op
                            | empty '''

def p_chained_logical_op(p):
    ''' chained_logical_op : OR level3 chained_logical_ops
                           | AND level3 chained_logical_ops '''
    quadruple_generator.chained_operators.append(p[1])


def p_level3(p):
    ''' level3 : level4
               | rel_op '''


def p_rel_op(p):
    ''' rel_op : level4 '<' level4 chained_rel_ops
               | level4 '>' level4 chained_rel_ops
               | level4 LESS_EQUAL_THAN level4 chained_rel_ops
               | level4 GREATER_EQUAL_THAN level4 chained_rel_ops
               | level4 EQUALS level4 chained_rel_ops '''
    quadruple_generator.operate_left(p[2], p.lexer.lineno)


def p_chained_rel_ops(p):
    ''' chained_rel_ops : chained_rel_op
                        | empty '''

def p_chained_rel_op(p):
    ''' chained_rel_op : '<' level4 chained_rel_ops
                       | '>' level4 chained_rel_ops
                       | LESS_EQUAL_THAN level4 chained_rel_ops
                       | GREATER_EQUAL_THAN level4 chained_rel_ops
                       | EQUALS level4 chained_rel_ops '''
    quadruple_generator.chained_operators.append(p[1])


def p_level4(p):
    ''' level4 : level5
               | add_subs_op '''


def p_add_subs_op(p):
    ''' add_subs_op : level5 '+' level5 chained_add_subs_ops
                    | level5 '-' level5 chained_add_subs_ops '''
    quadruple_generator.operate_left(p[2], p.lexer.lineno)


def p_chained_add_subs_ops(p):
    ''' chained_add_subs_ops : chained_add_subs_op
                             | empty '''

def p_chained_add_subs_op(p):
    ''' chained_add_subs_op : '+' level5 chained_add_subs_ops
                            | '-' level5 chained_add_subs_ops '''
    quadruple_generator.chained_operators.append(p[1])


def p_level5(p):
    ''' level5 : level6
               | times_div_mod_op
               | negation_op '''


def p_negation_op(p):
    ''' negation_op : NOT level6 '''
    quadruple_generator.operate_unary(p[1], p.lexer.lineno)


def p_times_div_mod_op(p):
    ''' times_div_mod_op : level6 '*' level6 chained_times_div_mod_ops
                         | level6 '/' level6 chained_times_div_mod_ops
                         | level6 MOD level6 chained_times_div_mod_ops '''
    quadruple_generator.operate_left(p[2], p.lexer.lineno)


def p_chained_times_div_mod_ops(p):
    ''' chained_times_div_mod_ops : chained_times_div_mod_op
                                  | empty '''

def p_chained_times_div_mod_op(p):
    ''' chained_times_div_mod_op : '*' level6 chained_times_div_mod_ops
                                 | '/' level6 chained_times_div_mod_ops
                                 | MOD level6 chained_times_div_mod_ops '''
    quadruple_generator.chained_operators.append(p[1])


def p_level6(p):
    ''' level6 : '(' expression ')'
               | const
               | increment
               | decrement '''


def p_increment(p):
    ''' increment : INCREMENT variable_id '''
    quadruple_generator.operate_unary(p[1], p.lexer.lineno)


def p_decrement(p):
    ''' decrement : DECREMENT variable_id '''
    quadruple_generator.operate_unary(p[1], p.lexer.lineno)


def p_break(p):
    ''' break : BREAK '''
    quadruple_generator.generate_break(p.lexer.lineno)


def p_function_declaration(p):
    ''' function_declaration : function function_declaration
                             | empty'''


def p_function(p):
    '''function : create_scope parameters_and_variables statements '}' '''
    directory.end_definition(p.lexer.lineno)


def p_create_scope(p):
    ''' create_scope : FUN return_type ID '''
    directory.define_function(p[2], p[3], p.lexer.lineno)


def p_parameters_and_variables(p):
    ''' parameters_and_variables : '(' parameters ')' '{' variable_declaration '''
    directory.declare_variables(p[2], p[5], p.lexer.lineno)


def p_return_type(p):
    ''' return_type : type
                    | void '''
    p[0] = p[1]


def p_void(p):
    ''' void : VOID '''
    p[0] = p[1].upper()


def p_type(p):
    ''' type : INT
             | DEC
             | CHAR
             | STR
             | BOOL '''
    p[0] = Types[p[1].upper()]


def p_statements(p):
    ''' statements : statement ';' statements
                   | no_colon_statement statements
                   | empty'''


def p_statement(p):
    '''statement : call
                 | assignment
                 | special
                 | return
                 | increment
                 | decrement
                 | break '''


def p_no_colon_statement(p):
    ''' no_colon_statement : condition
                           | cycle '''


def p_call(p):
    ''' call : call_id '(' arguments ')' '''
    quadruple_generator.call(p[1], p.lexer.lineno)


def p_call_id(p):
    ''' call_id : ID '''
    quadruple_generator.init_call(p[1], p.lexer.lineno)


def p_arguments(p):
    ''' arguments : empty
                  | argument_list '''


def p_argument_list(p):
    ''' argument_list : expression
                      | expression ',' arguments '''
    quadruple_generator.read_parameter(p.lexer.lineno)


def p_assignment(p):
    ''' assignment : assignment_id '=' expression '''
    quadruple_generator.assign(p[1], p.lexer.lineno)


def p_condition(p):
    ''' condition : IF '(' expression if_quad ')' block optional_elses'''


def p_optional_elses(p):
    ''' optional_elses : elses
                       | add_pending_if '''


def p_if_quad(p):
    ''' if_quad : empty '''
    quadruple_generator.generate_boolean_structure(p.lexer.lineno, 'if')


def p_add_pending_if(p):
    ''' add_pending_if : empty '''
    quadruple_generator.add_pending_if()


def p_cycle(p):
    ''' cycle : WHILE '(' store_expression_position expression while_quad ')' block add_pending_while'''


def p_add_pending_while(p):
    ''' add_pending_while : empty '''
    quadruple_generator.add_pending_while()


def p_while_quad(p):
    ''' while_quad : empty '''
    quadruple_generator.generate_boolean_structure(p.lexer.lineno, 'while')


def p_store_expression_position(p):
    ''' store_expression_position : empty '''
    quadruple_generator.store_expression_position()


def p_special(p):
    ''' special : special_id '(' arguments ')' '''
    quadruple_generator.special_call(p[1], p.lexer.lineno)


def p_special_id(p):
    ''' special_id : SPECIAL_ID '''
    quadruple_generator.init_special(p[1], p.lexer.lineno)


def p_return(p):
    ''' return : RETURN expression '''
    quadruple_generator.generate_return(p.lexer.lineno)


def p_elses(p):
    ''' elses : elseif_else other_elses '''


def p_other_elses(p):
    ''' other_elses : elseif_else
                    | empty '''


def p_elseif_else(p):
    ''' elseif_else : else block add_pending_if
                    | elseif '(' expression if_quad ')' block optional_elses add_pending_if'''


def p_else(p):
    ''' else : ELSE '''
    quadruple_generator.add_else_jumps()


def p_elseif(p):
    ''' elseif : ELSEIF '''
    quadruple_generator.add_else_jumps()


def p_parameters(p):
    ''' parameters : all_parameters
                   | empty '''
    if p[1] is not None:
        p[0] = p[1]
    else:
        p[0] = []


def p_all_parameters(p):
    ''' all_parameters : parameter other_parameters '''
    if p[2]:
        p[2].append(p[1])
        p[0] = p[2]
    else:
        p[0] = [p[1]]


def p_other_parameters(p):
    ''' other_parameters : comma_separated_parameters
                         | empty '''
    if p[1] is not None:
        p[0] = p[1]
    else:
        p[0] = []


def p_comma_separated_parameters(p):
    ''' comma_separated_parameters : ',' parameter other_parameters '''
    if p[3]:
        p[3].append(p[2])
        p[0] = p[3]
    else:
        p[0] = [p[2]]


def p_parameter(p):
    'parameter : type ID'
    p[0] = (p[1], p[2])


def p_const(p):
    ''' const : variable_id
              | function_result
              | int_val
              | dec_val
              | char_val
              | str_val
              | bool_val '''


def p_int_val(p):
    ''' int_val : INT_VAL '''
    quadruple_generator.push_constant(Types.INT, p[1])
    p[0] = Types.INT, p[1]


def p_dec_val(p):
    ''' dec_val : DEC_VAL '''
    quadruple_generator.push_constant(Types.DEC, p[1])


def p_char_val(p):
    ''' char_val : CHAR_VAL '''
    quadruple_generator.push_constant(Types.CHAR, p[1])


def p_str_val(p):
    ''' str_val : STR_VAL '''
    quadruple_generator.push_constant(Types.STR, p[1])


def p_bool_val(p):
    ''' bool_val : BOOL_VAL '''
    quadruple_generator.push_constant(Types.BOOL, CONSTANT_VALS[p[1]])


def p_variable_id(p):
    ''' variable_id : usage_id '''
    quadruple_generator.operands.append((p[1][0], p[1][1]))


def p_function_result(p):
    ''' function_result : call
                        | special '''


def p_block(p):
    ''' block : '{' statements '}' '''


def p_error(p):
    raise GrammaticalError(p)


def create_parser(filepath):
    global quadruple_generator
    global directory
    quadruple_generator = QuadrupleGenerator(filepath)
    directory = Directory()
    return yacc()


def parse_file(path):
    parser = create_parser(path)

    with open(path) as file:
        parser.parse(file.read())

    with open(quadruple_generator.filepath) as file:
        constants = {type_: {address: value for value, address in
                             value_address.items()}
                     for type_, value_address in
                     quadruple_generator.CONSTANT_ADDRESS_DICT.items()}

        global directory
        return ''.join(play_note(file.read(), constants, directory))


if __name__ == "__main__":
    for file in argv[1:]:
        try:
            program_output = parse_file(file)
        except FileNotFoundError as e:
            print_red("File", file, "was not found. Skipping...")
        except Exception as e:
            print_red(f"ERROR in {file}: {str(e)}")
        else:
            print_green(file)
            print(program_output)
