
#
# This is a schematron implemenation in python
#
# It uses elementpath to support XPath2 expressions
#

# Copyright (c) 2020 Ionite
# See LICENSE for the license

from lxml import etree
import os
from .xsl_generator import schema_to_xsl
from elementpath import XPath2Parser, XPathContext, select

class SchematronException(Exception):
    pass

def abstract_replace_vars(text, variables):
    s = text
    # Reverse sort them by length, so a basic replace() call works
    keys = sorted(variables.keys(), key=len, reverse=True)
    for key in keys:
        s = s.replace("$%s" % key, variables[key])
    return s

class WorkingDirectory(object):
    def __init__(self, new_directory):
        self.new_directory = new_directory
        self.original_directory = os.getcwd()

    def __enter__(self):
        os.chdir(self.new_directory)

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.chdir(self.original_directory)

class Schema(object):
    def __init__(self):
        self.title = None
        self.file_path = None

        # Prefixes is a mapping of prefix to uri
        self.ns_prefixes = {}
        # A list of patterns
        self.patterns = []

    def read_from_file(self, file_path):
        self.file_path = file_path
        xml = etree.parse(file_path)
        #print("[XX] processing %s" % file_path)
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
                #print("applying %s to %s" % (pattern.isa, pattern.id))
                #print("rule count: %d" % len(pattern.rules))
                abstract = self.find_pattern(pattern.isa)
                #for pk,pv in pattern.variables.items():
                # Do Note: abstract is the pattern defining the rules; the isa origin defines the parameters
                for rule in abstract.rules:
                    rule.context = abstract_replace_vars(rule.context, pattern.variables)
                    for assertion in rule.assertions:
                        assertion.test = abstract_replace_vars(assertion.test, pattern.variables)

    def to_xsl_str(self):
        return schema_to_xsl(self)

    def validate_document(self, xml_doc):
        """
        Validates the given xml document against this schematron schema.

        :return: a tuple ([errors], [warnings])
        """
        errors = []
        warnings = []
        for p in self.patterns:

            parser = XPath2Parser(self.ns_prefixes, p.variables)

            # print("[XX] %s has %d rules" % (p.id, len(p.rules)))
            for r in p.rules:

                # Is this a bug in elementpath or should we simply not select a context?
                # See what elementpath does with context_item=None
                if r.context == '/':
                    elements = [None]
                else:
                    elements = select(xml_doc, r.context, namespaces=self.ns_prefixes, variables=p.variables)
                for element in elements:
                    # Important NOTE: the XPathContext can be modified by the evaluator!
                    # Not sure if this is intentional, but we need to make sure we re-initialize it
                    # for every assertion.
                    for a in r.assertions:
                        context = XPathContext(root=xml_doc, item=element)
                        #print("[XX] START TEST: '%s'" % a.id)
                        #print("[XX] TEST EXPR: '%s'" % a.test)
                        root_token = parser.parse(a.test)

                        #print("[XX] Pattern: %s" % p.id)
                        #print("[XX] Context root: %s" % str(xml_doc.getroot()))
                        #print("[XX] Context item: %s" % r.context)
                        #print("[XX] CONTEXT ELEMENT: " + str(element))
                        #if 'id' in a.__dict__:
                        #    print("[XX] Id: " + a.id)
                        #print("[XX] Test: '%s'" % a.test)
                        result = root_token.evaluate(context=context)
                        if not result:
                            print("[XX] Failed assertion")
                            print("[XX] Pattern: %s" % p.id)
                            print("[XX] Variables:")
                            for k,v in p.variables.items():
                                print("  %s: %s" % (k,v))
                            print("[XX] Context root: %s" % str(xml_doc.getroot()))
                            print("[XX] Context item: %s" % r.context)
                            print("[XX] CONTEXT ELEMENT: " + str(element))
                            if 'id' in a.__dict__:
                                print("[XX] Id: " + a.id)
                            print("[XX] Test: '%s'" % a.test)
                            print("[XX] Result: %s" % str(result))

                            if a.flag == "warning":
                                warnings.append(a)
                            else:
                                print("[XX] ELEMENTS: " + str(elements))
                                #raise Exception(self.file_path)
                                errors.append(a)
                        # pass

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
        #print("[XX] processing %s" % file_path)
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
