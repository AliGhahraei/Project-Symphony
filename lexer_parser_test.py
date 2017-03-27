from lexer import lexer
from glob import glob
from symphony_parser import (create_parser, GrammaticalError,
                             RedeclarationError, UndeclaredError)
from unittest import TestCase, main


VALID_PROGRAMS_PATH = 'tests/valid_symphonies/'
GRAMMAR_PATH = 'tests/invalid_grammar/'
REDECLARATION_PATH = 'tests/redeclaration/'
UNDECLARED_PATH = 'tests/undeclared_variables/'


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
        for invalid_program in glob(path + '*.sym'):
            self.parser = create_parser()
            
            try:
                with open(invalid_program) as file:
                    
                    with self.assertRaises(RaisedError):
                        print('Testing', invalid_program + '...', end=' ')
                        self.parser.parse(file.read())
            except:
                print('\033[91m Error!\033[0m')
                raise
            print()


    def test_right(self):      
        for valid_program in glob(VALID_PROGRAMS_PATH + '*.sym'):
            self.parser = create_parser()
            
            try:               
                with open(valid_program) as file:
                    print('Testing', valid_program + '...', end=' ')
                    self.parser.parse(file.read())
            except:
                print('\033[91m Error!\033[0m')
                raise
            print()


    def test_grammar(self):
        self.assert_programs_raise(GRAMMAR_PATH, GrammaticalError)


    def test_redeclaration(self):
        self.assert_programs_raise(REDECLARATION_PATH, RedeclarationError)


    def test_undeclared_variables(self):
        self.assert_programs_raise(UNDECLARED_PATH, UndeclaredError)


if __name__ == '__main__':
    main()
