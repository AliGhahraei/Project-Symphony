#!/usr/bin/python

from collections import deque
from lexer import tokens, Types, OPERATORS, UNARY_OPERATORS, DUPLICATED_OPERATORS
from ply.yacc import yacc
from sys import exit, argv

from orchestra import generate_memory_addresses, play_note, SPECIAL_PARAMETER_TYPES


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
    def __init__(self, return_type, name):
        self.name = name
        self.return_type = return_type
        self.variables = {}
        self.parameter_types = deque()
        self.first_quadruple = None
        self.return_address = None


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

        # self.functions[self.current_scope] = None
        self.current_scope = Directory.GLOBAL_SCOPE
        quadruple_generator.generate_quad('ENDPROC')


    def declare_variables(self, parameters, variables, line_number,
                          is_global=False):
        self.functions[self.current_scope].first_quadruple = len(
            quadruple_generator.quadruples)

        for parameter in parameters:
            self.functions[self.current_scope].parameter_types.appendleft(
                parameter[0])
            self._declare_variable(parameter[0], parameter[1], is_global,
                                   line_number)

        for variable in variables:
            self._declare_variable(variable[0], variable[1], is_global,
                                   line_number)


    def define_function(self, return_type, function, line_number):
        if function in self.functions:
            raise RedeclarationError(f'Error on line {line_number}: you are'
                                     f' defining your {function} function more'
                                     f' than once')

        self.current_scope = function
        self.functions[function] = FunctionScope(return_type, function)


    def _declare_variable(self, variable_type, variable, is_global, line_number):
        current_function_vars = self.functions[self.current_scope].variables

        if variable in current_function_vars:
            raise RedeclarationError(f'Error on line {line_number}: you are '
                                     f'declaring your {variable} variable more'
                                     f' than once')

        current_function_vars[variable] = (
            variable_type,
            quadruple_generator.generate_variable_address(variable_type,
                                                          is_global),
            variable,
            # TODO: add code for storing array size
            None,
        )


    def get_variable(self, name, line_number):
        variable = None
        try:
            variable = self.functions[self.current_scope].variables[
                name]
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


    def operate(self, operator_symbol, line_number):
        right_type, right_address = self.operands.pop()
        left_type, left_address = self.operands.pop()

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


    def operate_unary(self, operator_symbol, line_number):
        type_, address = self.operands.pop()

        try:
            result_type = UNARY_TABLE[type_][UNARY_OPERATORS[operator_symbol]]
            if result_type == None:
                raise IndexError('Result is None')

            result_address = self.generate_temporal_address(result_type)

            if operator_symbol in DUPLICATED_OPERATORS:
                operator_symbol = DUPLICATED_OPERATORS[operator_symbol],

            self.generate_quad(operator_symbol, address, result_address)
            self.operands.append((result_type, result_address))
        except IndexError:
            raise TypeError(
                f'Error on line {line_number}: The {operator_symbol} operation'
                f' cannot be used for type {type_.name}')


    def generate_boolean_structure(self, line_number, structure_name):
        type_, address = self.operands.pop()

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
        self.quadruples[gotof_quad] += ' ' + str(len(self.quadruples))


    def add_else_jumps(self):
        pending_if_jump = self.pending_jumps.pop()
        self.pending_jumps.append(len(self.quadruples))
        self.generate_quad('GOTO')
        self.quadruples[pending_if_jump] += ' ' + str(len(self.quadruples))


    def assign(self, name, line_number):
        variable = directory.get_variable(name, line_number)
        result_type, result_address = self.operands.pop()
        if variable[0] == result_type:
            self.generate_quad('=', result_address, variable[1])
        else:
            raise TypeError(f'Error on line {line_number}: you are trying '
                            f'to assign a(n) {result_type.name} value to '
                            f'a(n) {variable[0].name} type')


    def generate_quad(self, *args):
        self.quadruples.append(' '.join(str(arg) for arg in args))


    def read_parameter(self):
        self.arguments.appendleft(self.operands.pop())


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
            result_address = self.generate_temporal_address(
                called_function.return_type)
            self.operands.append((called_function.return_type, result_address))
            self.generate_quad('=', called_function.return_address, result_address)


    def special_call(self, function):
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


    def generate_variable_address(self, variable_type, is_global):
        new_address = None

        if is_global:
            new_address = self.ADDRESSES.global_[variable_type]

            self.ADDRESSES.global_[variable_type] = new_address + 1
        else:
            new_address = self.ADDRESSES.local[variable_type]
            self.ADDRESSES.local[variable_type] = new_address + 1

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

        self.generate_quad('ERA', function)
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

        return_type, return_address = self.operands.pop()
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
    ''' program : PROGRAM ID ';' global_declarations function_declaration block '''
    finalize()


def p_global_declarations(p):
    ''' global_declarations : variable_declaration '''
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
    ''' declaration_ids : id other_declaration_ids '''
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


def p_id(p):
    ''' id : ID
           | ID '[' expression ']' '''
    p[0] = p[1]
    # TODO: add code for array size


def p_expression(p):
    ''' expression : level1
                   | exp_op '''


def p_exp_op(p):
    ''' exp_op : level1 EXPONENTIATION level1 '''
    quadruple_generator.operate(p[2], p.lexer.lineno)


def p_level1(p):
    ''' level1 : level2
               | plus_minus_op '''


def p_plus_minus_op(p):
    ''' plus_minus_op : '+' level2
                      | '-' level2 '''
    quadruple_generator.operate_unary(p[1], p.lexer.lineno)


def p_level2(p):
    ''' level2 : level3
               | binary_op '''


def p_binary_op(p):
    ''' binary_op : level3 OR level3
                  | level3 AND level3 '''
    quadruple_generator.operate(p[2], p.lexer.lineno)


def p_level3(p):
    ''' level3 : level4
               | rel_op '''


def p_rel_op(p):
    ''' rel_op : level4 '<' level4
               | level4 '>' level4
               | level4 LESS_EQUAL_THAN level4
               | level4 GREATER_EQUAL_THAN level4
               | level4 EQUALS level4 '''
    quadruple_generator.operate(p[2], p.lexer.lineno)


def p_level4(p):
    ''' level4 : level5
               | add_subs_op '''


def p_add_subs_op(p):
    ''' add_subs_op : level5 '+' level5
                    | level5 '-' level5 '''
    quadruple_generator.operate(p[2], p.lexer.lineno)


def p_level5(p):
    ''' level5 : level6
               | times_div_mod_op
               | negation_op '''


def p_negation_op(p):
    ''' negation_op : NOT level6 '''
    quadruple_generator.operate_unary(p[1], p.lexer.lineno)


def p_times_div_mod_op(p):
    ''' times_div_mod_op : level6 '*' level6
                         | level6 '/' level6
                         | level6 MOD level6 '''
    quadruple_generator.operate(p[2], p.lexer.lineno)


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


def p_function_declaration(p):
    ''' function_declaration : function function_declaration
                             | empty'''


def p_function(p):
    '''function : create_scope parameters_and_variables statements '}' ';' '''
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
                 | empty'''


def p_statement(p):
    '''statement : call
                 | assignment
                 | condition
                 | cycle
                 | special
                 | return
                 | increment
                 | decrement '''


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
    quadruple_generator.read_parameter()


def p_assignment(p):
    ''' assignment : id '=' expression '''
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
    quadruple_generator.special_call(p[1])


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
    quadruple_generator.push_constant(Types.BOOL, p[1])


def p_variable_id(p):
    ''' variable_id : id '''
    variable = directory.get_variable(p[1], p.lexer.lineno)
    quadruple_generator.operands.append((variable[0], variable[1]))


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


if __name__ == "__main__":
    for path in argv[1:]:
        parser = create_parser(path)

        try:
            with open(path) as file:
                parser.parse(file.read())

            with open(quadruple_generator.filepath) as file:
                constants = {type_: {address: value for value, address in
                                     value_address.items()}
                             for type_, value_address in
                             quadruple_generator.CONSTANT_ADDRESS_DICT.items()}

                play_note(file.read(), constants)
        except FileNotFoundError:
            print("The file", path, "was not found. Skipping...")
