from lexer import lexer
from os import listdir
from symphony_parser import parser, GrammaticalError, RedeclarationError
from unittest import TestCase, main


VALID_PROGRAMS_PATH = 'tests/valid_symphonies/'
GRAMMAR_TEST = 'tests/invalid_grammar/'
REDECLARATION_TEST = 'tests/redeclaration/'


class LexerTest(TestCase):
    def setUp(self):
        pass


    def assert_lexer_IO(self, lexer_input, expected_output):
        lexer.input(lexer_input)
        actual_output = ''.join([''.join(str(token.value).split()) + token.type
                                 for token in lexer])
        self.assertEqual(actual_output, ''.join(expected_output.split()))


    def test_types_right(self):
        self.assert_lexer_IO(
            '''
            /*
            Multiline comments are ignored...
            ... All of them
            // Even nested comments
            fun int fun1(int x, int y){
              rasfsdgsg
            }
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


    def assert_programs_raise(self, path, RaisedError):
        for invalid_program in listdir(path):
            try:
                with open(path + invalid_program) as file:
                    with self.assertRaises(RaisedError):
                        print('Testing', invalid_program + '...', end=' ')
                        parser.parse(file.read())
            except:
                print('\033[91m Error!\033[0m')
                raise
            print()


    def test_right(self):
        for valid_program in listdir(VALID_PROGRAMS_PATH):
            try:
                with open(VALID_PROGRAMS_PATH + valid_program) as file:
                    print('Testing', valid_program + '...', end=' ')
                    parser.parse(file.read())
            except:
                print('\033[91m Error!\033[0m')
                raise
            print()


    def test_grammar(self):
        self.assert_programs_raise(GRAMMAR_TEST, GrammaticalError)


    def test_redeclaration(self):
        self.assert_programs_raise(REDECLARATION_TEST, RedeclarationError)


if __name__ == '__main__':
    main()
