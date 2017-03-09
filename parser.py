from ply.yacc import yacc
from lexer import tokens
from sys import exit


def p_program(t):
    ''' program : PROGRAM ID ';' variable_declaration function_declaration block '''
    pass


def p_empty(t):
    ''' empty : '''
    pass


def p_variable_declaration(t):
    ''' variable_declaration : variables variable_declaration 
                             | empty '''
    pass


def p_variables(t):
    ''' variables : type ids ';' '''
    pass


def p_ids(t):
    ''' ids : id other_ids '''
    pass
    

def p_other_ids(t):
    ''' other_ids : ',' ids 
                  | empty '''
    pass


def p_id(t):
    ''' id : ID 
           | ID '[' expression ']' '''
    pass


def p_expression(t):
    ''' expression : level1 
                   | level1 EXPONENTIATION level1  '''
    pass


def p_level1(t):
    ''' level1 : level2 
               | '+' level2
               | '-' level2'''
    pass


def p_level2(t):
    ''' level2 : level3 
               | level3 OR level3 
               | level3 AND level3 '''
    pass


def p_level3(t):
    ''' level3 : level4
               | level4 '<' level4
               | level4 '>' level4
               | level4 LESS_EQUAL_THAN level4
               | level4 GREATER_EQUAL_THAN level4
               | level4 EQUALS level4 '''
    pass


def p_level4(t):
    ''' level4 : level5
               | level5 '+' level5
               | level5 '-' level5'''
    pass


def p_level5(t):
    ''' level5 : level6
               | level6 '*' level6
               | level6 '/' level6
               | level6 MOD level6
               |  '''
    pass


def p_level6(t):
    ''' level6 : '(' expression ')'
               | const
               | NOT const
               | INCREMENT const
               | DECREMENT const 
               | call
               | NOT call
               | INCREMENT call
               | DECREMENT call'''
    pass


def p_function_declaration(t):
    ''' function_declaration : function function_declaration
                             | empty'''
    pass


def p_function(t):
    '''function : FUN return_type ID '(' parameters ')' '{' variable_declaration statutes '}' ';' '''
    pass


def p_return_type(t):
    ''' return_type : type 
                    | VOID '''
    pass


def p_type(t):
    ''' type : INT 
             | DEC 
             | CHAR 
             | STR 
             | BOOL '''
    pass


def p_statutes(t):
    ''' statutes : call
                 | assignment
                 | condition
                 | cycle 
                 | special '''
    pass


def p_call(t):
    ''' call : ID '(' expressions ')' ';' '''
    pass


def p_expressions(t):
    ''' expressions : expression
                    | expression ',' expressions '''
    pass


def p_assignment(t):
    ''' assignment : ID '=' expression ';'
                   | ID '[' expression ']' '=' expression ';' '''
    pass


def p_condition(t):
    ''' condition : IF '(' expression ')' block elses ';' '''
    pass


def p_cycle(t):
    ''' cycle : WHILE '(' expression ')' block ';' '''
    pass


def p_special(t):
    ''' special : SPECIAL_ID '(' expressions ')' ';' '''
    pass


def p_elses(t):
    ''' elses : empty
              | ELSE block
              | ELSEIF '(' expression ')' block elses '''
    pass


def p_parameters(t):
    ''' parameters : type ID other_parameters'''
    pass


def p_other_parameters(t):
    ''' other_parameters : ',' parameters 
                         | empty '''
    pass

def p_const(t):
    ''' const : id 
              | INT 
              | DEC '''
    pass


def p_block(t):
    ''' block : '{' statutes '}' '''
    pass


def p_error(t):
    print(t.value)


parser = yacc()

while True:
    try:
        input_string = input('Project Symphony > ')
        parser.parse(input_string)
    except(EOFError, KeyboardInterrupt):
        print('Bye!')
        exit(0)
