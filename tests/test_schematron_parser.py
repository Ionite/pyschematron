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

    def check_statement(self, statement, expected_result, xml_doc=None, context_item=None, context_root=None, debug=False):
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

        #self.check_statement("exists(element/name)", True)
        #self.check_statement("exists(element/decimal)", True)
        #self.check_statement("exists(/decimal)", True)



    def test_empty_elements_xpath1(self):
        self.check_statement("* or normalize-space(text()) != ''", True)



class TestParseSchematron(unittest.TestCase):

    def test_basic_example(self):
        schema = Schema(get_file("schematron", "basic.sch"))

        doc = etree.parse(get_file("xml", "basic_ok.xml"))

        variables = {}
        parser = XPath2Parser(schema.ns_prefixes, variables)
        for p in schema.patterns:
            #print("[XX] %s has %d rules" % (p.id, len(p.rules)))
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

        errors, warnings = schema.validate_document(xml_doc)
        error_id_list = [e.id for e in errors]
        warning_id_list = [w.id for w in warnings]
        self.assertEqual(expected_errors, error_id_list)
        self.assertEqual(expected_warnings, warning_id_list)

    def test_valid_documents(self):
        self.check_schema_validation(get_file("schematron", "basic.sch"), get_file("xml", "basic_ok.xml"), [], [])

    def test_invalid_documents(self):
        self.check_schema_validation(get_file("schematron", "basic.sch"), get_file("xml", "basic_error_1.xml"), ["1"], [])
        self.check_schema_validation(get_file("schematron", "basic.sch"), get_file("xml", "basic_error_2.xml"), ["2"], [])
        self.check_schema_validation(get_file("schematron", "basic.sch"), get_file("xml", "basic_warning_3.xml"), [], ["3"])
        self.check_schema_validation(get_file("schematron", "basic.sch"), get_file("xml", "basic_warning_4.xml"), [], ["4"])

class TestXpath2QueryBinding(unittest.TestCase):
    def test_error_let_statement(self):
        schema = Schema(get_file("schematron", "xpath2/error_let_statement.sch"))
        xml_doc = etree.parse(get_file("xml", "basic_ok.xml"))
        self.assertRaises(SchematronQueryBindingError, schema.validate_document, xml_doc)

if __name__ == '__main__':
    unittest.main()