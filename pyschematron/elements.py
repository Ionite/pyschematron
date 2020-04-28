"""
This module contains the schematron elements, as defined in the schematron definition files
"""
import copy
import os

from lxml import etree

from pyschematron.exceptions import *
from pyschematron.util import WorkingDirectory, abstract_replace_vars
from pyschematron.query_bindings import xslt, xslt2, xpath2
from pyschematron.validation import ValidationContext, ValidationReport

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

        #
        # Specification properties (elements)
        #
        # <include> elements are processed directly when reading files
        self.title = None
        self.ns_prefixes = {}
        # self.p (TODO)
        self.variables = {}
        self.phases = {}
        self.patterns = {}
        # self.diagnostics

        # Specification properties (attributes)
        self.id = None
        self.default_phase = None
        self.see = None
        self.fpi = None
        self.xml_lang = None
        self.xml_space = None
        self.schemaVersion = None
        self.query_binding = None

        #
        # Implementation properties
        #
        self.file_path = None
        self.verbosity = verbosity

        if filename is not None:
            self.read_from_file(filename)

    def set_query_binding(self, query_binding):
        if query_binding is None:
            self.query_binding = QUERY_BINDINGS['xslt'].instantiate()
        elif query_binding not in QUERY_BINDINGS:
            raise SchematronNotImplementedError(
                "Query Binding '%s' is not supported by this implementation" % query_binding)
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
            self.id = root.attrib.get("id", "")
            self.see = root.attrib.get("see", "")
            self.fpi = root.attrib.get("fpi", "")
            self.xml_lang = root.attrib.get("xml:lang", "")
            self.xml_space = root.attrib.get("xml:space", "default")
            self.schemaVersion = root.attrib.get("schemaVersion", "")
            self.default_phase = root.attrib.get("defaultPhase", "#ALL")
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
                elif el_name == 'let':
                    self.variables[element.attrib['name']] = element.attrib['value']
                elif el_name == 'ns':
                    self.ns_prefixes[element.attrib['prefix']] = element.attrib['uri']
                elif el_name == 'pattern':
                    pattern = Pattern()
                    pattern.read_from_element(element)
                    if pattern.id in self.patterns:
                        raise SchematronError("Duplicate pattern: %s" % pattern.id)
                    self.patterns[pattern.id] = pattern
                elif el_name == 'phase':
                    phase = Phase()
                    phase.read_from_element(element)
                    self.phases[phase.id] = phase
                elif el_name == 'include':
                    pattern = Pattern()
                    pattern.read_from_file(element.attrib['href'])
                    if pattern.id in self.patterns:
                        raise SchematronError("Duplicate pattern: %s" % pattern.id)
                    self.patterns[pattern.id] = pattern
                else:
                    raise SchematronError("Unknown element in schematron file: %s" % element.tag)

        if process_abstract_patterns:
            self.process_abstract_patterns()

    def get_pattern(self, pattern_id):
        if pattern_id in self.patterns:
            return self.patterns[pattern_id]
        else:
            raise SchematronError("Unknown pattern: %s" % pattern_id)

    def process_abstract_patterns(self):
        for pattern in self.patterns.values():
            if pattern.isa is not None:
                # print("applying %s to %s" % (pattern.isa, pattern.id))
                # print("rule count: %d" % len(pattern.rules))
                abstract = self.get_pattern(pattern.isa)
                pattern.isa = None
                # for pk,pv in pattern.variables.items():
                # Do Note: abstract is the pattern defining the rules; the isa origin defines the parameters
                for rule in [r.copy() for r in abstract.rules]:
                    # Copy the rule, with the parameters replaced, into the 'is-a' pattern
                    rule.context = abstract_replace_vars(self.query_binding, rule.context, pattern.params)
                    for assertion in rule.assertions:
                        assertion.test = abstract_replace_vars(self.query_binding, assertion.test, pattern.params)
                    pattern.rules.append(rule)

    def get_patterns_for_phase(self, phase_name):
        if phase_name == "#ALL":
            return [pattern for pattern in self.patterns.values() if not pattern.abstract]
        else:
            result = []
            phase = self.get_phase(phase_name)
            for pattern_id in phase.active_patterns:
                pattern = self.get_pattern(pattern_id)
                if pattern.abstract:
                    raise SchematronError("Phase %s contains active pattern %s, only non-abstract patterns can be specified" % (phase_name, pattern_id))
                result.append(pattern)
            return result

    def get_phase(self, phase_name):
        if phase_name in self.phases:
            return self.phases[phase_name]
        else:
            raise SchematronError("Unknown phase: %s" % phase_name)

    def validate_document(self, xml_doc, phase="#DEFAULT"):
        """
        Validates the given xml document against this schematron schema.

        :return: a tuple ([errors], [warnings])
        """
        report = ValidationReport()

        if phase == "#DEFAULT":
            phase = self.default_phase

        patterns = self.get_patterns_for_phase(phase)

        # Idea for performance improvement:
        # - loop over the actual elements in the document
        # - while this element is not 'known', process rules as already done,
        #   but store a mapping of each element that is encountered in a rule context match to that rule
        # - process assertions when the element is encountered, but stop the rule loop, and move on to the next element
        # - if this element is already 'known', we can immediately process the assertions
        # - if not, continue the processing of rules

        schema_context = ValidationContext(self, xml_doc)
        if phase != "#ALL":
            schema_context.add_variables(self.phases[phase].variables)

        for p in patterns:
            # We track the fired rule for each element, since every document node should only have one rule
            fired_rules = {}
            # Variables themselves can be expressions,
            # so we evaluate them here, and replace the originals
            # with the result of the evaluation
            pattern_context = schema_context.copy()
            pattern_context.set_pattern(p)

            for r in p.rules:
                rule_context = pattern_context.copy()
                rule_context.set_rule(r)

                report.add_fired_rule(rule_context)

                # If the context is the literal '/', pass 'None' as the context item to elementpath
                elements = rule_context.get_rule_context_elements()

                for element in elements:
                    if element in fired_rules:
                        # Already matched a rule, skip this one
                        continue
                    # Mark this element as having fired a rule (so it can be skipped later, if
                    # it matches other rules as well)
                    fired_rules[element] = r.context

                    rule_context.validate_assertions(element, report)

        return report

class Phase(object):
    def __init__(self):
        self.id = None
        self.active_patterns = []
        self.variables = {}

    def read_from_element(self, phase_element):
        self.id = phase_element.attrib['id']
        for element in phase_element:
            cls = element.__class__.__name__
            if cls == "_Comment":
                continue
            el_name = etree.QName(element.tag).localname
            if el_name == 'active':
                self.active_patterns.append(element.attrib["pattern"])
            elif el_name == 'let':
                p_name = element.attrib['name']
                p_value = element.attrib['value']
                self.variables[p_name] = p_value
            else:
                raise SchematronError("Unknown element in phase: %s: %s" % (self.id, element.tag))


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
        xml = etree.parse(file_path)
        with WorkingDirectory(os.path.dirname(file_path)):
            self.read_from_element(xml.getroot())

class Rule(object):
    def __init__(self):
        self.context = None
        self.assertions = []
        self.variables = {}
        self.id = None

    def copy(self):
        new_rule = Rule()
        new_rule.context = self.context
        new_rule.id = self.id
        new_rule.assertions = self.assertions[:]
        new_rule.variables = copy.deepcopy(self.variables)
        return new_rule

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
            elif el_name == 'let':
                p_name = element.attrib['name']
                p_value = element.attrib['value']
                self.variables[p_name] = p_value
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
            self.flag = "error"
        self.text = a_element.text
