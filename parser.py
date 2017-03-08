from ply.yacc import yacc
from lexer import tokens


def p_empty(t):
    ''' empty : '''
    pass


def p_program(t):
    ''' program : PROGRAM ID ; variable_declaration function_declaration 
    block '''
    pass


def p_variable_declaration(t):
    ''' variable_declaration : variables other_variable_declarations '''
    pass


def p_other_variable_declarations(t):
    ''' other_variable_declarations : variable_declaration | empty '''
    pass


def p_variables(t):
    ''' variables : type ids ';' '''
    pass


def p_ids(t):
    ''' ids : id other_ids '''
    pass
    

def p_other_ids(t):
    ''' other_ids : ',' ids | empty '''
    pass


def p_id(t):
    ''' id : ID | ID '[' const ']' '''


def p_function_declaration(t):
    ''' function_declaration : function other_function_declarations '''
    pass


def p_other_function_declarations(t):
    ''' other_function_declarations : function_declaration | empty '''
    pass


def p_function(t):
    '''function : FUN return_type ID '(' parameters ')' '{' function_variables
    statutes '}' ';' '''
    pass


def p_return_type(t):
    ''' return_type : type | VOID '''


def p_type(t):
    ''' type : INT | DEC | CHAR | STR | BOOL '''
    pass


def p_statutes(t):
    pass


def p_parameters(t):
    pass


def p_function_variables(t):
    pass


def p_const(t):
    pass


def p_block(t):
    pass


parser = yacc()

while True:
    input_string = input('Project Symphony > ')
    parser.parse(input_string)
