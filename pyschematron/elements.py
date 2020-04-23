
"""
This module contains the schematron elements, as defined in the schematron definition files
"""
import os

from elementpath import XPath2Parser, XPathContext, select
from lxml import etree

from pyschematron.exceptions import SchematronException
from pyschematron.util import WorkingDirectory, abstract_replace_vars


class Schema(object):
    def __init__(self, verbosity=0):
        self.title = None
        self.file_path = None
        self.verbosity = verbosity

        # Prefixes is a mapping of prefix to uri
        self.ns_prefixes = {}
        # A list of patterns
        self.patterns = []

    def msg(self, level, msg):
        if self.verbosity >= level:
            print(msg)

    def read_from_file(self, file_path):
        self.file_path = file_path
        xml = etree.parse(file_path)
        # print("[XX] processing %s" % file_path)
        with WorkingDirectory(os.path.dirname(file_path)):
            root = xml.getroot()
            for element in root:
                # Ignore comments
                cls = element.__class__.__name__
                if cls == "_Comment":
                    continue
                el_name = etree.QName(element.tag).localname
                if el_name == 'title':
                    self.title = element.text
                elif el_name == 'ns':
                    self.ns_prefixes[element.attrib['prefix']] = element.attrib['uri']
                elif el_name == 'pattern':
                    pattern = Pattern()
                    pattern.read_from_element(element)
                    self.patterns.append(pattern)
                elif el_name == 'include':
                    pattern = Pattern()
                    pattern.read_from_file(element.attrib['href'])
                    self.patterns.append(pattern)
                else:
                    raise SchematronException("Unknown element in schematron file: %s" % element.tag)

    def find_pattern(self, id):
        for pattern in self.patterns:
            if pattern.id == id:
                return pattern
        raise SchematronException("Can't find pattern %s" % id)

    def process_abstract_patterns(self):
        for pattern in self.patterns:
            if pattern.isa is not None:
                # print("applying %s to %s" % (pattern.isa, pattern.id))
                # print("rule count: %d" % len(pattern.rules))
                abstract = self.find_pattern(pattern.isa)
                # for pk,pv in pattern.variables.items():
                # Do Note: abstract is the pattern defining the rules; the isa origin defines the parameters
                for rule in abstract.rules:
                    rule.context = abstract_replace_vars(rule.context, pattern.variables)
                    for assertion in rule.assertions:
                        assertion.test = abstract_replace_vars(assertion.test, pattern.variables)

    def validate_document(self, xml_doc):
        """
        Validates the given xml document against this schematron schema.

        :return: a tuple ([errors], [warnings])
        """
        errors = []
        warnings = []
        for p in self.patterns:

            parser = XPath2Parser(self.ns_prefixes, p.variables)

            # Variables themselves can be expressions,
            # so we evaluate them here, and replace the originals
            # with the result of the evaluation
            if p.variables and 's' in p.variables:
                for name,value in parser.variables.items():
                    root_node = parser.parse(value)
                    context = XPathContext(root=xml_doc)
                    result = root_node.evaluate(context)
                    parser.variables[name] = result


            for r in p.rules:
                # Contexts are essentially a findall(), so if it is not absolute, make it a selector
                # that finds them all
                if not r.context.startswith('/'):
                    r.context = "//" + r.context
                # If the context is the literal '/', pass 'None' as the context item to elementpath
                if r.context == '/':
                    elements = [None]
                else:
                    elements = select(xml_doc, r.context, namespaces=self.ns_prefixes, variables=parser.variables)

                for element in elements:
                    # Important NOTE: the XPathContext can be modified by the evaluator!
                    # Not sure if this is intentional, but we need to make sure we re-initialize it
                    # for every assertion.
                    for a in r.assertions:
                        context = XPathContext(root=xml_doc, item=element)
                        self.msg(3, "Start test: %s" % a.id)
                        self.msg(4, "Test context: %s" % str(r.context))
                        self.msg(4, "Test expression: %s" % a.test)
                        root_token = parser.parse(a.test)

                        result = root_token.evaluate(context=context)
                        if not result:
                            self.msg(5, "Failed assertion")
                            self.msg(5, "Pattern: %s" % p.id)
                            self.msg(5, "Variables:")
                            for k, v in p.variables.items():
                                self.msg(5, "  %s: %s" % (k, v))
                            self.msg(5, "Context root: %s" % str(xml_doc.getroot()))
                            self.msg(5, "Context item: %s" % r.context)
                            self.msg(5, "CONTEXT ELEMENT: " + str(element))
                            if 'id' in a.__dict__:
                                self.msg(5, "Id: " + a.id)
                            self.msg(5, "Test: '%s'" % a.test)
                            self.msg(5, "Result: %s" % str(result))

                            if a.flag == "warning":
                                warnings.append(a)
                            else:
                                self.msg(5, "ELEMENTS: " + str(elements))
                                # raise Exception(self.file_path)
                                errors.append(a)

        return (errors, warnings)


class Pattern(object):
    def __init__(self):
        self.abstract = False
        self.isa = None

        # is there a difference between let and param statements?
        self.variables = {}

        self.id = None
        self.rules = []

    def read_from_element(self, p_element):
        self.id = p_element.attrib["id"]
        if "abstract" in p_element.attrib and p_element.attrib['abstract'] == 'true':
            self.abstract = True
        if "is-a" in p_element.attrib:
            self.isa = p_element.attrib['is-a']

        for element in p_element:
            cls = element.__class__.__name__
            if cls == "_Comment":
                continue
            el_name = etree.QName(element.tag).localname
            if el_name == 'rule':
                rule = Rule()
                rule.read_from_element(element, self.variables)
                self.rules.append(rule)
            elif el_name == 'let' or el_name == 'param':
                p_name = element.attrib['name']
                p_value = element.attrib['value']
                self.variables[p_name] = p_value
            else:
                raise SchematronException("Unknown element in pattern: %s: %s" % (self.id, element.tag))

    def read_from_file(self, file_path):
        # print("[XX] processing %s" % file_path)
        xml = etree.parse(file_path)
        with WorkingDirectory(os.path.dirname(file_path)):
            self.read_from_element(xml.getroot())


class Rule(object):
    def __init__(self):
        self.context = None
        self.assertions = []

    def read_from_element(self, r_element, variables):
        self.context = r_element.attrib['context']
        for element in r_element:
            cls = element.__class__.__name__
            if cls == "_Comment":
                continue
            el_name = etree.QName(element.tag).localname
            if el_name == 'assert':
                assertion = Assertion()
                assertion.read_from_element(element, variables)
                self.assertions.append(assertion)
            else:
                raise SchematronException("Unknown element in rule with context %s: %s" % (self.context, element.tag))


class Assertion(object):
    def __init__(self):
        self.id = "unset"
        self.test = None
        self.flag = None
        self.text = None

    def read_from_element(self, a_element, variables):
        self.test = a_element.attrib['test']
        if 'id' in a_element.attrib:
            self.id = a_element.attrib['id']
        if 'flag' in a_element.attrib:
            self.flag = a_element.attrib['flag']
        else:
            self.flag = "fatal"
        self.text = a_element.text