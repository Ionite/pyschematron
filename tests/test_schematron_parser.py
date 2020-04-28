import os
import unittest

from elementpath import XPath2Parser, XPathContext, select
from decimal import Decimal
from lxml import etree

from pyschematron.elements import Schema
from pyschematron.exceptions import *

BASE_DIR = os.path.abspath("%s/../../" % __file__)


def get_file(category, name):
    return os.path.join(BASE_DIR, "tests", "data", category, name)


class TestIndividualStatements(unittest.TestCase):
    """Some individual tests to make sure our version of elementpath supports the necessary functionality"""

    def setUp(self):
        self.parser = XPath2Parser()
        self.xml_str = """<doc>
        <element>
            <name>Foo</name>
            <number>1</number>
            <decimal>12.34</decimal>
            <subelement>
                <name>Bar</name>
            </subelement>
        </element>
    </doc>"""
        self.xml_doc = etree.XML(self.xml_str)

    def evaluate_statement(self, statement, xml_doc=None, context_item=None, context_root=None, debug=False):
        if xml_doc is None:
            xml_doc = self.xml_doc
        if context_root is None:
            context_root = xml_doc
        context = XPathContext(root=context_root, item=context_item)
        statement_root = self.parser.parse(statement)
        return statement_root.evaluate(context)

    def check_statement(self, statement, expected_result, xml_doc=None, context_item=None, context_root=None,
                        debug=False):
        if xml_doc is None:
            xml_doc = self.xml_doc
        if context_root is None:
            context_root = xml_doc
        context = XPathContext(root=context_root, item=context_item)
        statement_root = self.parser.parse(statement)
        result = statement_root.evaluate(context)

        if debug:
            print("[DEBUG] Context root: " + str(context_root))
            print("[DEBUG] Context item: " + str(context_item))
            print("[DEBUG] Statement: " + str(statement))
            print("[DEBUG] Expected: %s (%s)" % (expected_result, str(type(expected_result))))
            print("[DEBUG] Got:      %s (%s)" % (result, str(type(result))))
        self.assertEqual(expected_result, result, "Expected %s for %s" % (str(expected_result), statement))

    def check_statement_has_result(self, statement, xml_doc=None, context_item=None, context_root=None):
        # Same as check_statement, but now check whether there is any result at all
        if xml_doc is None:
            xml_doc = self.xml_doc
        if context_root is None:
            context_root = xml_doc
        context = XPathContext(root=context_root, item=context_item)
        statement_root = self.parser.parse(statement)
        result = statement_root.evaluate(context)
        self.assertNotEqual([], result, "Expected non-empty result for %s" % (statement))

    def test_element_type_coercion(self):
        self.check_statement("xs:decimal(\"12.34\")", Decimal('12.34'))
        self.check_statement("xs:decimal(element/decimal)", Decimal('12.34'))
        element = self.xml_doc.find("element/decimal")
        self.check_statement("xs:decimal(.)", Decimal('12.34'), context_item=element)

    def test_element_exists(self):
        # when setup with defaults, 'doc' is the default context, but the 'element' containing doc is the xpath root
        self.check_statement("exists(element/name)", True)
        self.check_statement("exists(element/number)", True)

        self.check_statement("exists(/doc/element/name)", True)
        self.check_statement("exists(/doc/element/number)", True)

        self.check_statement("exists(//name)", True)
        self.check_statement("exists(//number)", True)

        context_root = self.xml_doc.find("doc")
        self.check_statement("exists(/*/element/name)", True, context_root=context_root)

        # self.check_statement("exists(element/name)", True)
        # self.check_statement("exists(element/decimal)", True)
        # self.check_statement("exists(/decimal)", True)

    def test_empty_elements_xpath1(self):
        self.check_statement("* or normalize-space(text()) != ''", True)


class TestParseSchematron(unittest.TestCase):

    def test_basic_example(self):
        schema = Schema(get_file("schematron", "basic.sch"))

        doc = etree.parse(get_file("xml", "basic1_ok.xml"))

        variables = {}
        parser = XPath2Parser(schema.ns_prefixes, variables)
        for p in schema.patterns.values():
            # print("[XX] %s has %d rules" % (p.id, len(p.rules)))
            for r in p.rules:

                elements = select(doc, r.context)
                for element in elements:
                    context = XPathContext(root=doc, item=element)
                    for a in r.assertions:
                        root_token = parser.parse(a.test)
                        result = root_token.evaluate(context)
                        self.assertTrue(result, a.text)

    def test_unknown_querybinding(self):
        self.assertRaises(SchematronNotImplementedError, Schema, get_file("schematron", "unknown_querybinding.sch"))


class TestValidation(unittest.TestCase):

    def check_schema_validation(self, schema_file, xml_file, expected_errors, expected_warnings):
        """
        expected_errors is a list of the id values of the assertions that should fail with either no flag or flag="error"
        expected_warnings is a list of the id values of the assertions that should fail with either flag="warning"
        """
        schema = Schema(schema_file)
        xml_doc = etree.parse(xml_file)

        report = schema.validate_document(xml_doc)
        errors = report.get_failed_asserts()
        error_id_list = [e.id for e in errors if e.flag != 'warning']
        warnings = report.get_failed_asserts()
        warning_id_list = [w.id for w in warnings if w.flag == 'warning']
        self.assertEqual(expected_errors, error_id_list)
        self.assertEqual(expected_warnings, warning_id_list)

    def test_valid_documents(self):
        self.check_schema_validation(get_file("schematron", "basic.sch"), get_file("xml", "basic1_ok.xml"), [], [])

    def test_invalid_documents(self):
        self.check_schema_validation(get_file("schematron", "basic.sch"), get_file("xml", "basic1_error_1.xml"), ["1"],
                                     [])
        self.check_schema_validation(get_file("schematron", "basic.sch"), get_file("xml", "basic1_error_2.xml"), ["2"],
                                     [])
        self.check_schema_validation(get_file("schematron", "basic.sch"), get_file("xml", "basic1_warning_3.xml"), [],
                                     ["3"])
        self.check_schema_validation(get_file("schematron", "basic.sch"), get_file("xml", "basic1_warning_4.xml"), [],
                                     ["4"])


class TestRuleOrder(unittest.TestCase):
    """
    This test is taken from the article at
    http://schematron.com/2018/07/the-most-common-programming-error-with-schematron/
    """

    def setUp(self):
        self.schema = Schema(get_file("schematron", "orderchecks/xslt.sch"))

    def validate(self, schema, xml_string):
        xml_doc = etree.ElementTree(etree.XML(xml_string))
        report = schema.validate_document(xml_doc)
        errors = report.get_failed_asserts()
        error_ruleid_list = [e.rule.id for e in errors]
        return error_ruleid_list

    def check_rule_order(self, schematron_file):
        schema = Schema(get_file("schematron", schematron_file))

        # Element a should match rule 1 only
        self.assertEqual([], self.validate(schema, '<a>1</a>'))
        # self.assertEqual(['r1'], self.validate("<a>2</a>"))
        self.assertEqual(['r1'], self.validate(schema, '<root id="1"><a>2</a></root>'))

        # Element c should match rule 3 only
        self.assertEqual([], self.validate(schema, "<c>1</c>"))
        self.assertEqual(['r3'], self.validate(schema, "<c>2</c>"))

        # Element c should match rule 4 only
        self.assertEqual([], self.validate(schema, "<d>1</d>"))
        self.assertEqual(['r4'], self.validate(schema, "<d>2</d>"))

        # An arbitraty element should match rule 5
        self.assertEqual([], self.validate(schema, '<arb id="a">1</arb>'))
        self.assertEqual(['r5'], self.validate(schema, "<arb>1</arb>"))

        # Make sure this goes for nested elements too
        self.assertEqual([], self.validate(schema, '<arb id="a"><a>1</a><b>1</b><c>1</c><d>1</d><e id="1">1</e></arb>'))
        self.assertEqual(['r4'],
                         self.validate(schema, '<arb id="a"><a>1</a><b>1</b><c>1</c><d>2</d><e id="1">1</e></arb>'))
        self.assertEqual(['r1', 'r2', 'r3', 'r4'],
                         self.validate(schema, '<arb id="a"><a>2</a><b>2</b><c>2</c><d>2</d><e id="1">2</e></arb>'))

    def test_order_xslt(self):
        self.check_rule_order("orderchecks/xslt.sch")

    def test_order_xslt2(self):
        self.check_rule_order("orderchecks/xslt2.sch")

    def test_order_xpath2(self):
        self.check_rule_order("orderchecks/xpath2.sch")


class TestXpath2QueryBinding(unittest.TestCase):
    def test_error_let_statement(self):
        schema = Schema(get_file("schematron", "xpath2/error_let_statement.sch"))
        xml_doc = etree.parse(get_file("xml", "basic1_ok.xml"))
        self.assertRaises(SchematronQueryBindingError, schema.validate_document, xml_doc)


class TestVariableSubstitution(unittest.TestCase):

    def test_variables1(self):
        schema = Schema(get_file("schematron", "variables/variables1_xslt2.sch"))
        xml_doc = etree.parse(get_file("xml", "variables/variables1_correct.xml"))
        report = schema.validate_document(xml_doc)
        errors = report.get_failed_asserts()
        self.assertEqual([], errors, [e.test for e in errors])

    def test_variables_multiple_error(self):
        schema = Schema(get_file("schematron", "variables/variables1_xslt2_multiple_error.sch"))
        xml_doc = etree.parse(get_file("xml", "variables/variables1_correct.xml"))
        self.assertRaises(SchematronError, schema.validate_document, xml_doc)

class TestFullSchematronSample(unittest.TestCase):
    def setUp(self):
        self.schema = Schema(get_file("schematron", "full.sch"))

    def test_ok(self):
        xml_doc = etree.parse(get_file("xml", "basic1_ok.xml"))
        report = self.schema.validate_document(xml_doc)
        failed_asserts = report.get_failed_asserts_by_flag()
        self.assertEqual({}, failed_asserts)

    def test_bad_1(self):
        xml_doc = etree.parse(get_file("xml", "basic1_error_1.xml"))
        report = self.schema.validate_document(xml_doc)
        self.assertEqual(2, len(report.get_failed_asserts_by_flag()))
        self.assertEqual(1, len(report.get_failed_asserts_flag("builtin_existence")))
        self.assertEqual(1, len(report.get_failed_asserts_flag("included_existence")))

    def test_phases(self):
        xml_doc = etree.parse(get_file("xml", "basic1_error_1.xml"))
        report = self.schema.validate_document(xml_doc, phase="builtin_and_included")
        self.assertEqual(2, len(report.get_failed_asserts_by_flag()))
        self.assertEqual(1, len(report.get_failed_asserts_flag("builtin_existence")))
        self.assertEqual(1, len(report.get_failed_asserts_flag("included_existence")))

        report = self.schema.validate_document(xml_doc, phase="builtin_only")
        self.assertEqual(1, len(report.get_failed_asserts_by_flag()))
        self.assertEqual(1, len(report.get_failed_asserts_flag("builtin_existence")))
        self.assertEqual(0, len(report.get_failed_asserts_flag("included_existence")))

        report = self.schema.validate_document(xml_doc, phase="included_only")
        self.assertEqual(1, len(report.get_failed_asserts_by_flag()))
        self.assertEqual(0, len(report.get_failed_asserts_flag("builtin_existence")))
        self.assertEqual(1, len(report.get_failed_asserts_flag("included_existence")))

        self.assertRaises(SchematronError, self.schema.validate_document, xml_doc, "unknown_phase")
        self.assertEqual("phase_with_unknown_pattern", self.schema.get_phase("phase_with_unknown_pattern").id)
        self.assertRaises(SchematronError, self.schema.validate_document, xml_doc, "phase_with_unknown_pattern")



if __name__ == '__main__':
    unittest.main()
