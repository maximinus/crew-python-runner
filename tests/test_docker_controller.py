import unittest

from src.crew_python_runner import runner


def get_python_code(filename):
    with open(f'./python_code/{filename}.py') as f:
        return f.read()


class TestSimpleCodeRuns(unittest.TestCase):
    def test_code_runs(self):
        code = get_python_code('test_print')
        result = runner.run_python(code)
        self.assertEqual(result.output, 'Running!')
        self.assertEqual(result.error_code, 0)

    def test_error_output(self):
        code = get_python_code('test_error')
        result = runner.run_python(code)
        self.assertTrue(result.output.startswith('Traceback (most recent call last):'))
        self.assertTrue(result.output.rstrip().endswith('division by zero'))
        self.assertEqual(result.error_code, 1)

    def test_string_repr(self):
        code = get_python_code('test_print')
        result = runner.run_python(code)
        self.assertEqual(str(result), '0: Running!')


if __name__ == '__main__':
    unittest.main()
