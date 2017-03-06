from lexer_parser import lexer
from unittest import TestCase, main


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
            ++ -- % equals > < >= <= and or not fun while if else elseif hello
            // This is a comment, so it should be ignored
            "my string"
            ''',
            
            '''
            12 INT 4.75 DEC 0.9 DEC a CHAR hello STR true BOOL false BOOL 
            void VOID , , ; ; ( ( ) ) { { } } [ [ ] ] = = + + - - * * / /
            ** EXPONENTIATION ++ INCREMENT -- DECREMENT % % equals EQUALS > > 
            < < >= GREATER_EQUAL_THAN <= LESS_EQUAL_THAN and AND or OR not NOT
            fun FUN while WHILE if IF else ELSE elseif ELSEIF hello ID 
            my string STR
            ''')


if __name__ == '__main__':
    main()
