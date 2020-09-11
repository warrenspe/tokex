import logging

logger = logging.getLogger('tokex')

import logging
import sys

class TemporaryLogLevel(object):
    def __init__(self, target_level):
        self.target_level = target_level

    def __enter__(self):
        self.old_level = logger.getEffectiveLevel()
        logger.setLevel(self.target_level)

    def __exit__(self, et, ev, tb):
        logger.setLevel(self.old_level)
