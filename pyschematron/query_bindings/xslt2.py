"""
The query binding implementation for XPath2
"""

from .xpath2 import XPath2Binding
from elementpath import XPath2Parser, XPathContext, select, Selector

def instantiate():
    return XSLT2Binding()

class XSLT2Binding(XPath2Binding):
    def __init__(self):
        self.name = "xslt2"

    def interpret_let_statement(self, xml_document, value, namespaces, variables, context_item=None):
        return self.parse_expression(xml_document, value, namespaces, variables, context_item)