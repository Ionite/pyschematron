import unittest

from elementpath import XPath2Parser, XPathContext, select
from lxml import etree

from pyschematron.elements import Schema
from pyschematron.exceptions import *
from test_util import get_file


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
                        self.assertTrue(result, a.to_string())

    def test_unknown_querybinding(self):
        self.assertRaises(SchematronNotImplementedError, Schema, get_file("schematron", "unknown_querybinding.sch"))


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
        error_ruleid_list = [err.parent.id for err, element in errors]
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

    def test_phase_with_unknown_pattern(self):
        schema = Schema(get_file("schematron", "malformed/bad_active_pattern.sch"))
        xml_doc = etree.parse(get_file("xml", "basic1_error_1.xml"))
        self.assertEqual("bad_phase", schema.get_phase("bad_phase").id)
        self.assertRaises(SchematronError, schema.validate_document, xml_doc, "bad_phase")


class TestDiagnostics(unittest.TestCase):
    def test_simple_diagnostics(self):
        schema = Schema(get_file("schematron", "diagnostics.sch"))
        xml_doc = etree.parse(get_file("xml", "diagnostics/more_than_three_animals.xml"))
        report = schema.validate_document(xml_doc)

        self.assertEqual(3, len(report.get_failed_asserts()))
        self.assertEqual(1, len(report.get_failed_asserts()[0][0].diagnostic_ids))
        self.assertEqual("""Noah, you must remove as many animals from the ark so that
      only two of one species live in this accommodation.""".strip(),
                         report.get_failed_asserts()[0][0].get_diagnostic_text(report.get_failed_asserts()[0][0].diagnostic_ids[0]).strip())


if __name__ == '__main__':
    unittest.main()
