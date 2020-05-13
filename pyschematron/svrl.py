
"""
SVRL parsing and creation classes
"""

from collections import OrderedDict
from lxml import etree
import copy

from pyschematron.xml import xml_util

NS = {
#    'xsl': 'http://www.w3.org/1999/XSL/Transform',
#    'sch': 'http://purl.oclc.org/dsdl/schematron',
    'svrl': 'http://purl.oclc.org/dsdl/svrl'
}

def E(prefix, name, attrs=None, nsmap=None, child=None, text=None):
    _nsmap = copy.copy(NS)
    if nsmap is not None:
        for _prefix, _namespace in nsmap.items():
            _nsmap[_prefix] = _namespace
    element = etree.Element("{%s}%s" % (_nsmap[prefix], name), nsmap=_nsmap)

    if attrs is not None:
        for name, value in attrs.items():
            element.attrib[name] = value

    if child is not None:
        element.append(child)

    if text is not None:
        element.text = text

    return element


class SVRLError(Exception):
    pass

class SchematronOutput(object):
    def __init__(self, title=None, phase=None, schema_version=None, namespaces=OrderedDict(), xml_element=None):
        self.title = title
        self.phase = phase
        self.schema_version = schema_version

        self.nsmap = namespaces
        self.texts = []
        self.attribute_prefixes = OrderedDict()
        self.active_patterns = []

        self.last_active_pattern = None
        self.last_fired_rule = None

        if xml_element is not None:
            self.from_xml(xml_element)

    def add_attribute_prefix(self, prefix, uri):
        self.attribute_prefixes[prefix] = uri

    def add_active_pattern(self, active_pattern):
        self.last_active_pattern = active_pattern
        self.active_patterns.append(active_pattern)

    def from_xml(self, element):
        self.title = element.attrib.get("title")
        self.phase = element.attrib.get("phase")
        self.schema_version = element.attrib.get("schemaVersion")

        self.nsmap = element.nsmap

        for child in element.getchildren():
            if isinstance(child, etree._Comment):
                continue
            el_name = etree.QName(child.tag).localname
            if el_name == 'text':
                self.texts.append(Text(xml_element=child))
            elif el_name == 'ns-prefix-in-attribute-values':
                self.attribute_prefixes[child.attrib.get("prefix")] = child.attrib.get("uri")
            elif el_name == 'active-pattern':
                self.last_active_pattern = ActivePattern(xml_element=child)
                self.active_patterns.append(self.last_active_pattern)
            elif el_name == 'fired-rule':
                self.last_fired_rule = FiredRule(xml_element=child)
                self.last_active_pattern.add_fired_rule(self.last_fired_rule)
            elif el_name == 'failed-assert':
                failed_assert = FailedAssert(xml_element=child)
                self.last_fired_rule.add_report(failed_assert)
            elif el_name == 'successful-report':
                successful_report = SuccessfulReport(xml_element=child)
                self.last_fired_rule.add_report(successful_report)
            else:
                raise SVRLError("Unknown element in SVRL document: %s" % el_name)

    def to_xml(self):
        element = E('svrl', 'schematron-output', nsmap=self.nsmap)
        xml_util.set_attr(element, 'title', self.title)
        xml_util.set_attr(element, 'phase', self.phase)
        xml_util.set_attr(element, 'schemaVersion', self.schema_version)

        for text in self.texts:
            element.append(text.to_xml())
        for prefix,uri in self.attribute_prefixes.items():
            element.append(E('svrl', 'ns-prefix-in-attribute-values', {'prefix': prefix, 'uri': uri}))
        for active_pattern in self.active_patterns:
            # Note: fired-rules, failed-assert and successful-report elements are *not* nested!
            # So add this element immediately
            element.append(active_pattern.to_xml())
            for fired_rule in active_pattern.fired_rules:
                element.append(fired_rule.to_xml())

                for report in fired_rule.reports:
                    element.append(report.to_xml())


        return element

class ActivePattern(object):
    def __init__(self, id=None, name=None, role=None, xml_element=None):
        self.id = id
        self.name = name
        self.role = role

        self.fired_rules = []

        if xml_element is not None:
            self.from_xml(xml_element)

    def from_xml(self, xml_element):
        self.id = xml_element.attrib.get("id")
        self.name = xml_element.attrib.get("name")
        self.role = xml_element.attrib.get("role")

    def to_xml(self):
        element = E('svrl', 'active_pattern')
        xml_util.set_attr(element, 'id', self.id)
        xml_util.set_attr(element, 'name', self.name)
        xml_util.set_attr(element, 'role', self.role)
        return element

    def add_fired_rule(self, fired_rule):
        self.fired_rules.append(fired_rule)

class FiredRule(object):
    def __init__(self, id=None, context=None, role=None, flag=None, xml_element=None):
        self.id = id
        self.context = context
        self.role = role
        self.flag = flag

        if xml_element is not None:
            self.from_xml(xml_element)

        # Reports are either 'FailedAssert' or 'SuccessfulReport'
        self.reports = []

    def from_xml(self, xml_element):
        self.id = xml_element.attrib.get("id")
        self.context = xml_element.attrib.get("context")
        self.role = xml_element.attrib.get("role")
        self.flag = xml_element.attrib.get("flag")

    def to_xml(self):
        element = E('svrl', 'fired-rule')
        xml_util.set_attr(element, 'id', self.id)
        xml_util.set_attr(element, 'context', self.context)
        xml_util.set_attr(element, 'role', self.role)
        xml_util.set_attr(element, 'flag', self.flag)
        return element

    def add_report(self, report):
        self.reports.append(report)

class Report(object):
    def __init__(self, id=None, location=None, test=None, role=None, flag=None, xml_element=None):
        self.id = id
        self.location = location
        self.test = test
        self.role = role
        self.flag = flag

        self.diagnostic_references = []
        self.text = None

        if xml_element is not None:
            self.from_xml(xml_element)

    def from_xml(self, element):
        self.id = element.attrib.get("id")
        self.location = element.attrib.get("location")
        self.test = element.attrib.get("test")
        self.role = element.attrib.get("role")
        self.flag = element.attrib.get("flag")

        for child in element.getchildren():
            el_name = etree.QName(child.tag).localname
            if el_name == 'diganostic-reference':
                pass
            elif el_name == 'text':
                self.text = Text(xml_element=child)
            else:
                raise SVRLError("Unknown element in SVRL document: %s" % el_name)

    def to_xml(self):
        element = E('svrl', self.NAME)
        xml_util.set_attr(element, 'id', self.id)
        xml_util.set_attr(element, 'location', self.location)
        xml_util.set_attr(element, 'test', self.test)
        xml_util.set_attr(element, 'role', self.role)
        xml_util.set_attr(element, 'flag', self.flag)

        for diagnostic_reference in self.diagnostic_references:
            element.append(diagnostic_reference.to_xml())
        if self.text is not None:
            element.append(self.text.to_xml())
        return element

class FailedAssert(Report):
    NAME = 'failed-assert'

class SuccessfulReport(Report):
    NAME = 'successful-report'

class DiagnosticReference(object):
    def __init__(self, diagnostic=None, xml_element=None):
        self.diagnostic = diagnostic

        if xml_element is not None:
            self.from_xml(xml_element)

    def from_xml(self, element):
        self.diagnostic = element.attrib.get('diagnostic')
        for child in element.getchildren():
            el_name = etree.QName(child.tag).localname
            if el_name == 'text':
                self.text = Text(xml_element=child)
            else:
                raise SVRLError("Unknown element in SVRL document: %s" % el_name)

    def to_xml(self):
        element = E('svrl', 'diagnostic-reference')
        xml_util.set_attr(element, 'diagnostic', self.diagnostic)

        if self.text is not None:
            element.append(self.text.to_xml())

class Text(object):
    def __init__(self, text=None, xml_element=None):
        self.text = text
        if xml_element is not None:
            self.from_xml(xml_element)

    def from_xml(self, element):
        self.text = element.text

    def to_xml(self):
        element = E('svrl', 'text')
        element.text = self.text
        return element
