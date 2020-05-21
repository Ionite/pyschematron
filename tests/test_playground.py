import unittest
from io import StringIO

import copy
from lxml import etree

from pyschematron.commands import validate
from pyschematron.commands import convert

from pyschematron.elementpath_extensions.select import select_with_context, select_all_with_context

from test_util import get_file
from pyschematron.elementpath_extensions.xslt2_parser import XSLT2Parser
from pyschematron.elementpath_extensions.context import XPathContextXSLT

def elem_priority(elem):
    if 'priority' in elem.attrib:
        return int(elem.attrib.get('priority'))
    else:
        return 0

def myprint(text):
    print(text)

def parse_expression(xml_document, expression, namespaces, variables, context_item=None):
    parser = XSLT2Parser(namespaces, variables)
    root_node = parser.parse(expression)
    context = XPathContextXSLT(root=xml_document, item=context_item)
    result = root_node.evaluate(context)
    return result

class XLSTTransform:
    def __init__(self, xslt):
        self.xslt = xslt
        self.variables = {
            'archiveDirParameter': '',
            'archiveNameParameter': '',
            'fileNameParameter': '',
            'fileDirParameter': ''
        }
        self.mode_templates = {}
        self._process_xslt()

    def _process_xslt(self):
        """preprocessing of the supplied xslt"""
        for element in self.xslt.getroot():
            if isinstance(element, etree._Comment):
                continue
            el_name = etree.QName(element.tag).localname
            if el_name == 'variable':
                var_name = element.attrib['name']
                var_value = element.attrib.get('select')
                if var_value is None:
                    var_value = element.text
                self.variables[var_name] = var_value
            elif el_name == 'template':
                mode = element.attrib.get('mode')
                if mode in self.mode_templates:
                    self.mode_templates[mode].append(element)
                else:
                    self.mode_templates[mode] = [element]
                #myprint("[XX] template match: '%s' mode %s" % (element.attrib['match'], str(element.attrib.get('mode'))))

                #match_expr = element.attrib['match']
                #template_match_elements = select_all_with_context(xml_doc, None, match_expr, namespaces=xslt.getroot().nsmap, variables=variables)
                #template_node_links[element] = template_match_elements
                #myprint("[XX] matching elements (%d): %s" % (len(template_match_elements), str(template_match_elements)))

    def get_potential_templates(self, mode, xml_doc, context_element):
        """

        :param mode:
        :param xml_doc:
        :param context_element: The XML node that is the current context
        :param element: The potential node (based on the 'select' statement of apply-template)
        :return:
        """
        result = []
        for template in self.mode_templates[mode]:
            match = template.attrib['match']
            #myprint("[XX] try template mode %s match %s in element %s" % (mode, match, str(context_element)))
            #myprint("[XX] looking for element %s" % str(element))
            applicable_elements = select_with_context(xml_doc, context_element, match, namespaces=self.xslt.getroot().nsmap, variables=self.variables)
            #myprint("[XX] elements:" + str(applicable_elements))
            if len(applicable_elements) > 0:
                result.append(template)
        # TODO: sort
        result = sorted(result, key=elem_priority, reverse=True)
        return result

    def transform(self, xml_doc):
        context_node = xml_doc.getroot()
        potential_templates = self.get_potential_templates(None, xml_doc, None)
        myprint("[XX] initial potential templates:")
        myprint(potential_templates)
        template = potential_templates[0]
        output_node = etree.Element("new_root")
        self.process_template(xml_doc, template, xml_doc.getroot(), output_node)
        print("[XX] RESULT:")
        # clear out all whitespace and parse again
        str = etree.tostring(output_node, pretty_print=True).decode('utf-8')
        parser = etree.XMLParser(remove_blank_text=True)
        new = etree.fromstring(str, parser=parser)
        print(etree.tostring(new, pretty_print=True).decode('utf-8'))


    def process_template_child(self, output_node, xml_doc, context_node, child):
        return child

    def process_xsl_apply_template(self, child, context_node, xml_doc):
        mode = child.attrib['mode']
        select = child.attrib.get('select')
        if select is None:
            elements_from_select = [context_node]
        elif select is '/':
            elements_from_select = [xml_doc.getroot()]
        else:
            elements_from_select = select_with_context(xml_doc, context_node, select, namespaces=self.xslt.getroot().nsmap, variables=self.variables)
        for element_from_select in elements_from_select:
            potential_templates = self.get_potential_templates(mode, xml_doc, element_from_select)
            if len(potential_templates) == 0:
                myprint("[XX] no potential templates")
            else:
                # for template in potential_templates:
                #    myprint("[XX] potential template: mode %s match %s priority %s" % (template.attrib['mode'], template.attrib['match'], str(template.attrib.get('priority'))))
                new_template = potential_templates[0]
                myprint("[XX] applying template: context node %s mode %s match %s priority %s" % (
                    str(element_from_select),
                    new_template.attrib['mode'], new_template.attrib['match'], str(new_template.attrib.get('priority'))))
                # pick the first one and process
                self.process_template(xml_doc, new_template, element_from_select, child)

    def process_node(self, node, xml_doc, context_node, output_node):
        if isinstance(node, etree._Comment):
            # Remove comments from xsl
            return None
        el_qname = etree.QName(node)
        if el_qname.namespace == 'http://www.w3.org/1999/XSL/Transform':
            el_name = el_qname.localname
            if el_name == 'comment':
                value = node.text
                for attr_child in node.getchildren():
                    value += str(self.process_node(attr_child, xml_doc, context_node, output_node))
                    if attr_child.tail is not None:
                        value += attr_child.tail
                return etree.Comment(value)
                #return node.text
            elif el_name == 'value-of':
                value = self.process_xsl_value_of(node, xml_doc, context_node)
                #print("[XX] RESULT OF VALUE OF (%s) %s" % (str(type(value)), str(value)))
                return value
            elif el_name == 'attribute':
                name = node.attrib['name']
                value = node.text
                for attr_child in node.getchildren():
                    value += str(self.process_node(attr_child, xml_doc, context_node, output_node))
                    if attr_child.tail is not None:
                        value += attr_child.tail
                output_node.attrib[name] = value
            elif el_name == 'apply-templates':
                return self.process_template(xml_doc, node, context_node, output_node)
            else:
                raise Exception("NotImpl: XSL directive '%s'" % el_name)
        else:
            new_output_node = etree.Element(node.tag, attrib=node.attrib, nsmap=node.nsmap)
            self.process_node_children(node, xml_doc, context_node, new_output_node)
            return new_output_node

    def process_node_children(self, node, xml_doc, context_node, output_node):
        for child in node:
            process_node_result = self.process_node(child, xml_doc, context_node, output_node)
            if process_node_result is None:
                pass
            elif isinstance(process_node_result, etree._Element):
                output_node.append(process_node_result)
            elif isinstance(process_node_result, str):
                # TODO: should this be added to text, or should we see if there are preceding child nodes
                # and use tail?
                # TODO: children of attribute?
                if output_node.text is None:
                    output_node.text = process_node_result
                else:
                    output_node.text += process_node_result
            else:
                raise Exception("NOTIMPL: return type %s from process_node" % str(type(process_node_result)))
        return output_node

    def process_xsl_value_of(self, node, xml_doc, context_node):
        select = node.attrib['select']
        # TODO: add document-uri to possible functions?
        if select == 'document-uri(/)':
            return ""
        else:
            result = parse_expression(xml_doc, "string(%s)" % node.attrib['select'], node.nsmap, self.variables, context_item=context_node)
        return result

    def process_template(self, xml_doc, template, context_node, output_node):
        #print("[XX] PROCESS TEMPLATE MODE %s" % (template.attrib.get('mode')))
        # copy all children, then process them
        #for child in template:
        #    output_node.append(copy.copy(source_child))
        return self.process_node_children(template, xml_doc, context_node, output_node)


class PlaygroundTest(unittest.TestCase):
    """Assorted tests, mainly used as a playground for later development"""

    def do_run_xslt_test(self, xslt_file, xml_file):

        xslt = etree.parse(xslt_file)
        xml_doc = etree.parse(xml_file)

        # Variables as defined in the XSL
        variables = {}
        # Template elements, and the document elements that match the match expression
        # key: template, value: [node]
        template_node_links = {}
        # key: mode, value: [template]
        mode_templates = {}

        # Preprocessing
        # Loop through the xslt, and store variables,
        # match templates to elements
        for element in xslt.getroot():
            if isinstance(element, etree._Comment):
                continue
            el_name = etree.QName(element.tag).localname
            if el_name == 'variable':
                var_name = element.attrib['name']
                var_value = element.attrib.get('select')
                if var_value is None:
                    var_value = element.text
                variables[var_name] = var_value
            elif el_name == 'template':
                mode = element.attrib.get('mode')
                if mode in mode_templates:
                    mode_templates[mode].append(element)
                else:
                    mode_templates[mode] = [element]
                #myprint("[XX] template match: '%s' mode %s" % (element.attrib['match'], str(element.attrib.get('mode'))))

                match_expr = element.attrib['match']
                template_match_elements = select_all_with_context(xml_doc, None, match_expr, namespaces=xslt.getroot().nsmap, variables=variables)
                template_node_links[element] = template_match_elements
                #myprint("[XX] matching elements (%d): %s" % (len(template_match_elements), str(template_match_elements)))

        context_node = xml_doc.getroot()
        potential_templates = get_potential_templates(mode_templates, template_node_links, None, xml_doc)
        myprint("[XX] initial potential templates:")
        myprint(potential_templates)
        template = potential_templates[0]
        for child in template.iter():
            el_name = etree.QName(child.tag).localname
            if el_name == 'apply-templates' and 'select' in child.attrib and 'mode' in child.attrib:
                mode = child.attrib['mode']
                select = child.attrib['select']
                myprint("[XX] mode: " + mode)
                myprint("[XX] select: " + mode)

                elements_from_select = select_with_context(xml_doc, context_node, select, namespaces=xslt.getroot().nsmap, variables=variables)
                myprint("[XX] elements for new context: " + str(elements_from_select))
                for element_from_select in elements_from_select:
                    if isinstance(element_from_select, etree._ElementTree):
                        element_from_select = element_from_select.getroot()
                    myprint("ELEMENT: " + str(element_from_select))
                    potential_templates = []
                    for potential_template in mode_templates[mode]:
                        myprint("[XX] initial potential new template for mode %s: %s" % (mode, str(potential_template.attrib["match"])))
                        matching_elements = select_with_context(xml_doc, element_from_select, potential_template.attrib['match'], namespaces=xslt.getroot().nsmap, variables=variables)
                        myprint("[XX] matching elements: " + str(matching_elements))
        #if context_node in template_match_elements[]

    def do_run_xslt_test2(self, xslt_file, xml_file):

        xslt = etree.parse(xslt_file)
        xml_doc = etree.parse(xml_file)

        transformer = XLSTTransform(xslt)
        transformer.transform(xml_doc)

    def test_playground(self):
        self.do_run_xslt_test(get_file("skeleton_output", "schematron.xsl"),
                              get_file("schematron", "schematron.sch"))

    def test_playground2(self):
        self.do_run_xslt_test2(get_file("skeleton_output", "schematron.xsl"),
                              get_file("schematron", "malformed/bad_is_a_attribute.sch"))

    def test_siubl11(self):
        self.do_run_xslt_test2("/home/jelte/repos/SI/validation/xsl/si-ubl-1.1.xsl",
                               "/home/jelte/repos/SI/testset/SI-UBL-1.1/SI-UBL-1.1-error-BII2-T10-R003.xml")

    def test_siubl20(self):
        self.do_run_xslt_test2("/home/jelte/repos/SI/validation/xsl/si-ubl-2.0.xsl",
                               "/home/jelte/repos/SI/testset/SI-UBL-2.0/SI-UBL-2.0_BR-NL-1_error_wrong_scheme.xml")
