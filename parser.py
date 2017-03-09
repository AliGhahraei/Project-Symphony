from ply.yacc import yacc
from lexer import tokens


def p_program(t):
    ''' program : PROGRAM ID ';' variable_declaration function_declaration block '''
    pass


def p_empty(t):
    ''' empty : '''
    pass


def p_variable_declaration(t):
    ''' variable_declaration : variables other_variable_declarations '''
    pass


def p_other_variable_declarations(t):
    ''' other_variable_declarations : variable_declaration 
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


def p_expression(t):
    ''' expression : grouping
                   | const
                   | call '''


def p_grouping(t):
    ''' grouping : level1 
                 | level1 EXPONENTIATION level1 '''


def p_level1(t):
    ''' level1 : level2 
               | '+' level2 
               | '-' level2 '''


def p_level2(t):
    ''' level2 : level3 
               | level3 OR level3 
               | level3 AND level3 '''


def p_level3(t):
    ''' level3 : level4
               | level4 '<' level4
               | level4 '>' level4
               | level4 LESS_EQUAL_THAN level4
               | level4 GREATER_EQUAL_THAN level4
               | level4 EQUALS level4 '''


def p_level4(t):
    ''' level4 : level5
               | level5 '+' level5
               | level5 '-' level5 '''


def p_level5(t):
    ''' level5 : level6
               | level6 '*' level6
               | level6 '/' level6
               | level6 MOD level6
               |  '''


def p_level6(t):
    ''' level6 : '(' expression ')'
               | const
               | NOT const
               | INCREMENT const
               | DECREMENT const '''


def p_function_declaration(t):
    ''' function_declaration : function other_function_declarations '''
    pass


def p_other_function_declarations(t):
    ''' other_function_declarations : function_declaration 
                                    | empty '''
    pass


def p_function(t):
    '''function : FUN return_type ID '(' parameters ')' '{' variable_declaration statutes '}' ';' '''
    pass


def p_return_type(t):
    ''' return_type : type 
                    | VOID '''


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
    ''' call : ID '(' expressions ')' '''
    pass


def p_expressions(t):
    ''' expressions : expression
                    | expression ',' expressions '''


def p_assignment(t):
    ''' assignment : ID '=' expression ';'
                   | ID '[' expression ']' '=' expression ';' '''
    pass


def p_condition(t):
    ''' condition : IF '[' expression ']' block elses ';' '''


def p_cycle(t):
    ''' cycle : WHILE '(' expression ')' block ';' '''


def p_special(t):
    ''' special : SPECIAL_ID '(' expressions ')' '''


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


parser = yacc()

while True:
    input_string = input('Project Symphony > ')
    parser.parse(input_string)
