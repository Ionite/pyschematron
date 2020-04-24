
"""
This module contains the schematron elements, as defined in the schematron definition files
"""
import os

from lxml import etree

from pyschematron.exceptions import *
from pyschematron.util import WorkingDirectory, abstract_replace_vars
from pyschematron.query_bindings import xslt, xslt2, xpath2

QUERY_BINDINGS = {
    'None': xslt,
    'xslt': xslt,
    'xslt2': xslt2,
    'xpath2': xpath2
}

class Schema(object):
    def __init__(self, filename=None, verbosity=0):
        """
        Initialize a Schematron Schema object

        :param filename: If specified, parse the schematron definition in the given file
        :param verbosity: The verbosity level
        """
        self.title = None
        self.file_path = None
        self.verbosity = verbosity
        self.query_binding = None

        # Prefixes is a mapping of prefix to uri
        self.ns_prefixes = {}
        # A list of patterns
        self.patterns = []

        if filename is not None:
            self.read_from_file(filename)

    def set_query_binding(self, query_binding):
        if query_binding is None:
            self.query_binding = QUERY_BINDINGS['xslt'].instantiate()
        elif query_binding not in QUERY_BINDINGS:
            raise SchematronNotImplementedError("Query Binding '%s' is not supported by this implementation" % query_binding)
        else:
            self.query_binding = QUERY_BINDINGS[query_binding].instantiate()

    def msg(self, level, msg):
        if self.verbosity >= level:
            print(msg)

    def read_from_file(self, file_path, process_abstract_patterns=True):
        """
        Fully parses the given schematron file.

        :param file_path: The .sch file to parse
        :param process_abstract_patterns: Set to False to *not* automatically process the abstract patterns that are used
        :return: None
        """
        self.file_path = file_path
        xml = etree.parse(file_path)
        with WorkingDirectory(os.path.dirname(file_path)):
            root = xml.getroot()
            # Process the attributes
            self.set_query_binding(root.attrib.get('queryBinding'))

            # Process the elements
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
                    raise SchematronError("Unknown element in schematron file: %s" % element.tag)

        if process_abstract_patterns:
            self.process_abstract_patterns()

    def find_pattern(self, id):
        for pattern in self.patterns:
            if pattern.id == id:
                return pattern
        raise SchematronError("Can't find pattern %s" % id)

    def process_abstract_patterns(self):
        for pattern in self.patterns:
            if pattern.isa is not None:
                # print("applying %s to %s" % (pattern.isa, pattern.id))
                # print("rule count: %d" % len(pattern.rules))
                abstract = self.find_pattern(pattern.isa)
                # for pk,pv in pattern.variables.items():
                # Do Note: abstract is the pattern defining the rules; the isa origin defines the parameters
                for rule in abstract.rules:
                    rule.context = abstract_replace_vars(self.query_binding, rule.context, pattern.params)
                    for assertion in rule.assertions:
                        assertion.test = abstract_replace_vars(self.query_binding, assertion.test, pattern.params)


    def validate_document(self, xml_doc):
        """
        Validates the given xml document against this schematron schema.

        :return: a tuple ([errors], [warnings])
        """
        errors = []
        warnings = []

        # Idea for performance improvement:
        # - loop over the actual elements in the document
        # - while this element is not 'known', process rules as already done,
        #   but store a mapping of each element that is encountered in a rule context match to that rule
        # - process assertions when the element is encountered, but stop the rule loop, and move on to the next element
        # - if this element is already 'known', we can immediately process the assertions
        # - if not, continue the processing of rules

        for p in self.patterns:
            # We track the fired rule for each element, since every document node should only have one rule
            fired_rules = {}
            # Variables themselves can be expressions,
            # so we evaluate them here, and replace the originals
            # with the result of the evaluation
            if p.variables:
                for name,value in p.variables.items():
                    p.variables[name] = self.query_binding.interpret_let_statement(xml_doc, value, self.ns_prefixes, p.variables)

            for r in p.rules:
                # Contexts are essentially a findall(), so if it is not absolute, make it a selector
                # that finds them all
                # This may be query-binding-specific
                #if not r.context.startswith('/'):
                #    r.context = "/" + r.context
                # If the context is the literal '/', pass 'None' as the context item to elementpath
                if r.context == '/':
                    elements = [None]
                else:
                    elements = self.query_binding.get_context_elements(xml_doc, r.context, namespaces=self.ns_prefixes, variables=p.variables)

                for element in elements:
                    if element in fired_rules:
                        # Already matched a rule, skip this one
                        continue
                    fired_rules[element] = r.context
                    # Important NOTE: the XPathContext can be modified by the evaluator!
                    # Not sure if this is intentional, but we need to make sure we re-initialize it
                    # for every assertion.
                    for a in r.assertions:
                        self.msg(3, "Start test: %s" % a.id)
                        self.msg(4, "Test context: %s" % str(r.context))
                        self.msg(4, "Test expression: %s" % a.test)
                        result = self.query_binding.evaluate_assertion(xml_doc, element, self.ns_prefixes, p.variables, a.test)
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

        self.variables = {}

        self.params = {}

        self.id = None
        self.rules = []

    def read_from_element(self, p_element):
        self.id = p_element.attrib.get("id", "pattern")
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
            elif el_name == 'let':
                p_name = element.attrib['name']
                p_value = element.attrib['value']
                self.variables[p_name] = p_value
            elif el_name == 'param':
                p_name = element.attrib['name']
                p_value = element.attrib['value']
                self.params[p_name] = p_value
            else:
                raise SchematronError("Unknown element in pattern: %s: %s" % (self.id, element.tag))

    def read_from_file(self, file_path):
        # print("[XX] processing %s" % file_path)
        xml = etree.parse(file_path)
        with WorkingDirectory(os.path.dirname(file_path)):
            self.read_from_element(xml.getroot())


class Rule(object):
    def __init__(self):
        self.context = None
        self.assertions = []
        self.id = None

    def read_from_element(self, r_element, variables):
        self.context = r_element.attrib['context']
        self.id = r_element.attrib.get('id', "")
        for element in r_element:
            cls = element.__class__.__name__
            if cls == "_Comment":
                continue
            el_name = etree.QName(element.tag).localname
            if el_name == 'assert':
                assertion = Assertion(rule=self)
                assertion.read_from_element(element, variables)
                self.assertions.append(assertion)
            else:
                raise SchematronError("Unknown element in rule with context %s: %s" % (self.context, element.tag))


class Assertion(object):
    def __init__(self, rule=None):
        self.id = "unset"
        self.test = None
        self.flag = None
        self.text = None

        self.rule = rule

    def read_from_element(self, a_element, variables):
        self.test = a_element.attrib['test']
        if 'id' in a_element.attrib:
            self.id = a_element.attrib['id']
        if 'flag' in a_element.attrib:
            self.flag = a_element.attrib['flag']
        else:
            self.flag = "fatal"
        self.text = a_element.text