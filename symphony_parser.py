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

directory = None
quadruple_generator = None


class FunctionScope():
    def __init__(self, return_type, name):
        self.name = name
        self.return_type = return_type
        self.variables = {}
        self.parameter_types = []
        self.first_quadruple = None


class Directory():
    GLOBAL_SCOPE = None

    def __init__(self):
        self.current_scope = None
        self.functions = {}
        self.define_function('VOID', Directory.GLOBAL_SCOPE, 0)


    def clear_scope(self):
        self.functions[self.current_scope] = None
        self.current_scope = Directory.GLOBAL_SCOPE
        quadruple_generator.generate_quad('ENDPROC')


    def declare_variables(self, parameters, variables, line_number,
                          is_global=False):
        self.functions[self.current_scope].first_quadruple = len(
            quadruple_generator.quadruples)
        
        for parameter in parameters:
            self.functions[self.current_scope].parameter_types.append(
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
                raise UndeclaredError(f'Error on line {line_number}: You tried'
                                      f' to use the variable {name}, but it was'
                                      f' not declared beforehand. Check if you'
                                      f' wrote the name correctly and if you are'
                                      f' trying to use a variable defined inside'
                                      f' another function')
        return variable


class QuadrupleGenerator():
    def __init__(self, filepath):
        self.filepath = filepath
        self.operands = []
        self.CONSTANT_ADDRESS_DICT = {type_: {} for type_ in Types}
        self.quadruples = []
        self.pending_jumps = []

        sector_iterator = iter(MEMORY_SECTORS)
        current_address = sector_iterator.__next__()[1]
        self.ADDRESSES = []
        for sector in sector_iterator:
            next_address = sector[1]
            sector_size = next_address - current_address

            type_addresses = [starting_address for starting_address in
                              range(current_address, next_address,
                                    int((sector_size) / len(Types)))]
            type_addresses = dict(zip(Types, type_addresses))

            self.ADDRESSES.append(type_addresses)
            current_address = next_address
        self.ADDRESSES = ADDRESS_TUPLE._make(self.ADDRESSES)


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
            self.generate_quad(operator_symbol, address,
                               result_address)
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
                f'{structure_name} must receive a boolean inside its '
                f'parenthesis, but a {type_.value} was found.')

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
                                 f'to assign a {result_type} value to a '
                                 f'{variable[0]} type')


    def generate_quad(self, *args):
        self.quadruples.append(' '.join(str(arg) for arg in args))


    def call(self, function):
        self.operands.pop()


    def special_call(self, function):
        self.operands.pop()
    

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
        with open(self.filepath[:-4] + '.note', 'w') as file:
            file.write('\n'.join(self.quadruples) + '\n')


    def store_expression_position(self):
        self.pending_jumps.append(len(self.quadruples))


class GrammaticalError(Exception):
    pass


class RedeclarationError(Exception):
    pass


class UndeclaredError(Exception):
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
    '''function : create_scope parameters_and_variables statutes '}' ';' '''
    directory.clear_scope()


def p_create_scope(p):
    ''' create_scope : FUN return_type ID '''
    directory.define_function(p[2], p[3], p.lexer.lineno)


def p_parameters_and_variables(p):
    ''' parameters_and_variables : '(' parameters ')' '{' variable_declaration '''
    directory.declare_variables(p[2], p[5], p.lexer.lineno)


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
    ''' call : init_call '(' expressions ')' '''
    quadruple_generator.call(p[1])


def p_init_call(p):
    ''' init_call : ID '''
#    directory.init_call(p[1])


def p_expressions(p):
    ''' expressions : expression
                    | expression ',' expressions '''


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
    ''' special : SPECIAL_ID '(' expressions ')' '''
    quadruple_generator.special_call(p[1])


def p_return(p):
    ''' return : RETURN expression
               | RETURN '''


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
    ''' block : '{' statutes '}' '''


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
        except FileNotFoundError:
            print("The file", path, "was not found")
