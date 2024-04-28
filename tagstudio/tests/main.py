import unittest

if __name__ == '__main__':
    """Runs every test."""
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover(start_dir='src', pattern='test_*.py')

    runner = unittest.TextTestRunner()
    result = runner.run(test_suite)
