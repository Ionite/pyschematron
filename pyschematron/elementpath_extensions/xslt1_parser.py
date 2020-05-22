from elementpath.xpath1_parser import XPath1Parser, is_document_node


class XSLT1Parser(XPath1Parser):
    SYMBOLS = XPath1Parser.SYMBOLS | {
        'current'
    }


register = XSLT1Parser.register
unregister = XSLT1Parser.unregister
literal = XSLT1Parser.literal
prefix = XSLT1Parser.prefix
infix = XSLT1Parser.infix
infixr = XSLT1Parser.infixr
method = XSLT1Parser.method
function = XSLT1Parser.function

register('current')


@method(function('current', nargs=0))
def select(self, context=None):
    if context is None:
        self.missing_context()
    if context.current_item is not None:
        return [context.current_item]
    else:
        return [context.root.getroot()]
        #raise Exception("current() called in a context without an original context item")


XSLT1Parser.build()
