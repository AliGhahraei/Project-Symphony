from ply.lex import lex, LexError


tokens = (
    'INT', 'DEC', 'CHAR', 'STR', 'BOOL', 'VOID', 'COMMA', 'SEMICOLON',
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
keywords_to_types.update({keyword: 'BOOL' for keyword in ['true', 'false']})


states = (
    ('MULTILINECOMMENT', 'exclusive'),
)

t_MULTILINECOMMENT_ignore = ' \t'


def t_MULTILINECOMMENT(t):
    r'/\*'
    t.lexer.begin('MULTILINECOMMENT')


def t_MULTILINECOMMENT_newline(t):
    r'\n'
    t.lexer.lineno += 1


def t_MULTILINECOMMENT_close(t):
    r'\*/'
    t.lexer.begin('INITIAL')


def t_MULTILINECOMMENT_text(t):
    r'[^(\*/)]'
    pass


def t_MULTILINECOMMENT_error(t):
    t_error(t)


def t_IDS_AND_KEYWORDS(t):
    r'[a-zA-Z_][0-9a-zA-Z_]*'
    t.type = keywords_to_types.get(t.value, 'ID')
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


def t_eof(t):
    return None


def t_error(t):
    print("The system found a problem with how you wrote your program, so "
          + "please find the character sequence '" + t.value[0] + "' on line "
          + str(t.lexer.lineno) + " and correct it.")

"""
def t_SINGLE_LINE_COMMENT(t):

def t_MULTI_LINE_COMMENT(t):
""" 

literals = ['>', '<', ',', ';', '(', ')', '{', '}', '[', ']', '=', '+', '-', 
            '*', '/', '%']
t_GREATER_EQUAL_THAN = r'>='
t_LESS_EQUAL_THAN = r'<='
t_EXPONENTIATION = r'\*\*'
t_INCREMENT = r'\+\+'
t_DECREMENT = r'--'

t_ignore_SINGLE_LINE_COMMENT = r'//.*'
t_ignore = " \t"


lexer = lex()
