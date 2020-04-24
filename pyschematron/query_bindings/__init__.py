
from pyschematron.exceptions import SchematronError, SchematronNotImplementedError

class QueryBinding(object):
    def __init__(self):
        raise SchematronError("QueryBinding base class cannot be instantiated directly")

    # Mandatory to implement in derived classes
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
        raise SchematronNotImplementedError("%s not implemented in query binding %s" % ("context element selection", self.get_name()))

    def evaluate_assertion(self, xml_document, context_element, namespaces, parser_variables, assertion):
        raise SchematronNotImplementedError("%s not implemented in query binding %s" % ("assertion evaluation", self.get_name()))


    #
    # Optional to implement in derived classes
    #
    def get_variable_delimiter(self):
        raise SchematronNotImplementedError("%s not implemented in query binding %s" % ("name query interpretation", self.get_name()))

    def get_abstract_pattern_delimiter(self):
        raise SchematronNotImplementedError("%s not implemented in query binding %s" % ("name query interpretation", self.get_name()))

    def evaluate_name_query(self, xml_document, context_element, namespaces, parser_variables, name_query):
        raise SchematronNotImplementedError("%s not implemented in query binding %s" % ("name query interpretation", self.get_name()))

    def evaluate_value_of_query(self, xml_document, context_element, namespaces, parser_variables, name_query):
        raise SchematronNotImplementedError("%s not implemented in query binding %s" % ("value-of query interpretation", self.get_name()))

    def interpret_let_statement(self, xml_document, value, namespaces, variables):
        raise SchematronNotImplementedError("%s not implemented in query binding %s" % ("let statement interpretation", self.get_name()))
