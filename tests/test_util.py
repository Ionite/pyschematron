import os

BASE_DIR = os.path.abspath("%s/../../" % __file__)


def get_file(category, name):
    return os.path.join(BASE_DIR, "tests", "data", category, name)