import argparse
import os
import unittest
import sys

sys.path.append('.')

# Globals
TEST_DIR = os.path.split(os.path.dirname(os.path.realpath(__file__)))[-1]

def run(verbosity=1):
    loader = unittest.TestLoader()
    suite = loader.discover(TEST_DIR)
    _runSuite(suite, verbosity)

def runSelective(testFiles, verbosity):
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromNames(["%s.test_%s" % (TEST_DIR, testFile) for testFile in testFiles])
    _runSuite(suite, verbosity)

def _runSuite(testSuite, verbosity):
    unittest.TextTestRunner(verbosity=verbosity).run(testSuite)

def main():
    parser = argparse.ArgumentParser(description="Execute Tokex Unit Tests")
    parser.add_argument("testFiles", nargs="*")
    parser.add_argument("--verbosity", nargs="?", choices=['1', '2'], default=1)
    args = parser.parse_args()

    if len(args.testFiles):
        runSelective(args.testFiles, int(args.verbosity))
    else:
        run(int(args.verbosity))

if __name__ == '__main__':
    main()
