class SchematronError(Exception):
    pass

class SchematronParseError(SchematronError):
    pass

class SchematronNotSupportedError(SchematronError):
    pass