import os


class WorkingDirectory(object):
    def __init__(self, new_directory):
        self.new_directory = new_directory
        self.original_directory = os.getcwd()

    def __enter__(self):
        os.chdir(self.new_directory)

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.chdir(self.original_directory)


def abstract_replace_vars(query_binding, text, variables):
    s = text
    # Reverse sort them by length, so a basic replace() call works
    keys = sorted(variables.keys(), key=len, reverse=True)
    for key in keys:
        s = s.replace("%s%s" % (query_binding.get_abstract_pattern_delimiter(), key), variables[key])
    return s
