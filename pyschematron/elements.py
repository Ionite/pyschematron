"""
This module contains the schematron elements, as defined in the schematron definition files
"""
import copy
import os
import re

from collections import OrderedDict
from lxml import etree

from elementpath import xpath_context
from elementpath import XPath2Parser

from pyschematron.exceptions import *
from pyschematron.util import WorkingDirectory, abstract_replace_vars
from pyschematron.query_bindings import xslt, xslt2, xpath2
from pyschematron.validation import ValidationContext, ValidationReport
from pyschematron.xml import xml_util
from pyschematron.xml.xsl_generator import E

QUERY_BINDINGS = {
    'None': xslt,
    'xslt': xslt,
    'xslt2': xslt2,
    'xpath2': xpath2
}

class SchemaObject(object):
    def __init__(self, parent):
        self.parent = parent

    def get_schema(self):
        """Return the top-level schema for this object"""
        parent = self.parent
        while parent.parent is not None:
            parent = parent.parent
        return parent

class ComplexText(SchemaObject):
    """
    Base class for elements that contain text elements, e.g. <p>, or <assert>
    This class that must be instantiated through other classes
    """

    def __init__(self, parent, xml_element=None):
        super().__init__(parent)
        if not hasattr(self, 'NAME'):
            raise Exception("base class ComplexText should not be instantiated directly")

        self.parts = []
        if xml_element is not None:
            self.from_xml(xml_element)

    def from_xml_child(self, element):
        el_name = etree.QName(element.tag).localname
        if el_name == 'span':
            self.parts.append(SpanText(self, element))
        elif el_name == 'emph':
            self.parts.append(EmphText(self, element))
        elif el_name == 'dir':
            self.parts.append(DirText(self, element))
        elif el_name == 'name':
            self.parts.append(NameText(self, element))
        elif el_name == 'value-of':
            self.parts.append(ValueOfText(self, element))
        else:
            raise SchematronError("TODO: \"%s\"" % el_name)
        if element.tail is not None:
            self.parts.append(BasicText(self, element.tail))

    def from_xml(self, element):
        if len(self.parts) > 0:
            #raise SchematronError("from_xml already called")
            return
        if element.text:
            self.parts.append(BasicText(self, element.text))
        for child in element.getchildren():
            self.from_xml_child(child)

    def to_minimal_xml(self):
        element = xml_util.create(self.NAME)
        subelement = None
        for part in self.parts:
            if isinstance(part, BasicText):
                if subelement is None:
                    element.text = part.to_string()
                else:
                    subelement.tail = part.to_string()
            else:
                subelement = part.to_minimal_xml()
                element.append(subelement)
        return element

    def to_string(self, resolve=False, xml_doc=None, current_element=None, namespaces=None):
        result = []
        for part in self.parts:
            result.append(part.to_string(resolve, xml_doc, current_element, namespaces))
        return "".join(result)

    def to_xsl(self):
        element = E('sch', self.NAME)
        subelement = None
        for part in self.parts:
            if part.__class__.__name__ == 'BasicText':
                if subelement is None:
                    element.text = part.text
                else:
                    subelement.tail = part.text
            else:
                subelement = part.to_xsl()
                element.append(subelement)
        return element



class Schema(object):
    def __init__(self, filename=None, xml_element=None, verbosity=0):
        """
        Initialize a Schematron Schema object

        :param filename: If specified, parse the schematron definition in the given file
        :param verbosity: The verbosity level
        """

        #
        # Specification properties (attributes)
        self.id = None
        self.icon = None
        self.default_phase = None
        self.see = None
        self.fpi = None
        self.xml_lang = None
        self.xml_space = None
        self.schema_version = None
        self.query_binding_name = None
        self.query_binding = None


        # Specification properties (elements)
        self.title = None
        self.ns_prefixes = OrderedDict()
        self.paragraphs = []
        self.variables = {}
        self.phases = {}
        self.patterns = {}
        # Another paragraphs?
        self.diagnostics = None
        # <include> elements are processed directly when reading files

        #
        # Implementation properties
        #
        self.parent = None
        self.file_path = None
        self.verbosity = verbosity
        self.abstract_patterns_processed = False
        self.abstract_rules_processed = False

        self.elements_read = 0
        self.element_number_of_first_pattern = None

        if filename is not None:
            self.read_from_file(filename)
        elif xml_element is not None:
            self.from_xml(xml_element)

    def set_query_binding(self, query_binding):
        if query_binding is None:
            self.query_binding_name = 'xslt'
            self.query_binding = QUERY_BINDINGS['xslt'].instantiate()
        elif query_binding not in QUERY_BINDINGS:
            raise SchematronNotImplementedError(
                "Query Binding '%s' is not supported by this implementation" % query_binding)
        else:
            self.query_binding_name = query_binding
            self.query_binding = QUERY_BINDINGS[query_binding].instantiate()

    def msg(self, level, msg):
        if self.verbosity >= level:
            print(msg)

    def _parse_xml_child(self, element):
        el_name = etree.QName(element.tag).localname
        if el_name == 'title':
            self.title = element.text
        elif el_name == 'let':
            self.variables[element.attrib['name']] = element.attrib.get('value', element.text)
        elif el_name == 'ns':
            self.ns_prefixes[element.attrib['prefix']] = element.attrib['uri']
        elif el_name == 'pattern':
            # Keep track of where we found the first pattern, so we can generate mode identifiers
            # in the same way as the skeleton implementation does
            if self.element_number_of_first_pattern is None:
                self.element_number_of_first_pattern = self.elements_read
            pattern = Pattern(self, element)
            if pattern.id == '':
                pattern.id = "#%d" % len(self.patterns)
            if pattern.id in self.patterns:
                raise SchematronError("Duplicate pattern id: %s" % pattern.id)
            self.patterns[pattern.id] = pattern
        elif el_name == 'phase':
            phase = Phase(self, element)
            self.phases[phase.id] = phase
        elif el_name == 'include':
            href = element.attrib['href']
            included_doc = etree.parse(href)
            with WorkingDirectory(os.path.dirname(os.path.abspath(href))):
                self._parse_xml_child(included_doc.getroot())
        elif el_name == 'p':
            self.paragraphs.append(ParagraphText(self, element))
        elif el_name == 'diagnostics':
            if self.diagnostics is not None:
                raise SchematronError("diagnostics element can only occur once per schema or pattern")
            self.diagnostics = Diagnostics(self, element)
        else:
            raise SchematronError("Unknown element in schema: %s" % element.tag)
        self.elements_read += 1

    def from_xml(self, root):
        # Process the attributes
        self.id = root.attrib.get("id", "")
        self.icon = root.attrib.get("icon")
        self.see = root.attrib.get("see", "")
        self.fpi = root.attrib.get("fpi", "")
        self.xml_lang = root.attrib.get("xml:lang", "")
        self.xml_space = root.attrib.get("xml:space", "default")
        self.schema_version = root.attrib.get("schemaVersion", "")
        self.default_phase = root.attrib.get("defaultPhase", "#ALL")
        self.set_query_binding(root.attrib.get('queryBinding'))

        # Process the elements
        for element in root:
            # Ignore comments
            cls = element.__class__.__name__
            if cls == "_Comment":
                continue
            self._parse_xml_child(element)

    def read_from_file(self, file_path, process_abstract_patterns=True, process_abstract_rules=True):
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
            self.from_xml(root)

        if process_abstract_patterns:
            self.process_abstract_patterns()
        if process_abstract_rules:
            self.process_abstract_rules()

    def get_pattern(self, pattern_id):
        if pattern_id in self.patterns:
            return self.patterns[pattern_id]
        else:
            raise SchematronError("Unknown pattern: %s" % pattern_id)

    def process_abstract_rules(self):
        import sys
        for pattern in self.patterns.values():
            new_rules = []
            for rule in pattern.rules:
                if rule.extends is not None and len(rule.extends) > 0:
                    for extends in rule.extends:
                        orig_rule = pattern.get_rule(extends)
                        for assertion in orig_rule.assertions:
                            rule.assertions.append(assertion)
                        for report in orig_rule.reports:
                            rule.reports.append(report)
                    rule.extends = []
                if not rule.abstract:
                    new_rules.append(rule)
            # pattern.rules = new_rules
        self.abstract_rules_processed = True

    def process_abstract_patterns(self):
        """
        Replaces the relevant data in 'is-a' patterns, and removes all abstract patterns
        :return:
        """
        new_patterns = {}
        for pattern in self.patterns.values():
            if pattern.abstract:
                continue
            elif pattern.is_a is not None:
                # print("applying %s to %s" % (pattern.isa, pattern.id))
                # print("rule count: %d" % len(pattern.rules))
                abstract = self.get_pattern(pattern.is_a)
                pattern.is_a = None
                # for pk,pv in pattern.variables.items():
                # Do Note: abstract is the pattern defining the rules; the isa origin defines the parameters
                for rule in [r.copy() for r in abstract.rules]:
                    # Copy the rule, with the parameters replaced, into the 'is-a' pattern
                    rule.context = abstract_replace_vars(self.query_binding, rule.context, pattern.params)
                    for assertion in rule.assertions:
                        assertion.test = abstract_replace_vars(self.query_binding, assertion.test, pattern.params)
                    for report in rule.reports:
                        report.test = abstract_replace_vars(self.query_binding, report.test, pattern.params)
                    pattern.rules.append(rule)
            new_patterns[pattern.id] = pattern
        self.patterns = new_patterns
        self.abstract_patterns_processed = True

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

    def to_minimal_xml_document(self):
        return etree.ElementTree(self.to_minimal_xml())

    def to_minimal_xml(self, minimal=False):
        """
        Creates a minimal syntax schema according to section 6.2 of the specification.
        TODO: non-minimal output
        :return: An ElementTree with the current Schema specification in minimal form
        """
        if not self.abstract_patterns_processed:
            self.process_abstract_patterns()
        root = xml_util.create('schema', add_nsmap=True)
        xml_util.set_attr(root, 'id', self.id)
        xml_util.set_attr(root, 'defaultPhase', self.default_phase)
        xml_util.set_attr(root, 'schemaVersion', self.schema_version)
        xml_util.set_attr(root, 'queryBinding', self.query_binding_name)
        xml_util.set_variables(root, self.variables)

        for phase in self.phases.values():
            root.append(phase.to_minimal_xml())
        for pattern in self.patterns.values():
            root.append(pattern.to_minimal_xml())
        return root

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
            self.msg(5, "Validating pattern: " + str(p.id))
            # We track the fired rule for each element, since every document node should only have one rule
            fired_rules = {}
            # Variables themselves can be expressions,
            # so we evaluate them here, and replace the originals
            # with the result of the evaluation
            pattern_context = schema_context.copy()
            pattern_context.set_pattern(p)

            for r in p.rules:
                self.msg(5, "Validating rule with context: " + str(r.context))
                if r.abstract:
                    continue
                rule_context = pattern_context.copy()

                # TODO: should this be done for every matching element?
                report.add_fired_rule(rule_context)
                rule_context.set_rule(r)

                # If the context is the literal '/', pass 'None' as the context item to elementpath
                elements = rule_context.get_rule_context_elements()
                self.msg(5, "Number of matching elements: %s" % len(elements))

                for element in elements:
                    rule_context.add_rule_variables(r, element)
                    if element in fired_rules:
                        # Already matched a rule, skip this one
                        continue
                    # Mark this element as having fired a rule (so it can be skipped later, if
                    # it matches other rules as well)
                    fired_rules[element] = r.context

                    rule_context.validate_assertions(element, report)

        return report


class Phase(SchemaObject):
    def __init__(self, parent, xml_element=None):
        super().__init__(parent)
        self.id = None
        self.icon = None
        self.see = None
        self.fpi = None
        self.xml_lang = None
        self.xml_space = None

        self.paragraphs = []
        self.variables = {}
        self.active_patterns = []

        if xml_element is not None:
            self.from_xml(xml_element)

    def _parse_xml_child(self, element):
        el_name = etree.QName(element.tag).localname
        if el_name == 'p':
            self.paragraphs.append(ParagraphText(element))
        elif el_name == 'let':
            p_name = element.attrib['name']
            p_value = element.attrib['value']
            self.variables[p_name] = p_value
        elif el_name == 'active':
            # TODO: it appears 'active' can also contain text, dir, emph, and span;
            # this is not implemented atm; but we probably need to make a class of that
            # as well (can just subclass ComplexText)
            self.active_patterns.append(element.attrib["pattern"])
        elif el_name == 'include':
            href = element.attrib['href']
            included_doc = etree.parse(href)
            with WorkingDirectory(os.path.dirname(os.path.abspath(href))):
                self._parse_xml_child(included_doc.getroot())
        else:
            raise SchematronError("Unknown element in phase: %s: %s" % (self.id, element.tag))

    def from_xml(self, phase_element):
        self.id = phase_element.attrib['id']
        for element in phase_element:
            cls = element.__class__.__name__
            if cls == "_Comment":
                continue
            self._parse_xml_child(element)

    def to_minimal_xml(self):
        element = xml_util.create('phase')
        xml_util.set_attr(element, 'id', self.id)
        xml_util.set_variables(element, self.variables)

        for pattern in self.active_patterns:
            active_element = xml_util.create('active')
            xml_util.set_attr(active_element, 'pattern', pattern)
            element.append(active_element)

        return element


class Pattern(SchemaObject):
    def __init__(self, parent, xml_element=None):
        super().__init__(parent)

        # Specification properties (attributes)
        self.abstract = False
        self.is_a = None
        self.id = None
        self.icon = None
        self.see = None
        self.fpi = None
        self.xml_lang = None
        self.xml_space = None
        self.title = None

        # Specification properties (elements)
        self.paragraphs = []
        self.variables = {}
        self.rules = []
        self.params = {}
        # <include> files are handled directly

        if xml_element is not None:
            self.from_xml(xml_element)

    def _parse_xml_child(self, element):
        el_name = etree.QName(element.tag).localname
        if el_name == 'title':
            self.title = element.text
        elif el_name == 'p':
            self.paragraphs.append(ParagraphText(element))
        elif el_name == 'let':
            p_name = element.attrib['name']
            p_value = element.attrib['value']
            self.variables[p_name] = p_value
        elif el_name == 'rule':
            rule = Rule(self, element, self.variables)
            self.rules.append(rule)
        elif el_name == 'param':
            p_name = element.attrib['name']
            p_value = element.attrib['value']
            self.params[p_name] = p_value
        elif el_name == 'include':
            href = element.attrib['href']
            included_doc = etree.parse(href)
            with WorkingDirectory(os.path.dirname(os.path.abspath(href))):
                self._parse_xml_child(included_doc.getroot())
        else:
            raise SchematronError("Unknown element in pattern: %s: %s" % (self.id, element.tag))

    def from_xml(self, p_element):
        if "abstract" in p_element.attrib and p_element.attrib['abstract'] == 'true':
            self.abstract = True
        if "is-a" in p_element.attrib:
            self.is_a = p_element.attrib['is-a']
        self.id = p_element.attrib.get("id", "")
        self.icon = p_element.attrib.get("icon")
        self.see = p_element.attrib.get("see")
        self.fpi = p_element.attrib.get("fpi")
        self.xml_lang = p_element.attrib.get("xml:lang")
        self.xml_space = p_element.attrib.get("xml:space")

        for element in p_element:
            cls = element.__class__.__name__
            if cls == "_Comment":
                continue
            self._parse_xml_child(element)

    def read_from_file(self, file_path):
        xml = etree.parse(file_path)
        with WorkingDirectory(os.path.dirname(file_path)):
            self.from_xml(xml.getroot())

    def to_minimal_xml(self):
        element = xml_util.create('pattern')
        xml_util.set_attr(element, 'id', self.id)
        xml_util.set_attr(element, 'title', self.title)
        xml_util.set_variables(element, self.variables)
        for rule in self.rules:
            element.append(rule.to_minimal_xml())
        return element

    def get_rule(self, id):
        for r in self.rules:
            if r.id == id:
                return r
        raise SchematronError("Error: unknown rule with id '%s'" % id)


class Rule(SchemaObject):
    def __init__(self, parent, xml_element=None, variables=None):
        super().__init__(parent)

        self.flag = None
        self.abstract = False
        self.context = None
        self.id = None
        self.icon = None
        self.see = None
        self.fpi = None
        self.xml_lang = None
        self.xml_space = None
        self.role = None
        self.subject = None

        self.variables = OrderedDict()
        self.assertions = []
        self.reports = []
        self.extends = []
        # includes are handled directly when parsing

        if xml_element is not None:
            self.from_xml(xml_element, variables)

    def copy(self):
        new_rule = Rule(self.parent)
        new_rule.context = self.context
        new_rule.id = self.id
        new_rule.assertions = self.assertions[:]
        new_rule.reports = self.reports[:]
        new_rule.variables = copy.deepcopy(self.variables)
        new_rule.abstract = self.abstract
        return new_rule

    def _parse_xml_child(self, element, variables):
        el_name = etree.QName(element.tag).localname
        if el_name == 'p':
            self.paragraphs.append(ParagraphText(element))
        elif el_name == 'let':
            p_name = element.attrib['name']
            p_value = element.attrib.get('value')
            self.variables[p_name] = p_value
        elif el_name == 'assert':
            assertion = Assertion(self, element)
            self.assertions.append(assertion)
        elif el_name == 'report':
            report = Report(self, element)
            self.reports.append(report)
        elif el_name == 'extends':
            self.extends.append(element.attrib['rule'])
        elif el_name == 'include':
            href = element.attrib['href']
            included_doc = etree.parse(href)
            with WorkingDirectory(os.path.dirname(os.path.abspath(href))):
                self._parse_xml_child(included_doc.getroot())
        else:
            raise SchematronError("Unknown element in rule with context %s: %s" % (self.context, element.tag))

    def from_xml(self, r_element, variables):
        self.id = r_element.attrib.get('id', "")
        self.abstract = r_element.attrib.get('abstract', False)
        if self.abstract:
            if self.id == '':
                raise SchematronError("Abstract rules must have a non-empty id attribute")
            if 'context' in r_element.attrib:
                raise SchematronError("Abstract rules cannot have a context attribute")
        else:
            self.context = r_element.attrib['context']
        for element in r_element:
            cls = element.__class__.__name__
            if cls == "_Comment":
                continue
            self._parse_xml_child(element, variables)

    def to_minimal_xml(self):
        element = xml_util.create('rule')
        xml_util.set_attr(element, 'id', self.id)
        xml_util.set_attr(element, 'context', self.context)
        xml_util.set_variables(element, self.variables)
        for assertion in self.assertions:
            element.append(assertion.to_minimal_xml())
        for report in self.reports:
            element.append(report.to_minimal_xml())
        return element


class RuleTest(ComplexText):
    """
    Base class for the tests that are part of rules. Each test can be an Assertion or a Report.
    This class is itself a subclass of 'ComplextText', as these can contain complex text values
    for assertion or report messages.
    """

    def __init__(self, parent, xml_element=None):
        super().__init__(parent, xml_element)
        self.id = None
        self.test = None
        self.flag = None
        # TODO: remove self.text
        #self.text = None
        self.diagnostic_ids = []

        if xml_element is not None:
            self.from_xml(xml_element)

    def from_xml(self, a_element):
        super().from_xml(a_element)
        self.test = a_element.attrib['test']
        if 'id' in a_element.attrib:
            self.id = a_element.attrib['id']
        #if a_element.text is not None:
        #    self.text = a_element.text.strip()
        #    self.new_text = TextElement(a_element)
        if 'diagnostics' in a_element.attrib:
            self.diagnostic_ids = re.split("\s+", a_element.attrib['diagnostics'])

    def to_minimal_xml(self):
        element = super().to_minimal_xml()
        xml_util.set_attr(element, 'test', self.test)
        xml_util.set_attr(element, 'flag', self.flag)
        return element

    def get_diagnostic(self, diagnostic_id):
        if diagnostic_id in self.rule.pattern.schema.diagnostics:
            return self.rule.pattern.schema.diagnostics[diagnostic_id]

    def get_diagnostic_text(self, diagnostic_id):
        if diagnostic_id not in self.get_schema().diagnostics:
            raise SchematronError("No diagnostic found with id %s" % diagnostic_id)
        return self.get_schema().diagnostics[diagnostic_id].to_string()
        #if diagnostic_id in self.rule.pattern.schema.diagnostics:
        #    return self.rule.pattern.schema.diagnostics[diagnostic_id].text


class Assertion(RuleTest):
    NAME = 'assert'
    # Assert statements can have a flag attribute
    def from_xml(self, a_element):
        super().from_xml(a_element)
        if 'flag' in a_element.attrib:
            self.flag = a_element.attrib['flag']
        else:
            self.flag = "error"


class Report(RuleTest):
    NAME = 'report'

    def to_assert(self):
        """
        Returns a clone of this Report as an Assert, with the test member inverted
        :return:
        """
        assertion = Assertion(self.parent)
        assertion.__dict__.update(self.__dict__)
        assertion.test = "not(%s)" % self.test
        return assertion

    def to_minimal_xml(self):
        """
        This inverts the statement of the report, and returns the result as
        an <assert> xml element, as per specification section 6.2
        :return: An <assert> xml Element
        """
        assertion = self.to_assert()
        return assertion.to_minimal_xml()


class Diagnostics(SchemaObject):
    def __init__(self, parent, xml_element=None):
        super().__init__(parent)

        self.diagnostics = {}
        if xml_element is not None:
            self.from_xml(xml_element)

    def from_xml(self, d_element):
        for element in d_element:
            cls = element.__class__.__name__
            if cls == "_Comment":
                continue
            el_name = etree.QName(element.tag).localname
            if el_name == 'diagnostic':
                diagnostic = Diagnostic(self, element)
                self.diagnostics[diagnostic.id] = diagnostic
            else:
                raise SchematronError("Unknown element in diagnostics element: %s" % (element.tag))

    def __iter__(self):
        return self.diagnostics.__iter__()

    def __getitem__(self, key):
        return self.diagnostics[key]


class Diagnostic(ComplexText):
    NAME = 'diagnostic'
    def __init__(self, parent, xml_element=None):
        super().__init__(parent, xml_element)
        self.id = None
        self.language = None
        self.text = None
        self.new_text = None
        if xml_element is not None:
            self.from_xml(xml_element)

    def from_xml(self, element):
        super().from_xml(element)
        self.id = element.attrib['id']
        self.language = element.attrib.get('{http://www.w3.org/XML/1998/namespace}lang')
        self.text = element.text
        self.new_text = TextElement(self, element)


class TextElement(SchemaObject):
    """Contains the text part of objects like Assertion and Report

    These text parts can themselves contain XML elements such as <emph> or <value-of>, so this class keeps a list of the individual parts
    that make a text section.
    """

    def __init__(self, parent, xml_element=None):
        super().__init__(parent)
        self.parts = []

        if xml_element is not None:
            self.from_xml(xml_element)

    def from_xml_child(self, element):
        el_name = etree.QName(element.tag).localname
        if el_name == 'name':
            self.parts.append(NameText(self, element))
        elif el_name == 'p':
            self.parts.append(ParagraphText(self, element))
        elif el_name == 'value-of':
            self.parts.append(ValueOfText(self, element))
        elif el_name == 'span':
            self.parts.append(SpanText(self, element))
        elif el_name == 'emph':
            self.parts.append(EmphText(self, element))
        elif el_name == 'dir':
            self.parts.append(DirText(self, element))
        else:
            raise SchematronError("TODO: '%s'" % el_name)
        if element.tail is not None:
            self.parts.append(BasicText(self, element.tail))

    def from_xml(self, element):
        if element.text:
            self.parts.append(BasicText(self, element.text))
        for child in element.getchildren():
            self.from_xml_child(child)


    def to_string(self, resolve=False, xml_doc=None, current_element=None, namespaces=None):
        result = []
        for part in self.parts:
            result.append(part.to_string(resolve, xml_doc, current_element, namespaces))
        return "".join(result)


class BasicText(SchemaObject):
    """XML text without an element (e.g. _Element.text or _Element.tail)"""
    def __init__(self, parent, text):
        super().__init__(parent)
        self.text = text

    def to_string(self, resolve=False, xml_doc=None, current_element=None, namespaces=None):
        return self.text


class NameText(SchemaObject):
    """The <name> objects"""
    def __init__(self, parent, xml_element):
        super().__init__(parent)
        self.path = xml_element.attrib.get('path')

    def to_string(self, resolve=False, xml_doc=None, current_element=None, namespaces=None):
        if resolve:
            qb = self.get_schema().query_binding
            result = qb.evaluate_name_query(xml_doc, current_element, namespaces, {}, "name(%s)" % (self.path or "."))
            # TODO: *should* we remove namespaces?
            if result.find('}') >= 0:
                result = result[result.find('}')+1:]
            if result.find(':') >= 0:
                result = result[result.find(':')+1:]
            return result
        else:
            path_attr = ""
            if self.path is not None:
                path_attr = 'path="%s" ' % self.path
            return "<name %s/>" % path_attr

    def to_minimal_xml(self):
        element = xml_util.create('name')
        if self.path is not None:
            element.attrib['path'] = self.path
        return element


class ValueOfText(SchemaObject):
    """The <value-of> objects"""
    def __init__(self, parent, xml_element):
        super().__init__(parent)
        self.select = xml_element.attrib.get('select')

    def to_string(self, resolve=False, xml_doc=None, current_element=None, namespaces=None):
        if resolve:
            qb = self.get_schema().query_binding
            result = qb.evaluate_value_of_query(xml_doc, current_element, namespaces, {}, "name(%s)" % (self.select or "."))
            # TODO: *should* we remove namespaces?
            if result.find('}') >= 0:
                result = result[result.find('}')+1:]
            if result.find(':') >= 0:
                result = result[result.find(':')+1:]
            return result
        else:
            select_attr = ""
            if self.select is not None:
                select_attr = 'select="%s" ' % self.select
            return "<value-of %s/>" % select_attr

    def to_minimal_xml(self):
        element = xml_util.create('value-of')
        if self.select is not None:
            element.attrib['select'] = self.select
        return element


class TitleText(ComplexText):
    NAME = 'title'
    ALLOWED_CHILDREN = [ 'dir' ]

class ParagraphText(ComplexText):
    NAME = 'p'
    ALLOWED_CHILDREN = [ 'span', 'emph', 'dir' ]

class SimpleText(SchemaObject):
    def __init__(self, parent, xml_element):
        super().__init__(parent)
        if not hasattr(self, 'NAME'):
            raise Exception("base class SimpleText should not be instantiated directly")
        self.text = xml_element.text

    def to_string(self, resolve=False, xml_doc=None, current_element=None, namespaces=None):
        return self.text

    def to_xsl(self):
        return E('sch', self.NAME, text=self.text)


class SpanText(SimpleText):
    def __init__(self, xml_element):
        super().__init__(xml_element)
        self.cls = xml_element.attrib.get('class')

    def to_xsl(self):
        result = super().to_xsl()
        if self.value is not None:
            result.attrib['class'] = self.cls
        return result


class EmphText(SimpleText):
    NAME = 'emph'


class DirText(SimpleText):
    NAME = 'dir'

    def __init__(self, xml_element):
        super().__init__(xml_element)
        self.value = xml_element.attrib.get('value')

    def to_xsl(self):
        result = super().to_xsl()
        if self.value is not None:
            result.attrib['value'] = self.value
        return result


#
# CURRENT TODO:
# recreate the to_xsl for at least all *Text classes
# add a test to see whether xsl output is valid xsl style sheet?
# add to_text and to_html as well, also for all elements
# before or after? generalize into base class and impl class
# add attributes as defined in the spec (also see https://www.mulberrytech.com/quickref/schematron_rev1.pdf )
# and https://www.data2type.de/en/xml-xslt-xslfo/schematron/schematron-reference/

# Suggestions for abstracting:
# - straight text
# - elements with only text (emph, dir, span, etc)
# - elements with subelements (let base class handle all, and specifiy 'allowed'?)

# then:
# consider for the rest as well? can we ease up on xsl_generator then?
# should we 'allow-foreign' too?