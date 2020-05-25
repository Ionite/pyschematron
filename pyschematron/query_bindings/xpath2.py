"""
The query binding implementation for XPath2
"""

import elementpath

from . import QueryBinding
from pyschematron.exceptions import *
from pyschematron.elementpath_extensions.context import XPathContextXSLT
from pyschematron.elementpath_extensions.xslt2_parser import XSLT2Parser

from elementpath import select, Selector

def instantiate():
    return XPath2Binding()


class XPath2Binding(QueryBinding):
    def __init__(self):
        self.name = "xpath2"

    def get_context_elements(self, xml_document, rule_context, namespaces, variables):
        result = select(xml_document, rule_context, namespaces=namespaces, variables=variables)
        if rule_context.startswith('/'):
            return result
        else:
            selector = Selector(rule_context, namespaces=namespaces, variables=variables)
            for el in xml_document.iter():
                result.extend(selector.select(el))
            return result

    def parse_expression(self, xml_document, expression, namespaces, variables, context_item=None):
        parser = XSLT2Parser(namespaces, variables)
        root_node = parser.parse(expression)
        context = XPathContextXSLT(root=xml_document, item=context_item)
        result = root_node.evaluate(context)
        return result

    def evaluate_assertion(self, xml_document, context_element, namespaces, parser_variables, assertion):
        parser = XSLT2Parser(namespaces, parser_variables)
        context = XPathContextXSLT(root=xml_document, item=context_element)
        expr = "fn:boolean(%s)" % assertion
        root_token = parser.parse(expr)
        result = root_token.evaluate(context=context)
        return result

    def get_variable_delimiter(self):
        return "$"

    def get_abstract_pattern_delimiter(self):
        return "$"

    def evaluate_name_query(self, xml_document, context_element, namespaces, parser_variables, name_query):
        parser = XSLT2Parser(namespaces, parser_variables)
        context = XPathContextXSLT(root=xml_document, item=context_element)
        expr = "fn:node-name(%s)" % name_query
        root_token = parser.parse(expr)
        result = root_token.evaluate(context=context)
        return result

    def evaluate_value_of_query(self, xml_document, context_element, namespaces, parser_variables, name_query):
        parser = XSLT2Parser(namespaces, parser_variables)
        context = XPathContextXSLT(root=xml_document, item=context_element)
        expr = "fn:string(%s)" % name_query
        root_token = parser.parse(expr)
        result = root_token.evaluate(context=context)
        return result

    def interpret_let_statement(self, xml_document, value, namespaces, variables):
        raise SchematronQueryBindingError("let statement not allowed for Xpath2 query bindings")
