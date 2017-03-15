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
        [ [Types.DEC.value] + [Types.BOOL.value] * 5],
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
    functions = {}

    def clear():
        Directory.functions.clear()


    def clear_scope():
        Directory.functions[Directory.scope] = None


    def declare(variable_type, variable):
        current_function_vars = Directory.functions[Directory.scope].variables

        if variable in current_function_vars:
            raise SemanticError('Error: you are declaring your ' + variable
                                + ' variable more than once ')

        current_function_vars[variable] = (
            variable,
            variable_type,
            # TODO: add code for storing array size
            None,
        )


    def define(return_type, function, parameters, variable_declarations):
        if function in Directory.functions:
            raise SemanticError('Error: you are declaring your "' + function
                                + '" function more than once')

        Directory.scope = function
        Directory.functions[function] = FunctionScope(return_type, function)

        for parameter in parameters:
            Directory.functions[function].parameter_types.append(parameter[0])
            Directory.declare(parameter[0], parameter[1])


        for variable in variable_declarations:
            Directory.declare(variable[0], variable[1])


def p_program(p):
    ''' program : PROGRAM ID ';' variable_declaration function_declaration block '''
    Directory.define('VOID', None, [], p[4])
    Directory.clear()


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
                   | level1 EXPONENTIATION level1  '''
    pass


def p_level1(p):
    ''' level1 : level2 
               | '+' level2
               | '-' level2'''
    pass


def p_level2(p):
    ''' level2 : level3 
               | level3 OR level3 
               | level3 AND level3 '''
    pass


def p_level3(p):
    ''' level3 : level4
               | level4 '<' level4
               | level4 '>' level4
               | level4 LESS_EQUAL_THAN level4
               | level4 GREATER_EQUAL_THAN level4
               | level4 EQUALS level4 '''
    pass


def p_level4(p):
    ''' level4 : level5
               | level5 '+' level5
               | level5 '-' level5 '''
    pass


def p_level5(p):
    ''' level5 : level6
               | NOT level6
               | level6 '*' level6
               | level6 '/' level6
               | level6 MOD level6 '''
    pass


def p_level6(p):
    ''' level6 : '(' expression ')'
               | const
               | increment
               | decrement '''
    pass


def p_increment(p):
    ''' increment : INCREMENT id '''
    pass


def p_decrement(p):
    ''' decrement : DECREMENT id '''
    pass


def p_function_declaration(p):
    ''' function_declaration : function function_declaration
                             | empty'''
    pass


def p_function(p):
    '''function : FUN return_type ID '(' parameters ')' '{' variable_declaration statutes '}' ';' '''
    Directory.define(p[2], p[3], p[5], p[8])
    Directory.clear_scope()
    

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
    pass


def p_statute(p):
    '''statute   : call
                 | assignment
                 | condition
                 | cycle 
                 | special 
                 | return
                 | increment
                 | decrement '''
    pass


def p_call(p):
    ''' call : ID '(' expressions ')' '''
    pass


def p_expressions(p):
    ''' expressions : expression
                    | expression ',' expressions '''
    pass


def p_assignment(p):
    ''' assignment : id '=' expression '''
    pass


def p_condition(p):
    ''' condition : IF '(' expression ')' block elses '''
    pass


def p_cycle(p):
    ''' cycle : WHILE '(' expression ')' block '''
    pass


def p_special(p):
    ''' special : SPECIAL_ID '(' expressions ')' '''
    pass


def p_return(p):
    ''' return : RETURN expression
               | RETURN '''
    pass


def p_elses(p):
    ''' elses : empty
              | ELSE block
              | ELSEIF '(' expression ')' block elses '''
    pass


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
    pass


def p_block(p):
    ''' block : '{' statutes '}' '''
    pass


def p_error(p):
    raise GrammaticalError(p)


parser = yacc()


class ParserError(Exception):
    def __init__(self, *args, **kwargs):
        Directory.clear()
        super().__init__(self, *args, **kwargs)


class GrammaticalError(ParserError):
    pass


class SemanticError(ParserError):
    pass
