import argparse
import logging
import os
import sys
import unittest


# Globals
TEST_DIR = os.path.dirname(
    os.path.abspath(__file__)
)
PROJECT_ROOT = os.path.normpath(
    os.path.join(TEST_DIR, "..")
)

def run(verbosity=1):
    loader = unittest.TestLoader()
    suite = loader.discover(TEST_DIR)
    _runSuite(suite, verbosity)


def runSelective(testFiles, verbosity):
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromNames(testFiles)
    _runSuite(suite, verbosity)


def _runSuite(testSuite, verbosity):
    unittest.TextTestRunner(verbosity=verbosity).run(testSuite)


def main():
    parser = argparse.ArgumentParser(description="Execute Tokex Unit Tests")
    parser.add_argument("testFiles", nargs="*")
    parser.add_argument("--verbosity", nargs="?", choices=['1', '2'], default=1)
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    if len(args.testFiles):
        runSelective(args.testFiles, int(args.verbosity))
    else:
        run(int(args.verbosity))


if __name__ == '__main__':
    # Ensure we're running from the project root
    os.chdir(PROJECT_ROOT)
    sys.path.insert(1, ".")

    main()
