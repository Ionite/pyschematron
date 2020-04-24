
from pyschematron.exceptions import *

from elementpath import XPath1Parser, XPathContext, select


def instantiate():
    return XSLTBinding()

class XSLTBinding(object):
    def __init__(self):
        self.name = 'xslt'

    def get_name(self):
        """
        Return the query binding name
        :return: the query binding name, as a string
        """
        return self.name

    def get_context_elements(self, xml_document, rule_context, namespaces, variables):
        """
        Returns the elements that are specified by the context statement
        :param xml_document: The document that is processed
        :param rule_context: The rule context expression
        :param namespaces: Namespaces to be used in the rule context expression
        :param variables: Variables to be used in the rule context expression
        :return:
        """
        return select(xml_document, rule_context, namespaces=namespaces, variables=variables)

    def parse_expression(self, xml_document, expression, namespaces, variables):
        parser = XPath1Parser(namespaces, variables)
        root_node = parser.parse(expression)
        context = XPathContext(root=xml_document)
        result = root_node.evaluate(context)
        return result

    def evaluate_assertion(self, xml_document, context_element, namespaces, parser_variables, assertion):
        parser = XPath1Parser(namespaces, parser_variables)
        context = XPathContext(root=xml_document, item=context_element)
        expr = assertion
        # Should we check whether this is boolean?
        root_token = parser.parse(expr)
        result = root_token.evaluate(context=context)
        return result


    def get_variable_delimiter(self):
        return "$"

    def get_abstract_pattern_delimiter(self):
        return "$"

    def evaluate_name_query(self, xml_document, context_element, namespaces, parser_variables, name_query):
        parser = XPath1Parser(namespaces, parser_variables)
        context = XPathContext(root=xml_document, item=context_element)
        expr = name_query
        # Should we check whether this returns a node name?
        root_token = parser.parse(expr)
        result = root_token.evaluate(context=context)
        return result

    def evaluate_value_of_query(self, xml_document, context_element, namespaces, parser_variables, name_query):
        parser = XPath1Parser(namespaces, parser_variables)
        context = XPathContext(root=xml_document, item=context_element)
        expr = name_query
        # Should we check whether this returns a string?
        root_token = parser.parse(expr)
        result = root_token.evaluate(context=context)
        return result

    def interpret_let_statement(self, xml_document, value, namespaces, variables):
        return self.parse_expression(xml_document, value, namespaces, variables)