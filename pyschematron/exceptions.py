
class SchematronError(Exception):
    pass

class SchematronParseError(SchematronError):
    pass

class SchematronNotImplementedError(SchematronError):
    pass

class SchematronQueryBindingError(SchematronError):
    pass