from lexer import tokens, Types
from ply.yacc import yacc
from sys import exit


CUBE = [
    [
        [ [Types.INT.value] * 3 + [Types.DEC.value] + [Types.INT.value] * 2 + [Types.BOOL.value] * 5 ],
        [] * 3,
        [ [Types.DEC.value] * 6 + [Types.BOOL.value] * 5 ],
    ],
    [
        [ [Types.STR.value] + [] * 5 + [Types.BOOL.value] * 5 ],
        [ Types.STR.value ],
    ],
    [
        [ [] * 6 + [Types.BOOL.value] * 5 ],
    ],
    [
        [ [] * 6 + [Types.BOOL.value] * 8 ],
    ],
    [
        [ [Types.DEC.value] + [Types.BOOL.value] * 5 ],
    ],
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


    def clear():
        Directory.functions.clear()


    def clear_scope():
        Directory.functions[Directory.current_scope] = None


    def declare_variables(parameters, variables):
        for parameter in parameters:
            Directory.functions[Directory.current_scope].parameter_types.append(
                parameter[0])
            Directory._declare_variable(parameter[0], parameter[1])

        for variable in variables:
            Directory._declare_variable(variable[0], variable[1])


    def define_function(return_type, function):
        if function in Directory.functions:
            raise DeclarationError('Error: you are defining your "' + function
                                   + '" function more than once')

        Directory.current_scope = function
        Directory.functions[function] = FunctionScope(return_type, function)


    def _declare_variable(variable_type, variable):
        current_scope = Directory.current_scope
        current_function_vars = Directory.functions[current_scope].variables

        if variable in current_function_vars:
            raise DeclarationError('Error: you are declaring your "' + variable
                                   + '" variable more than once')

        current_function_vars[variable] = (
            variable,
            variable_type,
            # TODO: add code for storing array size
            None,
        )


class QuadrupleGenerator():
    operators = ['$']
    operands = []
    
    def operate():
        return
        right_operand = QuadrupleGenerator.operands.pop()
        left_operand = QuadrupleGenerator.operands.pop()
        operator = QuadrupleGenerator.operators.pop()
        
        try:
            CUBE[left_operand[0]][right_operand[0]][operator]
        except IndexError:
            raise OperandTypeError(f'Error: The {operator} operation cannot be \
            used for {left_operand[1]} (with type {left_operand[0]}) and \
            {right_operand[1]} (with type {right_operand[0]})')
        
        QuadrupleGenerator.generate_quad(operator, left_operand, right_operand)


class ParserError(Exception):
    def __init__(self, *args, **kwargs):
        Directory.clear()
        super().__init__(self, *args, **kwargs)


class GrammaticalError(ParserError):
    pass


class DeclarationError(ParserError):
    pass


class OperandTypeError(ParserError):
    pass


def p_program(p):
    ''' program : PROGRAM ID ';' create_global_scope function_declaration block '''
    Directory.clear()


def p_create_global_scope(p):
    ''' create_global_scope : variable_declaration '''
    Directory.define_function('VOID', Directory.GLOBAL_SCOPE)
    Directory.declare_variables([], p[1])


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
    ''' expression : level1 pop_exp
                   | level1 pop_exp push_exp '''


def p_pop_exp(p):
    ''' pop_exp : empty '''
    if QuadrupleGenerator.operators[-1] == '**':
        QuadrupleGenerator.operate()


def p_push_exp(p):
    ''' push_exp : EXPONENTIATION level1 '''
    QuadrupleGenerator.operators.append(p[1])


def p_level1(p):
    ''' level1 : level2
               | '+' level2
               | '-' level2'''


def p_level2(p):
    ''' level2 : level3 pop_binary
               | level3 pop_binary push_binary '''


def p_pop_binary(p):
    ''' pop_binary : empty '''
    if QuadrupleGenerator.operators[-1] == 'and' \
      or QuadrupleGenerator.operators[-1] == 'or':
        QuadrupleGenerator.operate()


def p_push_binary(p):
    ''' push_binary : OR level3
                    | AND level3 '''
    QuadrupleGenerator.operators.append(p[1])


def p_level3(p):
    ''' level3 : level4 pop_rel
               | level4 pop_rel push_rel '''


def p_pop_rel(p):
    ''' pop_rel : empty '''
    if QuadrupleGenerator.operators[-1] == '<' or QuadrupleGenerator.operators[-1] == '>' or QuadrupleGenerator.operators[-1] == '<=' \
    or QuadrupleGenerator.operators[-1] == '>=' or QuadrupleGenerator.operators[-1] == '==':
        QuadrupleGenerator.operate()


def p_push_rel(p):
    ''' push_rel : '<' level4
                 | '>' level4 
                 | LESS_EQUAL_THAN level4
                 | GREATER_EQUAL_THAN level4
                 | EQUALS level4 '''
    QuadrupleGenerator.operators.append(p[1])


def p_level4(p):
    ''' level4 : level5 pop_plus_minus
               | level5 pop_plus_minus push_plus_minus '''


def p_pop_plus_minus(p):
    ''' pop_plus_minus : empty '''
    if QuadrupleGenerator.operators[-1] == '+' or QuadrupleGenerator.operators[-1] == '-':
        QuadrupleGenerator.operate()


def p_push_plus_minus(p):
    ''' push_plus_minus : '+' level5
                        | '-' level5 '''
    QuadrupleGenerator.operators.append(p[1])


def p_level5(p):
    ''' level5 : level6 pop_times_div_mod
               | NOT level6
               | level6 pop_times_div_mod push_times_div_mod '''


def p_pop_times_div_mod(p):
    ''' pop_times_div_mod : empty '''
    if QuadrupleGenerator.operators[-1] == '*' or QuadrupleGenerator.operators[-1] == '/' or QuadrupleGenerator.operators[-1] == 'mod':
        QuadrupleGenerator.operate()


def p_push_times_div_mod(p):
    ''' push_times_div_mod : '*' level6
                           | '/' level6 
                           | MOD level6 '''
    QuadrupleGenerator.operators.append(p[1])


def p_level6(p):
    ''' level6 : '(' expression ')'
               | const
               | increment
               | decrement '''


def p_increment(p):
    ''' increment : INCREMENT id '''


def p_decrement(p):
    ''' decrement : DECREMENT id '''


def p_function_declaration(p):
    ''' function_declaration : function function_declaration
                             | empty'''


def p_function(p):
    '''function : create_scope parameters_and_variables statutes '}' ';' '''
    Directory.clear_scope()


def p_create_scope(p):
    ''' create_scope : FUN return_type ID '''
    Directory.define_function(p[2], p[3])


def p_parameters_and_variables(p):
    ''' parameters_and_variables : '(' parameters ')' '{' variable_declaration '''
    Directory.declare_variables(p[2], p[5])


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
    p[0] = p[1]


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


def p_expressions(p):
    ''' expressions : expression
                    | expression ',' expressions '''


def p_assignment(p):
    ''' assignment : id '=' expression '''


def p_condition(p):
    ''' condition : IF '(' expression ')' block elses '''


def p_cycle(p):
    ''' cycle : WHILE '(' expression ')' block '''


def p_special(p):
    ''' special : SPECIAL_ID '(' expressions ')' '''


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
    ''' const : id 
              | call
              | special
              | INT_VAL
              | DEC_VAL
              | CHAR_VAL
              | STR_VAL
              | BOOL_VAL '''


def p_block(p):
    ''' block : '{' statutes '}' '''


def p_error(p):
    raise GrammaticalError(p)


parser = yacc()
