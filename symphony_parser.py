#!/usr/bin/python

from lexer import tokens, Types, OPERATORS, UNARY_OPERATORS
from ply.yacc import yacc
from sys import exit, argv

from orchestra import MEMORY_SECTORS, ADDRESS_TUPLE


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
        [None] * 6 + [Types.BOOL] * 5,
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


class FunctionScope():    
    def __init__(self, return_type, name):
        self.name = name
        self.return_type = return_type
        self.variables = {}
        self.parameter_types = []


class Directory():
    GLOBAL_SCOPE = None
    current_scope = None
    functions = {}
    

    def initialize():
        Directory.define_function('VOID', Directory.GLOBAL_SCOPE, 0)


    def clear():
        Directory.functions.clear()


    def clear_scope():
        Directory.functions[Directory.current_scope] = None
        Directory.current_scope = Directory.GLOBAL_SCOPE


    def declare_variables(parameters, variables, line_number, is_global=False):
        for parameter in parameters:
            Directory.functions[Directory.current_scope].parameter_types.append(
                parameter[0])
            Directory._declare_variable(parameter[0], parameter[1], is_global,
                                        line_number)

        for variable in variables:
            Directory._declare_variable(variable[0], variable[1], is_global,
                                        line_number)


    def define_function(return_type, function, line_number):
        if function in Directory.functions:
            raise RedeclarationError(f'Error on line {line_number}: you are'
                                     f' defining your {function} function more'
                                     f' than once')

        Directory.current_scope = function
        Directory.functions[function] = FunctionScope(return_type, function)


    def _declare_variable(variable_type, variable, is_global, line_number):
        current_scope = Directory.current_scope
        current_function_vars = Directory.functions[current_scope].variables

        if variable in current_function_vars:
            raise RedeclarationError(f'Error on line {line_number}: you are '
                                     f'declaring your {variable} variable more'
                                     f' than once')

        current_function_vars[variable] = (
            variable_type,
            QuadrupleGenerator.generate_variable_address(variable_type,
                                                         is_global),
            variable,
            # TODO: add code for storing array size
            None,
        )


    def get_variable(name, line_number):
        variable = None
        try:
            variable = Directory.functions[Directory.current_scope].variables[
                name]
        except KeyError:
            try:
                variable = Directory.functions[Directory.GLOBAL_SCOPE].variables[
                name]
            except KeyError:
                raise UndeclaredError(f'Error on line {line_number}: You tried'
                                      f' to use the variable {name}, but it was'
                                      f' not declared beforehand. Check if you'
                                      f' wrote the name correctly and if you are'
                                      f' trying to use a variable defined inside'
                                      f' another function')
        return variable


class QuadrupleGenerator():
    operands = []
    ADDRESSES = None
    CONSTANT_ADDRESS_DICT = {type_: {} for type_ in Types}


    def initialize():
        sector_iterator = iter(MEMORY_SECTORS)
        current_address = sector_iterator.__next__()[1]
        QuadrupleGenerator.ADDRESSES = []
        for sector in sector_iterator:
            next_address = sector[1]
            sector_size = next_address - current_address

            type_addresses = [starting_address for starting_address in
                              range(current_address, next_address,
                                    int((sector_size) / len(Types)))]
            type_addresses = dict(zip(Types, type_addresses))

            QuadrupleGenerator.ADDRESSES.append(type_addresses)
            current_address = next_address

        QuadrupleGenerator.ADDRESSES = ADDRESS_TUPLE._make(
            QuadrupleGenerator.ADDRESSES)


    def clear():
        QuadrupleGenerator.operands.clear()
        ADDRESSES = None
        CONSTANT_ADDRESS_DICT = {type_: None for type_ in Types}


    def operate(operator_symbol, line_number):
        right_type, right_address = QuadrupleGenerator.operands.pop()
        left_type, left_address = QuadrupleGenerator.operands.pop()

        try:
            result_type = CUBE[left_type][right_type][OPERATORS[operator_symbol]]
            if(result_type == None):
                raise IndexError('Result is None')
            
            result_address = QuadrupleGenerator.generate_temporal_address(
                result_type)
            
            QuadrupleGenerator.generate_quad(operator_symbol, left_address,
                                             right_address, result_address)
            QuadrupleGenerator.operands.append((result_type, result_address))
        except IndexError:
            raise OperandTypeError(
                f'Error on line {line_number}: The {operator_symbol} operation'
                f' cannot be used for types {left_type.name} and '
                f'{right_type.name}')


    def operate_unary(operator_symbol, line_number):
        type_, address = QuadrupleGenerator.operands.pop()

        try:
            result_type = UNARY_TABLE[type_][UNARY_OPERATORS[operator_symbol]]
            if(result_type == None):
                raise IndexError('Result is None')
            
            result_address = QuadrupleGenerator.generate_temporal_address(
                result_type)
            QuadrupleGenerator.generate_quad(operator_symbol, address,
                                             result_address)
            QuadrupleGenerator.operands.append((result_type, result_address))
        except IndexError:
            raise OperandTypeError(
                f'Error on line {line_number}: The {operator_symbol} operation'
                f' cannot be used for type {type_.name}')


    def assign(name, line_number):
        variable = Directory.get_variable(name, line_number)
        result_type, result_address = QuadrupleGenerator.operands.pop()
        if variable[0] == result_type:
            QuadrupleGenerator.generate_quad('=', result_address, variable[1])


    def generate_quad(operation, operand1, operand2, operand3=None):
        pass


    def call(function):
        QuadrupleGenerator.operands.pop()

    
    def generate_variable_address(variable_type, is_global):
        new_address = None
        
        if is_global:
            new_address = QuadrupleGenerator.ADDRESSES.global_[variable_type]
            QuadrupleGenerator.ADDRESSES.global_[variable_type] = new_address + 1
        else:
            new_address = QuadrupleGenerator.ADDRESSES.local[variable_type] 
            QuadrupleGenerator.ADDRESSES.local[variable_type] = new_address + 1

        return new_address


    def push_constant(type_, value):
        try:
            address = QuadrupleGenerator.CONSTANT_ADDRESS_DICT[type_][value]
        except KeyError:
            address = QuadrupleGenerator.ADDRESSES.constant[type_]
            QuadrupleGenerator.ADDRESSES.constant[type_] = address + 1

            QuadrupleGenerator.CONSTANT_ADDRESS_DICT[type_][value] = address

        QuadrupleGenerator.operands.append((type_, address))


    def generate_temporal_address(variable_type):
        new_address = QuadrupleGenerator.ADDRESSES.temporal[variable_type]
        QuadrupleGenerator.ADDRESSES.temporal[variable_type] = new_address + 1
        return new_address


class ParserError(Exception):
    def __init__(self, *args, **kwargs):
        clear()
        super().__init__(self, *args, **kwargs)


class GrammaticalError(ParserError):
    pass


class RedeclarationError(ParserError):
    pass


class OperandTypeError(ParserError):
    pass


class UndeclaredError(ParserError):
    pass


def clear():
    Directory.clear()
    QuadrupleGenerator.clear()


def p_program(p):
    ''' program : PROGRAM ID ';' create_global_scope function_declaration block '''
    clear()


def p_create_global_scope(p):
    ''' create_global_scope : variable_declaration '''
    QuadrupleGenerator.initialize()
    Directory.initialize()
    Directory.declare_variables([], p[1], p.lexer.lineno, is_global=True)


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
    QuadrupleGenerator.operate(p[2], p.lexer.lineno)


def p_level1(p):
    ''' level1 : level2
               | plus_minus_op '''


def p_plus_minus_op(p):
    ''' plus_minus_op : '+' level2
                      | '-' level2 '''
    QuadrupleGenerator.operate_unary(p[1], p.lexer.lineno)


def p_level2(p):
    ''' level2 : level3
               | binary_op '''


def p_binary_op(p):
    ''' binary_op : level3 OR level3
                  | level3 AND level3 '''
    QuadrupleGenerator.operate(p[2], p.lexer.lineno)


def p_level3(p):
    ''' level3 : level4 
               | rel_op '''


def p_rel_op(p):
    ''' rel_op : level4 '<' level4
               | level4 '>' level4 
               | level4 LESS_EQUAL_THAN level4
               | level4 GREATER_EQUAL_THAN level4
               | level4 EQUALS level4 '''
    QuadrupleGenerator.operate(p[2], p.lexer.lineno)


def p_level4(p):
    ''' level4 : level5
               | add_subs_op '''


def p_add_subs_op(p):
    ''' add_subs_op : level5 '+' level5
                    | level5 '-' level5 '''
    QuadrupleGenerator.operate(p[2], p.lexer.lineno)


def p_level5(p):
    ''' level5 : level6
               | times_div_mod_op 
               | negation_op '''


def p_negation_op(p):
    ''' negation_op : NOT level6 '''
    QuadrupleGenerator.operate_unary(p[1], p.lexer.lineno)


def p_times_div_mod_op(p):
    ''' times_div_mod_op : level6 '*' level6
                         | level6 '/' level6 
                         | level6 MOD level6 '''
    QuadrupleGenerator.operate(p[2], p.lexer.lineno)


def p_level6(p):
    ''' level6 : '(' expression ')'
               | const
               | increment
               | decrement '''


def p_increment(p):
    ''' increment : INCREMENT variable_id '''
    QuadrupleGenerator.operate_unary(p[1], p.lexer.lineno)


def p_decrement(p):
    ''' decrement : DECREMENT variable_id '''
    QuadrupleGenerator.operate_unary(p[1], p.lexer.lineno)


def p_function_declaration(p):
    ''' function_declaration : function function_declaration
                             | empty'''


def p_function(p):
    '''function : create_scope parameters_and_variables statutes '}' ';' '''
    Directory.clear_scope()


def p_create_scope(p):
    ''' create_scope : FUN return_type ID '''
    Directory.define_function(p[2], p[3], p.lexer.lineno)


def p_parameters_and_variables(p):
    ''' parameters_and_variables : '(' parameters ')' '{' variable_declaration '''
    Directory.declare_variables(p[2], p[5], p.lexer.lineno)


def p_return_type(p):
    ''' return_type : type 
                    | VOID '''
    p[0] = p[1]


def p_type(p):
    ''' type : INT 
             | DEC 
             | CHAR 
             | STR 
             | BOOL '''
    p[0] = Types[p[1].upper()]


def p_statutes(p):
    ''' statutes : statute ';' statutes
                 | empty'''


def p_statute(p):
    '''statute   : call
                 | assignment
                 | condition
                 | cycle 
                 | special 
                 | return
                 | increment
                 | decrement '''


def p_call(p):
    ''' call : ID '(' expressions ')' '''
    QuadrupleGenerator.call(p[1])


def p_expressions(p):
    ''' expressions : expression
                    | expression ',' expressions '''


def p_assignment(p):
    ''' assignment : id '=' expression '''
    QuadrupleGenerator.assign(p[1], p.lexer.lineno)


def p_condition(p):
    ''' condition : IF '(' expression ')' block elses '''


def p_cycle(p):
    ''' cycle : WHILE '(' expression ')' block '''


def p_special(p):
    ''' special : SPECIAL_ID '(' expressions ')' '''
    QuadrupleGenerator.call(p[1])


def p_return(p):
    ''' return : RETURN expression
               | RETURN '''


def p_elses(p):
    ''' elses : empty
              | ELSE block
              | ELSEIF '(' expression ')' block elses '''


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
    QuadrupleGenerator.push_constant(Types.INT, p[1])


def p_dec_val(p):
    ''' dec_val : DEC_VAL '''
    QuadrupleGenerator.push_constant(Types.DEC, p[1])


def p_char_val(p):
    ''' char_val : CHAR_VAL '''
    QuadrupleGenerator.push_constant(Types.CHAR, p[1])


def p_str_val(p):
    ''' str_val : STR_VAL '''
    QuadrupleGenerator.push_constant(Types.STR, p[1])


def p_bool_val(p):
    ''' bool_val : BOOL_VAL '''
    QuadrupleGenerator.push_constant(Types.BOOL, p[1])


def p_variable_id(p):
    ''' variable_id : id '''
    variable = Directory.get_variable(p[1], p.lexer.lineno)
    QuadrupleGenerator.operands.append((variable[0], variable[1]))


def p_function_result(p):
    ''' function_result : call
                        | special '''


def p_block(p):
    ''' block : '{' statutes '}' '''


def p_error(p):
    raise GrammaticalError(p)


def create_parser():
    return yacc()


if __name__ == "__main__":
    parser = create_parser()

    for path in argv[1:]:
        try:
            with open(path) as file:
                parser.parse(file.read())
        except FileNotFoundError:
            print("The file", path, "was not found")
