import unittest
from io import StringIO

import copy
from collections import OrderedDict
from lxml import etree

from pyschematron.elementpath_extensions.select import select_with_context, select_all_with_context

from test_util import get_file
from pyschematron.elementpath_extensions.xslt2_parser import XSLT2Parser
from pyschematron.elementpath_extensions.xslt1_parser import XSLT1Parser
from pyschematron.elementpath_extensions.context import XPathContextXSLT

from elementpath.exceptions import ElementPathSyntaxError

def elem_priority(elem_tuple):
    if 'priority' in elem_tuple[0].attrib:
        return int(elem_tuple[0].attrib.get('priority'))
    else:
        return 0

def print_debug(text):
    #print(text)
    pass

# caching select statements saves about 30% of the time for large xsls and documents
SELECT_CACHE = {}
SELECT_COUNTER = 0
SELECT_CACHE_HITS = 0

# other idea for speedup: track templates that use no context data
# (how to determine?), and cache processing result of those too
# Anything else?

def do_select(xml_doc, look_for_context, match, namespaces, variables):
    global SELECT_COUNTER
    global SELECT_CACHE_HITS
    SELECT_COUNTER = SELECT_COUNTER + 1
    #print("[XX] SELECT CTX %s EXPR %s" % (str(look_for_context), match))
    if (look_for_context, match) in SELECT_CACHE:
        SELECT_CACHE_HITS = SELECT_CACHE_HITS + 1
        return SELECT_CACHE[(look_for_context, match)]
    else:
        result = select_with_context(xml_doc, look_for_context, match, namespaces=namespaces, variables=variables)
        SELECT_CACHE[(look_for_context, match)] = result
        return result

PARSE_CACHE = {}

def parse_expression(xml_document, expression, namespaces, variables, context_item=None):
    #print_debug("[XX] CTX: %s EXPR: %s" % (str(context_item), str(expression)))
    if (context_item, expression) in PARSE_CACHE:
        return PARSE_CACHE[(context_item, expression)]
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
    print_debug("[XX] RESULT: " + str(result))
    PARSE_CACHE[(context_item, expression)] = result
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
                #myprint_debug("[XX] template match: '%s' mode %s" % (element.attrib['match'], str(element.attrib.get('mode'))))

                #match_expr = element.attrib['match']
                #template_match_elements = select_all_with_context(xml_doc, None, match_expr, namespaces=xslt.getroot().nsmap, variables=variables)
                #template_node_links[element] = template_match_elements
                #myprint_debug("[XX] matching elements (%d): %s" % (len(template_match_elements), str(template_match_elements)))

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
            print_debug("[XX] try template mode %s match %s in element %s" % (mode, match, str(context_element)))
            #myprint_debug("[XX] looking for element %s" % str(element))
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
                #applicable_elements = select_with_context(xml_doc, look_for_context, match, namespaces=self.xslt.getroot().nsmap, variables=self.variables)
                applicable_elements = do_select(xml_doc, look_for_context, match, namespaces=self.xslt.getroot().nsmap, variables=self.variables)
            print_debug("[XX] elements:" + str(applicable_elements))
            if len(applicable_elements) > 0:
                print_debug("[XX] template is applicable")
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
            print_debug("[XX] try template mode %s match %s" % (mode, match))
            print_debug("[XX]   the context_node is %s" % str(context_element))
            print_debug("[XX]   looking for selected element %s" % str(selected_element))
            #myprint_debug("[XX] looking for element %s" % str(element))
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
                if selected_element is None:
                    #applicable_elements = select_all_with_context(xml_doc, look_for_context, match, namespaces=self.xslt.getroot().nsmap, variables=self.variables)
                    applicable_elements = do_select(xml_doc, look_for_context, match, namespaces=self.xslt.getroot().nsmap, variables=self.variables)
                else:
                    applicable_elements = do_select(xml_doc, look_for_context, match, namespaces=self.xslt.getroot().nsmap, variables=self.variables)
            print_debug("[XX] elements:" + str(applicable_elements))
            if selected_element is None:
                if len(applicable_elements) > 0:
                    print_debug("[XX] template is applicable (no selected element)")
                    result.append((template, applicable_elements))
            elif selected_element in applicable_elements:
                print_debug("[XX] template is applicable (selected element in match results)")
                result.append((template, [selected_element]))
            else:
                # Also look for the selected element's direct children
                #found_child = False
                #if selected_element != xml_doc:
                #    children = selected_element.getchildren()
                #    for selected_child in children:
                #        if selected_child in applicable_elements:
                #            result.append(template)
                #            found_child = True
                #            break
                #if not found_child:
                #    print_debug("[XX] selected element not found in match results")
                print_debug("[XX] selected element not found in match results")
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
                #print_debug("[XX] APPEND %s" % str(pnr))
                #print_debug("[XX] TO %s" % str(target_node))
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
        print_debug("[XX] looking for initial template")
        potential_templates = self.get_potential_templates(None, xml_doc, xml_doc)
        print_debug("[XX] initial potential templates:")
        print_debug(potential_templates)
        template = potential_templates[0]
        output_node = etree.Element("new_root")
        process_result = self.process_template(xml_doc, template, None)
        self.apply_process_result(output_node, process_result)
        print_debug("[XX] RESULT:")
        # clear out all whitespace and parse again
        str = etree.tostring(output_node, pretty_print=True).decode('utf-8')
        parser = etree.XMLParser(remove_blank_text=True)
        new = etree.fromstring(str, parser=parser)
        print_debug(etree.tostring(new, pretty_print=True).decode('utf-8'))
        return etree.ElementTree(new)


    def process_template_child(self, output_node, xml_doc, context_node, child):
        return child


    def process_xsl_apply_template(self, template_node, context_node, xml_doc):
        # If select is not given, apply to all children of the context_node
        print_debug("[XX] Process XSL apply-templates mode: %s select: %s" % (str(template_node.attrib.get('mode')), str(template_node.attrib.get('select'))))
        print_debug("[XX] with context node: " + str(context_node))
        mode = template_node.attrib.get('mode')
        select = template_node.attrib.get('select')
        if select is None:
            if context_node is None:
                elements_to_apply_on = [xml_doc.getroot()]
            else:
                elements_to_apply_on = context_node.getchildren()
        elif select == '/':
            elements_to_apply_on = [xml_doc]
        else:
            print_debug("[XX] run select_with_context context %s select %s" % (str(context_node), str(select)))
            elements_to_apply_on = do_select(xml_doc, context_node, select, namespaces=self.xslt.getroot().nsmap, variables=self.variables)

        print_debug("[XX] Elements to apply templates on:")
        for e in elements_to_apply_on:
            print_debug("[XX]    %s" % str(e))

        mode_templates = self.mode_templates[mode]
        print_debug("[XX] Potential templates:")
        element_templates_todo = OrderedDict()
        for t in mode_templates:
            print_debug("[XX]    mode: %s match: %s" % (mode, str(t.attrib.get('match'))))
            if context_node == xml_doc:
                look_for_context = None
            else:
                look_for_context = context_node
            template_match_elements = do_select(xml_doc, look_for_context, t.attrib['match'], namespaces=self.xslt.getroot().nsmap, variables=self.variables)
            if len(template_match_elements) == 0:
                print_debug("[XX]    no elements match template (%s), try from root element" % t.attrib['match'])
                # If the context is None, try again from the root element
                #if look_for_context is None:
                #    look_for_context = xml_doc.getroot()
                #    template_match_elements = select_with_context(xml_doc, look_for_context, t.attrib['match'], namespaces=self.xslt.getroot().nsmap, variables=self.variables)

            found_applicable_element = False
            for tme in template_match_elements:
                print_debug("[XX]    template match element: " + str(tme))
                print_debug("[XX]    elements_to_apply_on: " + str(elements_to_apply_on))
                # can apply to either the element from select or their direct children
                # and if applicable for entire doc, returns them all
                #if tme in elements_to_apply_on or elements_to_apply_on == [xml_doc]:
                if elements_to_apply_on == [xml_doc]:
                    print_debug("[XX] THIS TEMPLATE IS APPLICABLE FOR %s" % str(tme))
                    found_applicable_element = True
                    if tme in element_templates_todo:
                        element_templates_todo[tme].append(t)
                    else:
                        element_templates_todo[tme] = [t]
                    print_debug("[XX]     list of potentials for %s now: %s" % (str(tme), str(element_templates_todo[tme])))
                elif tme in elements_to_apply_on:
                    print_debug("[XX] THIS TEMPLATE IS APPLICABLE FOR %s" % str(tme))
                    found_applicable_element = True
                    if tme in element_templates_todo:
                        element_templates_todo[tme].append(t)
                    else:
                        element_templates_todo[tme] = [t]
                    print_debug("[XX]     list of potentials for %s now: %s" % (str(tme), str(element_templates_todo[tme])))
                else:
                    # check children too
                    for etoa in elements_to_apply_on:
                        if not isinstance(etoa, str):
                            if tme in etoa:
                                found_applicable_element = True
                                if tme in element_templates_todo:
                                    element_templates_todo[tme].append(t)
                                else:
                                    element_templates_todo[tme] = [t]
                                print_debug("[XX]     list of potentials for %s now: %s" % (str(tme), str(element_templates_todo[tme])))
            if not found_applicable_element:
                print_debug("[XX]    Did not find any applicable element, do not execute this template")
                #if elements_to_apply_on != [xml_doc]:
                    #for tme in template_match_elements:
                    #    print_debug("[XX] YYYZZYY tme in []: %s" % str(tme in [el.getchildren() for el in elements_to_apply_on]))
                    #for el in elements_to_apply_on:
                    #    for c in el:
                    #        print_debug("[XX] [YYYYYY] el: %s elchild: %s" % (str(el), str(c)))
        print_debug("[XX] ALL TEMPLATES TO RUN:")
        for element,templates in element_templates_todo.items():
            print_debug("[XX]    Element: " + str(element))
            for template in templates:
                print_debug("[XX]        mode %s match %s prio %s" % (mode, str(template.attrib.get('match')), str(template.attrib.get('priority'))))
        print_debug(element_templates_todo)
        result = []
        for element,templates in element_templates_todo.items():
            sorted_templates = sorted(templates, key=elem_priority, reverse=True)
            print_debug("[XX] CHOSE TEMPLATE %s with PRIO %s" % (str(sorted_templates[0]), str(sorted_templates[0].attrib.get('priority'))))
            template_result = self.process_template(xml_doc, sorted_templates[0], element)
            if isinstance(template_result, list):
                result.extend(template_result)
            else:
                result.append(template_result)
        return result

    def prev_process_xsl_apply_template(self, child, context_node, xml_doc):
        mode = child.attrib.get('mode')
        select = child.attrib.get('select')
        if select is None:
            if mode is None:
                return None
            elements_from_select = [context_node]
        elif select is '/':
            #elements_from_select = [xml_doc.getroot()]
            #elements_from_select = [ xml_doc, xml_doc.getroot() ]
            elements_from_select = [ None ]
        else:
            elements_from_select = do_select(xml_doc, context_node, select, namespaces=self.xslt.getroot().nsmap, variables=self.variables)
        print_debug("[XX] ELEMENTS FROM SELECT: " + str(elements_from_select))
        result = []
        for element_from_select in elements_from_select:
            print_debug("[XX] LOOKING FOR TEMPLATE FOR SELECTED ELEMENT %s" % element_from_select)
            potential_templates = self.get_potential_templates2(mode, xml_doc, context_node, element_from_select)
            if len(potential_templates) == 0:
                print_debug("[XX] no potential templates")
                pass
            else:
                # for template in potential_templates:
                #    myprint_debug("[XX] potential template: mode %s match %s priority %s" % (template.attrib['mode'], template.attrib['match'], str(template.attrib.get('priority'))))
                if elements_from_select != [None]:
                    new_template = potential_templates[0][0]
                    print_debug("[XX] applying template: context node %s mode %s select %s match %s priority %s" % (
                        str(element_from_select),
                        str(new_template.attrib.get('mode')), select, new_template.attrib['match'], str(new_template.attrib.get('priority'))))
                    # pick the first one and process
                    # If the current context is still 'none', move to root now
                    template_result = self.process_template(xml_doc, new_template, element_from_select)
                    if isinstance(template_result, list):
                        result.extend(template_result)
                    else:
                        result.append(template_result)
                else:
                    new_template = potential_templates[0][0]
                    for matching_element in potential_templates[0][1]:
                        # execute template on all matching elements
                        print_debug("[XX] applying template: context node %s mode %s match_from_template %s match %s priority %s" % (
                            str(matching_element),
                            str(new_template.attrib.get('mode')), select, new_template.attrib['match'], str(new_template.attrib.get('priority'))))
                        # pick the first one and process
                        # If the current context is still 'none', move to root now
                        template_result = self.process_template(xml_doc, new_template, matching_element)
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
                #print_debug("[XX] RESULT OF VALUE OF (%s) %s" % (str(type(value)), str(value)))
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
                print_debug("[XX] found apply-templates mode: %s select: %s" % (str(node.attrib.get('mode')), str(node.attrib.get('select'))))
                result = self.process_xsl_apply_template(node, context_node, xml_doc)
                #result = self.process_template(xml_doc, node, context_node)
                print_debug("[XX] result of template: " + str(result))
                return result
                #self.apply_process_result(new_output_node, template_result)
            elif el_name == 'if':
                return self.process_xsl_if(node, xml_doc, context_node)
            elif el_name == 'choose':
                result = self.process_xsl_choose(node, xml_doc, context_node)
                print_debug("[XX] CHOOSE RESULT: " + str(result))
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
            #print_debug("[XX] PROCESS VARIABLE %s" % name)
            value = parse_expression(xml_doc, node.attrib['select'], self.xslt.getroot().nsmap, self.variables, context_node)
            #print_debug("[XX] VARIABLE SELECT RESULT: " + str(value))
        else:
            value = node.text
        self.variables[name] = value

    def process_xsl_choose(self, node, xml_doc, context_node):
        when_node = node.find('{http://www.w3.org/1999/XSL/Transform}when')
        otherwise_node = node.find('{http://www.w3.org/1999/XSL/Transform}otherwise')
        print_debug("[XX] when test: %s" % when_node.attrib['test'])
        if when_node is None:
            raise Exception('when not found')
        if context_node == xml_doc:
            # maybe None?
            context_node = None
        result = parse_expression(xml_doc, when_node.attrib['test'], when_node.nsmap, self.variables, context_item=context_node)
        if result:
            print_debug("[XX] result positive, apply when children")
            return self.process_node_children(when_node, xml_doc, context_node)
        elif otherwise_node is not None:
            print_debug("[XX] result negative, apply otherwise children: ")
            print_debug(etree.tostring(otherwise_node, pretty_print=True).decode('utf-8'))
            return self.process_node_children(otherwise_node, xml_doc, context_node)

    def process_xsl_if(self, node, xml_doc, context_node):
        result = parse_expression(xml_doc, node.attrib['test'], node.nsmap, self.variables, context_item=context_node)
        if result is not None and result:
            return self.process_node_children(node, xml_doc, context_node)

    def process_xsl_value_of(self, node, xml_doc, context_node):
        select = node.attrib['select']
        # TODO: add document-uri to possible functions?
        if select == 'document-uri(/)':
            return ""
        else:
            result = parse_expression(xml_doc, "string(%s)" % node.attrib['select'], node.nsmap, self.variables, context_item=context_node)
        return result

    def prevprocess_template(self, xml_doc, template, context_node):
        print_debug("[XX] PROCESS TEMPLATE MODE %s MATCH %s" % (template.attrib.get('mode'), str(template.attrib.get('match'))))
        if context_node == xml_doc or context_node is None:
            if template.attrib['match'] != '/':
                print_debug("[XX] context is document itself, and template does not apply to '/', changing to root element")
                context_node = xml_doc.getroot()
            else:
                print_debug("[XX] context is document itself, and template applies to '/', changing to None")
                context_node = None
        # copy all children, then process them
        #for child in template:
        #    output_node.append(copy.copy(source_child))
        return self.process_node_children(template, xml_doc, context_node)

    def process_template(self, xml_doc, template, context_node):
        print_debug("[XX] PROCESS TEMPLATE MODE %s MATCH %s" % (template.attrib.get('mode'), str(template.attrib.get('match'))))
        return self.process_node_children(template, xml_doc, context_node)


class PlaygroundTest(unittest.TestCase):
    """Assorted tests, mainly used as a playground for later development"""

    def do_run_xslt_test(self, xslt_file, xml_file):
        pass

    def do_run_xslt_test2(self, xslt_file, xml_file):

        xslt = etree.parse(xslt_file)
        xml_doc = etree.parse(xml_file)

        transformer = XLSTTransform(xslt)
        return transformer.transform(xml_doc)

    def test_playground(self):
        result = self.do_run_xslt_test2(get_file("skeleton_output", "schematron.xsl"),
                                        get_file("schematron", "schematron.sch"))
        failed_asserts = result.findall("//{http://purl.oclc.org/dsdl/svrl}failed-assert")
        self.assertEqual(0, len(failed_asserts))

    def test_playground2(self):
        result = self.do_run_xslt_test2(get_file("skeleton_output", "schematron.xsl"),
                                        get_file("schematron", "malformed/bad_is_a_attribute.sch"))
        failed_asserts = result.findall("//{http://purl.oclc.org/dsdl/svrl}failed-assert")
        self.assertEqual(1, len(failed_asserts))

    def test_siubl11_ok(self):
        result = self.do_run_xslt_test2("/home/jelte/repos/SI/validation/xsl/si-ubl-1.1.xsl",
                                        "/home/jelte/repos/SI/testset/SI-UBL-1.1/SI-UBL-1.1-ok-minimal.xml")
        failed_asserts = result.findall("//{http://purl.oclc.org/dsdl/svrl}failed-assert")
        self.assertEqual(0, len(failed_asserts))

    def test_siubl11(self):
        result = self.do_run_xslt_test2("/home/jelte/repos/SI/validation/xsl/si-ubl-1.1.xsl",
                                        "/home/jelte/repos/SI/testset/SI-UBL-1.1/SI-UBL-1.1-error-BII2-T10-R003.xml")
        failed_asserts = result.findall("//{http://purl.oclc.org/dsdl/svrl}failed-assert")
        self.assertEqual(1, len(failed_asserts))
        #print("[XX] SELECT CALLED: %d times" % SELECT_COUNTER)
        #print("[XX] %d cache hits for select" % SELECT_CACHE_HITS)

    def test_siubl20(self):
        result = self.do_run_xslt_test2("/home/jelte/repos/SI/validation/xsl/si-ubl-2.0.xsl",
                                        "/home/jelte/repos/SI/testset/SI-UBL-2.0/SI-UBL-2.0_BR-NL-1_error_wrong_scheme.xml")
        failed_asserts = result.findall("//{http://purl.oclc.org/dsdl/svrl}failed-assert")
        self.assertEqual(1, len(failed_asserts))

    def test_custom(self):
        self.do_run_xslt_test2(get_file("xslt", "student_sample.xsl"),
                              get_file("xml", "xslt/student_sample.xml"))


if __name__ == '__main__':
    unittest.main()
