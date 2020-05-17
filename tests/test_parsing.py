import unittest
from decimal import Decimal
from io import StringIO

from lxml import etree

from elementpath import XPath2Parser, XPathContext, select
from pyschematron.elementpath_extensions.select import select_with_context
from pyschematron.elementpath_extensions.xslt1_parser import XSLT1Parser
from pyschematron.elementpath_extensions.xslt2_parser import XSLT2Parser
from pyschematron.elements import Schema

from test_util import get_file


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


class TestAllElements(unittest.TestCase):
    def setUp(self):
        self.schema = Schema(get_file("schematron", "all_elements.sch"))

    def test_setup(self):
        pass


class TestXSLTParsers(unittest.TestCase):
    def check_current(self, parser_class):
        xml_doc = etree.parse(StringIO("""
        <root>
            <element id="a">value</element>
            <element id="b" ref="a">other value</element>
        </root>
        """))
        expr = "current()"
        for node in xml_doc.iter():
            nodes = select_with_context(xml_doc, node, expr, parser=parser_class)
            self.assertEqual([node], nodes)

        node_a = select(xml_doc, "//element")[0]
        node_b = select(xml_doc, "//element")[1]
        ref_node = select(xml_doc, "//element[@ref]")[0]
        nodes = select_with_context(xml_doc, ref_node, "/root/element[@id=current()/@ref]", parser=parser_class)
        self.assertEqual([node_a], nodes)

    def test_current_xslt1(self):
        self.check_current(XSLT1Parser)

    def test_current_xslt2(self):
        self.check_current(XSLT2Parser)
