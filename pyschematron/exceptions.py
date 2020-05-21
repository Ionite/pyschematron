class SchematronError(Exception):
    pass

class SchematronParseError(SchematronError):
    pass

class QueryBindingError(SchematronError):
    pass

class SchematronNotImplementedError(SchematronError):
    pass


class SchematronQueryBindingError(SchematronError):
    pass
