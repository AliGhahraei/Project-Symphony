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
            int dec char str bool 12 4.75 .9 'a' "hello" true false void , ; ( )
            { } [ ] = + - * / ** ++ -- mod equals > < >= <= and or not fun while
            if else elseif hello sqrt return
            // This is a comment, so it should be ignored
            "my string"
            program
            ''',
            
            '''
            int INT dec DEC char CHAR str STR bool BOOL 12 INT_VAL 4.75 DEC_VAL
            0.9 DEC_VAL a CHAR_VAL hello STR_VAL true BOOL_VAL false BOOL_VAL
            void VOID , , ; ; ( ( ) ) { { } } [ [ ] ] = = + + - - * * / /
            ** EXPONENTIATION ++ INCREMENT -- DECREMENT mod MOD equals EQUALS > > 
            < < >= GREATER_EQUAL_THAN <= LESS_EQUAL_THAN and AND or OR not NOT
            fun FUN while WHILE if IF else ELSE elseif ELSEIF hello ID sqrt 
            SPECIAL_ID return RETURN my string STR_VAL program PROGRAM
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
