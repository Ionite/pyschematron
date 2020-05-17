from elementpath.xpath2_parser import XPath2Parser


class XSLT2Parser(XPath2Parser):
    SYMBOLS = XPath2Parser.SYMBOLS | {
        'current'
    }


register = XSLT2Parser.register
unregister = XSLT2Parser.unregister
literal = XSLT2Parser.literal
prefix = XSLT2Parser.prefix
infix = XSLT2Parser.infix
infixr = XSLT2Parser.infixr
method = XSLT2Parser.method
function = XSLT2Parser.function

register('current')


@method(function('current', nargs=0))
def select(self, context=None):
    if context is None:
        self.missing_context()
    if context.current_item is not None:
        return [context.current_item]
    else:
        raise Exception("current() called in a context without an original context item")


XSLT2Parser.build()
