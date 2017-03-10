from lexer import lexer
from os import listdir
from parser import parser, ParserException
from unittest import TestCase, main


VALID_PROGRAMS_PATH = 'tests/valid_symphonies/'
INVALID_PROGRAMS_PATH = 'tests/invalid_symphonies/'


class LexerTest(TestCase):
    def setUp(self):
        pass


    def assertLexerIO(self, lexer_input, expected_output):
        lexer.input(lexer_input)
        actual_output = ''.join([''.join(str(token.value).split()) + token.type
                                 for token in lexer])
        self.assertEqual(actual_output, ''.join(expected_output.split()))


    def test_types_right(self):
        self.assertLexerIO(
            '''
            /*
            Multiline comments are ignored...
            ... All of them
            */
            12 4.75 .9 'a' "hello" true false void , ; ( ) { } [ ] = + - * / ** 
            ++ -- mod equals > < >= <= and or not fun while if else elseif hello
            sqrt
            // This is a comment, so it should be ignored
            "my string"
            program
            ''',
            
            '''
            12 INT 4.75 DEC 0.9 DEC a CHAR hello STR true BOOL false BOOL 
            void VOID , , ; ; ( ( ) ) { { } } [ [ ] ] = = + + - - * * / /
            ** EXPONENTIATION ++ INCREMENT -- DECREMENT mod MOD equals EQUALS > > 
            < < >= GREATER_EQUAL_THAN <= LESS_EQUAL_THAN and AND or OR not NOT
            fun FUN while WHILE if IF else ELSE elseif ELSEIF hello ID sqrt 
            SPECIAL_ID my string STR program PROGRAM
            ''')


class ParserTest(TestCase):
    def setUp(self):
        pass


    def test_valid_programs(self):
        for valid_program in listdir(VALID_PROGRAMS_PATH):
            with open(VALID_PROGRAMS_PATH + valid_program) as file:
                parser.parse(file.read())


    def test_invalid_programs(self):
        for invalid_program in listdir(INVALID_PROGRAMS_PATH):
            with self.assertRaises(ParserException):
                with open(INVALID_PROGRAMS_PATH + invalid_program) as file:
                    parser.parse(file.read())


if __name__ == '__main__':
    main()
