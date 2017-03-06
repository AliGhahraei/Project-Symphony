from lexer_parser import lexer
from unittest import TestCase, main


class LexerTest(TestCase):
    def setUp(self):
        pass


    def assertLexerIO(self, lexer_input, expected_output):
        lexer.input(lexer_input)
        actual_output = ''.join([str(token.value) + token.type
                                 for token in lexer])
        self.assertEqual(actual_output, ''.join(expected_output.split()))


    def test_int_right(self):
        self.assertLexerIO('12', '''12 INT''')


if __name__ == '__main__':
    main()
