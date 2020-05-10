from lxml import etree
from collections import OrderedDict

from pyschematron.exceptions import SchematronError

class ValidationContext(object):
    """
    Holds all the relevant data for an assertion to be validated
    """
    def __init__(self, schema, xml_doc):
        self.xml_doc = xml_doc
        self.variables = {}
        self.schema = schema
        self.pattern = None
        self.rule = None

        self.add_variables(schema.variables)

    def set_pattern(self, pattern):
        self.pattern = pattern
        self.add_variables(pattern.variables)

    def set_rule(self, rule):
        self.rule = rule
        self.add_variables(rule.variables)

    def add_variables(self, variables):
        for name, value in variables.items():
            if name in self.variables:
                raise SchematronError("Variable %s is declared multiple times within the same context" % name)
            self.variables[name] = self.schema.query_binding.interpret_let_statement(self.xml_doc, value, self.schema.ns_prefixes, self.variables)

    def copy(self):
        copy = ValidationContext(self.schema, self.xml_doc)
        copy.variables = self.variables.copy()
        copy.pattern = self.pattern
        copy.rule = self.rule
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
        if (assertion,element) not in self.fired_rules[rule_context]:
            self.fired_rules[rule_context].append((assertion, element))
    
    def add_successful_report(self, rule_context, report, element):
        if (report,element) not in self.fired_rules[rule_context]:
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
            result.extend([fa for fa,el in failed_asserts if fa.flag == flag])
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
                    result[assert_flag].append(failed_assert)
                else:
                    result[assert_flag] = [failed_assert]
        return result
