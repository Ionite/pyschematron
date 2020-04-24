"""
The query binding implementation for XPath2
"""

import elementpath

from elementpath import XPath2Parser, XPathContext, select

def get_context_elements(xml_document, rule_context, namespaces, variables):
    return select(xml_document, rule_context, namespaces=namespaces, variables=variables)

def parse_expression(xml_document, expression, namespaces, variables):
    parser = XPath2Parser(namespaces, variables)
    root_node = parser.parse(expression)
    context = XPathContext(root=xml_document)
    result = root_node.evaluate(context)
    return result
