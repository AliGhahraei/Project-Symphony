from lexer import tokens, Types
from ply.yacc import yacc
from sys import exit


functions_directory = {}
global_scope = None


class FunctionScope():
    def __init__(self, name, return_type):
        self.name = name
        self.return_type = return_type
        self.variables = {}


def p_program(p):
    ''' program : PROGRAM ID ';' variable_declaration function_declaration block '''
    global_scope = FunctionScope(p[2], 'VOID')


def p_empty(p):
    ''' empty : '''
    pass


def p_variable_declaration(p):
    ''' variable_declaration : type ids ';' variable_declaration
                             | empty '''
    pass


def p_ids(p):
    ''' ids : id other_ids '''
    pass
    

def p_other_ids(p):
    ''' other_ids : ',' ids 
                  | empty '''
    pass


def p_id(p):
    ''' id : ID 
           | ID '[' expression ']' '''
    pass


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


def p_decrement(p):
    ''' decrement : DECREMENT id '''


def p_function_declaration(p):
    ''' function_declaration : function function_declaration
                             | empty'''
    pass


def p_function(p):
    '''function : FUN return_type ID '(' parameters ')' '{' variable_declaration statutes '}' ';' '''
    pass


def p_return_type(p):
    ''' return_type : type 
                    | VOID '''
    pass


def p_type(p):
    ''' type : INT 
             | DEC 
             | CHAR 
             | STR 
             | BOOL '''
    pass


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


def p_elses(p):
    ''' elses : empty
              | ELSE block
              | ELSEIF '(' expression ')' block elses '''
    pass


def p_parameters(p):
    ''' parameters : type ID other_parameters
                   | empty '''
    pass


def p_other_parameters(p):
    ''' other_parameters : ',' type ID other_parameters
                         | empty '''
    pass


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
    raise ParserException


parser = yacc()


class ParserException(Exception):
    pass
