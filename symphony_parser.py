from lexer import tokens, Types
from ply.yacc import yacc
from sys import exit


GLOBAL_SCOPE = None


class FunctionScope():
    current_scope = GLOBAL_SCOPE
    
    def __init__(self, name, return_type):
        self.name = name
        self.return_type = return_type
        self.variables = {}


function_directory = {}
function_directory[GLOBAL_SCOPE] = FunctionScope(None, 'VOID')


def p_program(p):
    ''' program : PROGRAM ID ';' variable_declaration function_declaration block '''
    function_directory[GLOBAL_SCOPE] = FunctionScope(None, 'VOID')


def p_empty(p):
    ''' empty : '''
    p[0] = None


def p_variable_declaration(p):
    ''' variable_declaration : variable_group variable_declaration
                             | empty '''
    pass


def p_variable_group(p):
    ''' variable_group : type declaration_ids ';' '''
    current_function = function_directory[FunctionScope.current_scope]
    variable_type = p[1]

    for variable in p[2]:
        if variable in current_function.variables:
            raise SemanticError('Error: you are declaring your ' + variable
                                + ' variable more than once ')

        current_function.variables[variable] = (
            variable,
            variable_type,
            # TODO: add code for storing array size when expressions are finished
            None, 
        )


def p_declaration_ids(p):
    ''' declaration_ids : id other_declaration_ids '''
    if not p[2]:
        p[0] = [p[1]]
    else:
        p[2].append(p[1])
        p[0] = p[2]
    

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
    FunctionScope.current_scope = p[3]
    
    if p[3] in function_directory:
        raise SemanticError('Error: you are declaring your "' + p[3] + '" function more than once')
    
    function_directory[p[3]] = FunctionScope(p[3], p[2])
    

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
    raise ParserError(p)


parser = yacc()


class ParserError(Exception):
    pass


class SemanticError(Exception):
    pass
