from ply.lex import lex


tokens = (
    'INT', 'DEC', 'CHAR', 'STR', 'BOOLEAN', 'VOID', 'COMMA', 'SEMICOLON',
    'LEFT_PARENTHESIS', 'RIGHT_PARENTHESIS', 'LEFT_BRACKET', 'RIGHT_BRACKET',
    'LEFT_SQUARE_BRACKET', 'RIGHT_SQUARE_BRACKET', 'ASSIGNMENT', 'PLUS',
    'MINUS', 'MULTIPLICATION', 'DIVISION', 'EXPONENTIATION', 'INCREMENT',
    'DECREMENT', 'MODULUS', 'EQUALS', 'GREATER_THAN', 'LESS_THAN',
    'GREATER_EQUAL_THAN', 'LESS_EQUAL_THAN', 'AND', 'OR', 'NOT', 'FUN', 'WHILE',
    'IF', 'ELSE', 'ELSEIF', 'SINGLE_LINE_COMMENT', 'ID', 'IDS_AND_KEYWORDS',
)


keywords_named_as_types = ['void', 'equals', 'and', 'or', 'not', 'fun', 'while',
                          'if', 'else', 'elseif']
keywords_to_types = {keyword: keyword.upper()
                     for keyword in keywords_named_as_types}
keywords_to_types.update({keyword: 'BOOLEAN' for keyword in ['true', 'false']})


def t_IDS_AND_KEYWORDS(t):
    r'[a-zA-Z_][0-9a-zA-Z_]*'
    if t.value in keywords_to_types:
        t.type = keywords_to_types[t.value]
    else:
        t.type = 'ID'
    return t

def t_DEC(t):
    r'[+-]?[0-9]*\.[0-9]+'
    t.value = float(t.value)
    return t


def t_INT(t):
    r'[-+]?[0-9]+'
    t.value = int(t.value)
    return t


def t_CHAR(t):
    r"\'[^']\'"
    t.value = t.value[1:-1]
    return t


def t_STR(t):
    r'\"[^"]*\"'
    t.value = t.value[1:-1]
    return t


def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)


def t_error(t):
    print("The system found a problem with how you typed your program, so "
          + "please find the character sequence '" + t.value[0] + "' on line "
          + str(t.lexer.lineno) + " and correct it.")
    t.lexer.skip(1)

"""
def t_SINGLE_LINE_COMMENT(t):

def t_MULTI_LINE_COMMENT(t):
""" 

t_GREATER_THAN = r'>'
t_LESS_THAN = r'<'
t_GREATER_EQUAL_THAN = r'>='
t_LESS_EQUAL_THAN = r'<='
t_COMMA = r','
t_SEMICOLON = r';'
t_LEFT_PARENTHESIS = r'\('
t_RIGHT_PARENTHESIS = r'\)'
t_LEFT_BRACKET = r'\{'
t_RIGHT_BRACKET = r'\}'
t_LEFT_SQUARE_BRACKET = r'\['
t_RIGHT_SQUARE_BRACKET = r'\]'
t_ASSIGNMENT = r'='
t_PLUS = r'\+'
t_MINUS = r'-'
t_MULTIPLICATION = r'\*'
t_DIVISION = r'/'
t_EXPONENTIATION = r'\*\*'
t_INCREMENT = r'\+\+'
t_DECREMENT = r'--'
t_MODULUS = r'%'

t_ignore = " \t"


lexer = lex()


if __name__ == '__main__':
    test_data = '''
    hello = "hello_world"
    print(hello)
    '''
    lexer.input(test_data)
    
    for token in lexer:
        print(token.value, token.type)
