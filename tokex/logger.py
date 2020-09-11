import logging

LOGGER = logging.getLogger('tokex')

class TemporaryLogLevel(object):
    old_level = None

    def __init__(self, target_level):
        self.target_level = target_level

    def __enter__(self):
        self.old_level = LOGGER.getEffectiveLevel()
        LOGGER.setLevel(self.target_level)

    def __exit__(self, *_):
        LOGGER.setLevel(self.old_level)
