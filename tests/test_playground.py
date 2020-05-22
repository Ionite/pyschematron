import unittest
from io import StringIO

import copy
from lxml import etree

from pyschematron.commands import validate
from pyschematron.commands import convert

from pyschematron.elementpath_extensions.select import select_with_context, select_all_with_context

from test_util import get_file
from pyschematron.elementpath_extensions.xslt2_parser import XSLT2Parser
from pyschematron.elementpath_extensions.xslt1_parser import XSLT1Parser
from pyschematron.elementpath_extensions.context import XPathContextXSLT

from elementpath.exceptions import ElementPathSyntaxError

def elem_priority(elem):
    if 'priority' in elem.attrib:
        return int(elem.attrib.get('priority'))
    else:
        return 0

def myprint(text):
    print(text)

def parse_expression(xml_document, expression, namespaces, variables, context_item=None):
    print("[XX] PARSING EXPRESSION: " + expression)
    print("[XX] WITH CONTEXT NODE: " + str(context_item))
    parser = XSLT2Parser(namespaces, variables)
    try:
        root_node = parser.parse(expression)
    except ElementPathSyntaxError as orig_error:
        # Attempt fallback to xpath1 first, if that fails too, raise original error
        try:
            parser = XSLT1Parser(namespaces, variables)
            root_node = parser.parse(expression)
        except:
            raise orig_error

    context = XPathContextXSLT(root=xml_document, item=context_item)
    result = root_node.evaluate(context)
    print("[XX] RESULT: " + str(result))
    return result

class Attribute:
    def __init__(self, name, value):
        self.name = name
        self.value = value

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
            myprint("[XX] try template mode %s match %s in element %s" % (mode, match, str(context_element)))
            #myprint("[XX] looking for element %s" % str(element))
            if match == '/':
                if context_element == xml_doc:
                    applicable_elements = [ xml_doc ]
                else:
                    applicable_elements = []
            else:
                if context_element == xml_doc:
                    # TODO: problem here;
                    # sometimes we need the xml_doc.getroot() as the context
                    # sometimes None. How to tell the difference?
                    #look_for_context = None
                    look_for_context = xml_doc
                else:
                    look_for_context = context_element
                applicable_elements = select_with_context(xml_doc, look_for_context, match, namespaces=self.xslt.getroot().nsmap, variables=self.variables)
            myprint("[XX] elements:" + str(applicable_elements))
            if len(applicable_elements) > 0:
                print("[XX] template is applicable")
                result.append(template)
        # TODO: sort
        result = sorted(result, key=elem_priority, reverse=True)
        return result

    def get_potential_templates2(self, mode, xml_doc, context_element, selected_element):
        """
        Returns all templates for the given mode where the given 'selected_element' is in
        the results of the 'match' expresion of the template for the given context.
        If selected_elements is None, returns all templates where 'match' result is not empty
        :param mode:
        :param xml_doc:
        :param context_element: The XML node that is the current context
        :param element: The potential node (based on the 'select' statement of apply-template)
        :return:
        """
        result = []
        for template in self.mode_templates[mode]:
            match = template.attrib['match']
            myprint("[XX] try template mode %s match %s" % (mode, match))
            myprint("[XX]   the context_node is %s" %  str(context_element))
            myprint("[XX]   looking for selected element %s" % str(selected_element))
            #myprint("[XX] looking for element %s" % str(element))
            if match == '/':
                if context_element == xml_doc:
                    applicable_elements = [ xml_doc ]
                else:
                    applicable_elements = []
                applicable_elements = [ xml_doc ]
            else:
                if context_element == xml_doc:
                    # TODO: problem here;
                    # sometimes we need the xml_doc.getroot() as the context
                    # sometimes None. How to tell the difference?
                    #look_for_context = None
                    look_for_context = xml_doc
                else:
                    look_for_context = context_element
                applicable_elements = select_with_context(xml_doc, look_for_context, match, namespaces=self.xslt.getroot().nsmap, variables=self.variables)
            myprint("[XX] elements:" + str(applicable_elements))
            if selected_element is None:
                if len(applicable_elements) > 0:
                    print("[XX] template is applicable (no selected element)")
                    result.append(template)
            elif selected_element in applicable_elements:
                print("[XX] template is applicable (selected element in match results)")
                result.append(template)
        # TODO: sort
        result = sorted(result, key=elem_priority, reverse=True)
        return result

    def apply_process_result(self, target_node, process_node_result):
        """
        Add the result of a process_X call to the target node, depending on type of result
        :param target_node:
        :param result:
        :return:
        """
        prev_node = None
        if type(process_node_result) != list:
            process_node_result = [process_node_result]
        for pnr in process_node_result:
            if pnr is None:
                pass
            elif isinstance(pnr, Attribute):
                target_node.attrib[pnr.name] = pnr.value
            elif isinstance(pnr, etree._Element):
                #print("[XX] APPEND %s" % str(pnr))
                #print("[XX] TO %s" % str(target_node))
                target_node.append(pnr)
                prev_node = pnr
            elif isinstance(pnr, str):
                # TODO: should this be added to text, or should we see if there are preceding child nodes
                # and use tail?
                # TODO: children of attribute?
                if prev_node is None:
                    if target_node.text is None:
                        target_node.text = pnr
                    else:
                        target_node.text += pnr
                else:
                    if prev_node.tail is None:
                        prev_node.tail = pnr
                    else:
                        prev_node.tail += pnr
            else:
                raise Exception("NOTIMPL: return type %s from process_node" % str(type(pnr)))

    def transform(self, xml_doc):
        context_node = xml_doc.getroot()
        print("[XX] looking for initial template")
        potential_templates = self.get_potential_templates(None, xml_doc, xml_doc)
        myprint("[XX] initial potential templates:")
        myprint(potential_templates)
        template = potential_templates[0]
        output_node = etree.Element("new_root")
        process_result = self.process_template(xml_doc, template, xml_doc.getroot())
        self.apply_process_result(output_node, process_result)
        print("[XX] RESULT:")
        # clear out all whitespace and parse again
        str = etree.tostring(output_node, pretty_print=True).decode('utf-8')
        parser = etree.XMLParser(remove_blank_text=True)
        new = etree.fromstring(str, parser=parser)
        print(etree.tostring(new, pretty_print=True).decode('utf-8'))


    def process_template_child(self, output_node, xml_doc, context_node, child):
        return child

    def process_xsl_apply_template(self, child, context_node, xml_doc):
        mode = child.attrib.get('mode')
        select = child.attrib.get('select')
        if select is None:
            if mode is None:
                return None
            elements_from_select = [context_node]
        elif select is '/':
            #elements_from_select = [xml_doc.getroot()]
            elements_from_select = [ xml_doc, xml_doc.getroot() ]
        else:
            elements_from_select = select_with_context(xml_doc, context_node, select, namespaces=self.xslt.getroot().nsmap, variables=self.variables)
        print("[XX] ELEMENTS FROM SELECT: " + str(elements_from_select))
        result = []
        for element_from_select in elements_from_select:
            print("[XX] LOOKING FOR TEMPLATE FOR SELECTED ELEMENT %s" % element_from_select)
            # Get potential templates;
            # there are two
            potential_templates = self.get_potential_templates2(mode, xml_doc, context_node, element_from_select)
            if len(potential_templates) == 0:
                myprint("[XX] no potential templates")
                pass
            else:
                # for template in potential_templates:
                #    myprint("[XX] potential template: mode %s match %s priority %s" % (template.attrib['mode'], template.attrib['match'], str(template.attrib.get('priority'))))
                new_template = potential_templates[0]
                myprint("[XX] applying template: context node %s mode %s match %s priority %s" % (
                    str(element_from_select),
                    str(new_template.attrib.get('mode')), new_template.attrib['match'], str(new_template.attrib.get('priority'))))
                # pick the first one and process
                template_result = self.process_template(xml_doc, new_template, element_from_select)
                if isinstance(template_result, list):
                    result.extend(template_result)
                else:
                    result.append(template_result)
        return result

    def process_node(self, node, xml_doc, context_node):
        if isinstance(node, etree._Comment):
            # Remove comments from xsl
            return None
        el_qname = etree.QName(node)
        if el_qname.namespace == 'http://www.w3.org/1999/XSL/Transform':
            el_name = el_qname.localname
            if el_name == 'comment':
                value = node.text
                for attr_child in node.getchildren():
                    value += str(self.process_node(attr_child, xml_doc, context_node))
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
                    value += str(self.process_node(attr_child, xml_doc, context_node))
                    if attr_child.tail is not None:
                        value += attr_child.tail
                return Attribute(name, value)
            elif el_name == 'apply-templates':
                print("[XX] found apply-templates mode: %s select: %s" % (str(node.attrib.get('mode')), str(node.attrib.get('select'))))
                result = self.process_xsl_apply_template(node, context_node, xml_doc)
                #result = self.process_template(xml_doc, node, context_node)
                print("[XX] result of template: " + str(result))
                return result
                #self.apply_process_result(new_output_node, template_result)
            elif el_name == 'if':
                return self.process_xsl_if(node, xml_doc, context_node)
            elif el_name == 'choose':
                result = self.process_xsl_choose(node, xml_doc, context_node)
                print("[XX] CHOOSE RESULT: " + str(result))
                return result
            elif el_name == 'text':
                return node.text
            elif el_name == 'variable':
                # TODO: scoping
                self.process_xsl_variable(node, xml_doc, context_node)
                return None
            else:
                raise Exception("NotImpl: XSL directive '%s'" % el_name)
        else:
            new_output_node = etree.Element(node.tag, attrib=node.attrib, nsmap=node.nsmap)
            new_children = self.process_node_children(node, xml_doc, context_node)
            self.apply_process_result(new_output_node, new_children)
            return new_output_node

    def process_node_children(self, node, xml_doc, context_node):
        result = []
        if node.text:
            result.append(node.text)
        for child in node:
            process_node_result = self.process_node(child, xml_doc, context_node)
            if type(process_node_result) == list:
                result.extend(process_node_result)
            else:
                result.append(process_node_result)
            if child.tail:
                result.append(child.tail)
        return result

    def process_xsl_variable(self, node, xml_doc, context_node):
        name = node.attrib['name']
        if 'select' in node.attrib:
            #print("[XX] PROCESS VARIABLE %s" % name)
            value = parse_expression(xml_doc, node.attrib['select'], self.xslt.getroot().nsmap, self.variables, context_node)
            #print("[XX] VARIABLE SELECT RESULT: " + str(value))
        else:
            value = node.text
        self.variables[name] = value

    def process_xsl_choose(self, node, xml_doc, context_node):
        when_node = node.find('{http://www.w3.org/1999/XSL/Transform}when')
        otherwise_node = node.find('{http://www.w3.org/1999/XSL/Transform}otherwise')
        print("[XX] when test: %s" % when_node.attrib['test'])
        if when_node is None:
            raise Exception('when not found')
        result = parse_expression(xml_doc, when_node.attrib['test'], when_node.nsmap, self.variables, context_item=context_node)
        if result:
            print("[XX] result positive, apply when children")
            return self.process_node_children(when_node, xml_doc, context_node)
        elif otherwise_node is not None:
            print("[XX] result negative, apply otherwise children")
            return self.process_node_children(otherwise_node, xml_doc, context_node)

    def process_xsl_if(self, node, xml_doc, context_node):
        result = parse_expression(xml_doc, node.attrib['test'], node.nsmap, self.variables, context_item=context_node)
        if result is not None and result:
            return self.process_node(node, xml_doc, context_node)

    def process_xsl_value_of(self, node, xml_doc, context_node):
        select = node.attrib['select']
        # TODO: add document-uri to possible functions?
        if select == 'document-uri(/)':
            return ""
        else:
            result = parse_expression(xml_doc, "string(%s)" % node.attrib['select'], node.nsmap, self.variables, context_item=context_node)
        return result

    def process_template(self, xml_doc, template, context_node):
        print("[XX] PROCESS TEMPLATE MODE %s" % (template.attrib.get('mode')))
        if context_node == xml_doc:
            if template.attrib['match'] != '/':
                print("[XX] context is document itself, and template does not apply to '/', changing to root element")
                context_node = xml_doc.getroot()
            else:
                print("[XX] context is document itself, and template applies to '/', changing to None")
                context_node = None
        # copy all children, then process them
        #for child in template:
        #    output_node.append(copy.copy(source_child))
        return self.process_node_children(template, xml_doc, context_node)


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
        self.do_run_xslt_test2(get_file("skeleton_output", "schematron.xsl"),
                              get_file("schematron", "schematron.sch"))

    def test_playground2(self):
        self.do_run_xslt_test2(get_file("skeleton_output", "schematron.xsl"),
                              get_file("schematron", "malformed/bad_is_a_attribute.sch"))

    def test_siubl11_ok(self):
        self.do_run_xslt_test2("/home/jelte/repos/SI/validation/xsl/si-ubl-1.1.xsl",
                               "/home/jelte/repos/SI/testset/SI-UBL-1.1/SI-UBL-1.1-ok-minimal.xml")

    def test_siubl11(self):
        self.do_run_xslt_test2("/home/jelte/repos/SI/validation/xsl/si-ubl-1.1.xsl",
                               "/home/jelte/repos/SI/testset/SI-UBL-1.1/SI-UBL-1.1-error-BII2-T10-R003.xml")

    def test_siubl20(self):
        self.do_run_xslt_test2("/home/jelte/repos/SI/validation/xsl/si-ubl-2.0.xsl",
                               "/home/jelte/repos/SI/testset/SI-UBL-2.0/SI-UBL-2.0_BR-NL-1_error_wrong_scheme.xml")
