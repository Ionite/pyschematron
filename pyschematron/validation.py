from lxml import etree
from collections import OrderedDict

from pyschematron.exceptions import SchematronError


class ValidationContext(object):
    """
    Holds all the relevant data for an assertion or report to be validated
    """

    def __init__(self, schema, xml_doc):
        self.xml_doc = xml_doc
        self.variables = {}
        self.schema = schema
        self.pattern = None
        self.rule = None

        self.add_variables(schema.variables)

    def set_pattern(self, pattern):
        """
        Set the context pattern.
        This also adds the pattern variables to the context
        :param pattern: The pattern to set
        :return:
        """
        self.pattern = pattern
        self.add_variables(pattern.variables)

    def set_rule(self, rule):
        """
        Set the context rule.
        This DOES NOT add the rule variables to the context.
        That is done with a separate call to add_rule_variables(), as we need the document elements
        that match the rule's context to correctly evaluate the variable's value (which are generally unknown
        at the time this method is called, as the rule's context itself is necessary to determine those elements).
        :param rule:
        :return:
        """
        self.rule = rule

    # Special case for adding variables: within rules,
    # we have to use the context of the rule
    def add_rule_variables(self, rule, element):
        for name, value in rule.variables.items():
            self.variables[name] = self.schema.query_binding.interpret_let_statement(self.xml_doc, value, self.schema.ns_prefixes, self.variables,
                                                                                     context_item=element)

    # General case for adding variables
    def add_variables(self, variables, element=None):
        for name, value in variables.items():
            # Disallow multiple declarations of the same variables,
            # except in the case of rules
            if element is None and name in self.variables:
                raise SchematronError("Variable %s is declared multiple times within the same context" % name)
            self.variables[name] = self.schema.query_binding.interpret_let_statement(self.xml_doc, value, self.schema.ns_prefixes, self.variables)

    def copy(self):
        """
        Creates a clone of this ValidationContext
        :return:
        """
        copy = ValidationContext(self.schema, self.xml_doc)
        copy.__dict__.update(self.__dict__)
        return copy

    def msg(self, level, msg):
        if self.schema.verbosity >= level:
            print(msg)

    def get_rule_context_elements(self):
        """
        Returns all the elements in the xml doc that match the rule's context expression
        :return:
        """
        if self.rule.context == '/':
            return [None]
        else:
            return self.schema.query_binding.get_context_elements(self.xml_doc,
                                                                  self.rule.context,
                                                                  namespaces=self.schema.ns_prefixes,
                                                                  variables=self.variables)

    def validate_assertions(self, element, report):
        rule = self.rule
        for assert_test in rule.assertions:
            self.msg(3, "Start assert test: %s" % assert_test.id)
            self.msg(4, "Test context: %s" % str(rule.context))
            self.msg(4, "Test expression: %s" % assert_test.test)
            result = self.schema.query_binding.evaluate_assertion(self.xml_doc, element, self.schema.ns_prefixes, self.variables,
                                                                  assert_test.test)
            if not result:
                self.msg(5, "Failed assertion")
                self.msg(5, "Pattern: %s" % self.pattern.id)
                self.msg(5, "Variables:")
                for k, v in self.variables.items():
                    self.msg(5, "  %s: %s" % (k, v))
                self.msg(5, "Context root: %s" % str(self.xml_doc.getroot()))
                self.msg(5, "Context item: %s" % rule.context)
                self.msg(5, "CONTEXT ELEMENT: " + etree.tostring(element, pretty_print=True).decode('utf-8'))
                if assert_test.id:
                    self.msg(5, "Id: " + assert_test.id)
                self.msg(5, "Test: '%s'" % assert_test.test)
                self.msg(5, "Initial text: '%s'" % assert_test.to_string())
                self.msg(5, "Result: %s" % str(result))

                report.add_failed_assert(self, assert_test, element)
        for report_test in rule.reports:
            self.msg(3, "Start report test: %s" % report_test.id)
            self.msg(4, "Test context: %s" % str(rule.context))
            self.msg(4, "Test expression: %s" % report_test.test)
            result = self.schema.query_binding.evaluate_assertion(self.xml_doc, element, self.schema.ns_prefixes, self.variables,
                                                                  report_test.test)
            if result:
                self.msg(5, "Succesful report")
                self.msg(5, "Pattern: %s" % self.pattern.id)
                self.msg(5, "Variables:")
                for k, v in self.variables.items():
                    self.msg(5, "  %s: %s" % (k, v))
                self.msg(5, "Context root: %s" % str(self.xml_doc.getroot()))
                self.msg(5, "Context item: %s" % rule.context)
                self.msg(5, "CONTEXT ELEMENT: " + etree.tostring(element, pretty_print=True).decode('utf-8'))
                if report_test.id:
                    self.msg(5, "Id: " + report_test.id)
                self.msg(5, "Test: '%s'" % report_test.test)
                self.msg(5, "Result: %s" % str(result))

                report.add_successful_report(self, report_test, element)


class ValidationReport(object):
    def __init__(self):
        self.fired_rules = OrderedDict()

    def add_fired_rule(self, rule_context):
        self.fired_rules[rule_context] = []

    def add_failed_assert(self, rule_context, assertion, element):
        if (assertion, element) not in self.fired_rules[rule_context]:
            self.fired_rules[rule_context].append((assertion, element))

    def add_successful_report(self, rule_context, report, element):
        if (report, element) not in self.fired_rules[rule_context]:
            self.fired_rules[rule_context].append((report, element))

    def get_failed_asserts(self):
        """
        Return all failed asserts and successful reports as a list
        :param flag: The flag to filter for
        :return: A list of failed asserts
        """
        result = []
        for failed_asserts in self.fired_rules.values():
            result.extend(failed_asserts)
        return result

    def get_failed_asserts_flag(self, flag):
        """
        Return the failed asserts and succesful reports with the given flag value
        :param flag: The flag to filter for
        :return: A list of failed asserts
        """
        result = []
        for failed_asserts in self.fired_rules.values():
            result.extend([fa for fa, el in failed_asserts if fa.flag == flag])
        return result

    def get_failed_asserts_by_flag(self, default_flag=None):
        """
        Returns a dict of failed asserts and succesful reports, keyed by their flags.
        If default flag is given, asserts that did not have a flag are added to the list of asserts/reports with the given flag
        :return:
        """
        result = {}
        for failed_asserts in self.fired_rules.values():
            for failed_assert, element in failed_asserts:
                assert_flag = failed_assert.flag
                if assert_flag is None:
                    assert_flag = default_flag
                if assert_flag in result:
                    result[assert_flag].append((failed_assert, element))
                else:
                    result[assert_flag] = [(failed_assert, element)]
        return result
