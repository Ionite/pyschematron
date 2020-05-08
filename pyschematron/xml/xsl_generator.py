from lxml import etree
from pyschematron.xml.xsl_predefined_elements import get_predefined_elements_xslt1, get_predefined_elements_xslt2
from pyschematron.elements import *

import copy

NS = {
    'xsl': 'http://www.w3.org/1999/XSL/Transform',
    'sch': 'http://purl.oclc.org/dsdl/schematron',
    'svrl': 'http://purl.oclc.org/dsdl/svrl'
}


def E(namespace, name, attrs=None, nsmap=None, child=None, text=None):
    _nsmap = copy.copy(NS)
    if nsmap is not None:
        for prefix, namespace in nsmap.items():
            _nsmap[prefix] = namespace
    element = etree.Element("{%s}%s" % (_nsmap[namespace], name), nsmap=_nsmap)

    if attrs is not None:
        for name, value in attrs.items():
            element.attrib[name] = value

    if child is not None:
        element.append(child)

    if text is not None:
        element.text = text

    return element


def C(text):
    return etree.Comment(text)


def create_xsl_param(name):
    element = E("xsl", "param", {'name': name})
    return element


def create_xsl_variable(name):
    element = E("xsl", "param")
    element.attrib['name'] = name
    return element


def schema_to_xsl(schema, phase_name="#DEFAULT"):
    if phase_name == "#DEFAULT":
        phase_name = schema.default_phase

    if phase_name != "#ALL":
        phase = schema.get_phase(phase_name)
        patterns = schema.get_patterns_for_phase(phase_name)
    else:
        phase = None
        patterns = [pattern for pattern in schema.patterns.values() if not pattern.abstract]

    # Taken from the skeleton implementation:
    # If there is any rule context referencing an attribute, check attributes as well
    # If there is any rule context potentially referencing a possible comment or processing instruction, check those as well
    check_attributes = False
    check_comments_and_pi = False
    for pattern in patterns:
        for rule in pattern.rules:
            if not rule.abstract:
                if '@' in rule.context:
                    check_attributes = True
                if '(' in rule.context:
                    check_comments_and_pi = True
    if check_attributes:
        apply_templates_select = "@*|"
    else:
        apply_templates_select = ""
    if check_comments_and_pi:
        apply_templates_select += "*"
    else:
        apply_templates_select += "*|comment()|processing-instruction()"

    root = E("xsl", "stylesheet")
    if schema.query_binding_name == 'xslt':
        root.attrib['version'] = '1.0'
        predefined_elements = get_predefined_elements_xslt1()
    elif schema.query_binding_name == 'xslt2':
        root.attrib['version'] = '2.0'
        predefined_elements = get_predefined_elements_xslt2()
    else:
        print("Error: unable to convert schematron with query binding %s to xslt" % schema.query_binding_name)

    root.append(create_xsl_param('archiveDirParameter'))
    root.append(create_xsl_param('archiveNameParameter'))
    root.append(create_xsl_param('fileNameParameter'))
    root.append(create_xsl_param('fileDirParameter'))

    root.append(E('xsl', 'variable', {'name': 'document-uri'},
                  child=E('xsl', 'value-of', {'select': 'document-uri(/)'})))

    root.append(C('PHASES'))
    # TODO: Phases set at xsl generation time?

    root.append(C('PROLOG'))
    root.append(E('xsl', 'output', {'method': 'xml', 'omit-xml-declaration': 'no', 'standalone': 'yes', 'indent': 'yes'}))

    root.append(C('XSD TYPES FOR XSLT2'))
    root.append(C('KEYS AND FUNCTIONS'))
    root.append(C('DEFAULT RULES'))

    #root.append(get_predefined_elements())
    for predefined in predefined_elements:
        root.append(predefined)

    root.append(C('SCHEMA SETUP'))
    schema_setup = E('xsl', 'template', {'match': '/'})
    schematron_output = E('svrl', 'schematron-output', {'title': schema.title or "", 'schemaVersion': schema.schemaVersion or ""})
    if phase_name not in ["#DEFAULT", "#ALL"]:
        schematron_output.append(E('xsl', 'attribute', {'name': 'phase'}, text=phase_name))

    schematron_output_comment = E('xsl', 'comment')
    schematron_output_comment.append(E('xsl', 'value-of', {'select': '$archiveDirParameter'}))
    schematron_output_comment.append(E('xsl', 'value-of', {'select': '$archiveNameParameter'}))
    schematron_output_comment.append(E('xsl', 'value-of', {'select': '$fileNameParameter'}))
    schematron_output_comment.append(E('xsl', 'value-of', {'select': '$fileDirParameter'}))
    schematron_output.append(schematron_output_comment)

    for prefix,namespace in schema.ns_prefixes.items():
        schematron_output.append(E('svrl', 'ns-prefix-in-attribute-values', {'uri': namespace, 'prefix': prefix}))
    if schema.query_binding_name == 'xslt2':
        schematron_output.append(E('svrl', 'ns-prefix-in-attribute-values', {'uri': 'http://www.w3.org/2001/XMLSchema', 'prefix': 'xs'}))

    mode_count = schema.element_number_of_first_pattern
    for pattern in patterns:
        pattern_element = E('svrl', 'active-pattern')
        pattern_element.append(E('xsl', 'attribute', {'name': 'document'}, child=E('xsl', 'value-of', {'select': 'document-uri(/)'})))
        if pattern.id:
            pattern_element.append(E('xsl', 'attribute', {'name': 'id'}, text=pattern.id))
            pattern_element.append(E('xsl', 'attribute', {'name': 'name'}, text=pattern.id))
        pattern_element.append(E('xsl', 'apply-templates'))
        schematron_output.append(pattern_element)
        schematron_output.append(E('xsl', 'apply-templates', {'select': '/', 'mode': "M%d" % mode_count}))
        mode_count += 1
    schema_setup.append(schematron_output)
    root.append(schema_setup)

    root.append(C('SCHEMATRON PATTERNS'))
    root.append(E('svrl', 'text', text=schema.title or ""))
    for name,value in schema.variables.items():
        root.append(E('xsl', 'variable', {'name': name, 'select': value}))
    if phase:
        for name, value in phase.variables.items():
            root.append(E('xsl', 'variable', {'name': name, 'select': value}))

    mode_count = schema.element_number_of_first_pattern
    for pattern in patterns:
        root.append(C('PATTERN %s' % pattern.id))
        priority = 999 + len(pattern.rules)
        for rule in pattern.rules:
            if rule.abstract:
                continue
            root.append(C('RULE %s' % rule.id))
            rule_element = E('xsl', 'template', {'match': rule.context, 'priority': '%d' % priority, 'mode': 'M%d' % mode_count})
            rule_element.append(E('svrl', 'fired-rule', {'context': rule.context}))
            for name, value in rule.variables.items():
                rule_element.append(E('xsl', 'variable', {'name': name, 'select': value}))

            for report in rule.reports:
                rule_element.append(C('REPORT %s' % (report.id or "")))
                # Create the main report element
                if_element = E('xsl', 'if', {'test': report.test})
                successful_report = E('svrl', 'successful-report', {'test': report.test.strip()})
                if report.id is not None:
                    successful_report.append(E('xsl', 'attribute', {'name': 'id'}, text=report.id))
                if report.flag and report.flag != 'error':
                    successful_report.append(E('xsl', 'attribute', {'name': 'flag'}, text=report.flag))
                successful_report.append(E('xsl', 'attribute', {'name': 'location'}, child=E('xsl', 'apply-templates', {'select': '.', 'mode': 'schematron-select-full-path'})))

                # Convert the textual part of the report
                #successful_report.append(E('svrl', 'text', text=(report.text or "")))
                text_parts = report.new_text
                text_element = E('svrl', 'text')
                #text_element = E('svrl', 'text', text=text_parts.initial_text)
                text_subelement = None
                for part in text_parts.parts:
                    if type(part) == BasicText:
                        #last_subelement.tail = part.to_string()
                        #text_element.text = text_element.text + part.text
                        if text_subelement is None:
                            text_element.text = part.text
                        else:
                            text_subelement.tail = part.text
                    elif type(part) == NameText:
                        text_subelement = E('xsl', 'value-of', {'select': 'name(%s)' % (part.path or '.')})
                        text_element.append(text_subelement)
                    # The skeleton implementation adds empty xsl:text elements here, why?
                    text_subelement = E('xsl', 'text')
                    text_element.append(text_subelement)
                    #text_element.text = str(text_parts.parts)
                successful_report.append(text_element)

                #successful_report.append(text_element)

                # Add diagnostics
                for diagnostic_id in report.diagnostic_ids:
                    diagnostic = report.get_diagnostic(diagnostic_id)
                    diagnostic_reference = E('svrl', 'diagnostic-reference', {'diagnostic': diagnostic_id})
                    if diagnostic.language is not None:
                        diagnostic_attr = E('xsl', 'attribute', {'name': 'xml:lang'}, text=diagnostic.language)
                        diagnostic_attr.tail = diagnostic.text
                        diagnostic_reference.append(diagnostic_attr)
                    else:
                        diagnostic_reference.text = diagnostic.text

                if_element.append(successful_report)
                rule_element.append(if_element)

            for assertion in rule.assertions:
                rule_element.append(C('ASSERT %s' % (assertion.id or "")))
                choose = E('xsl', 'choose')
                choose.append(E('xsl', 'when', {'test': assertion.test}))
                otherwise = E('xsl', 'otherwise')
                failed_assert = E('svrl', 'failed-assert', {'test': assertion.test.strip()})
                if assertion.id is not None:
                    failed_assert.append(E('xsl', 'attribute', {'name': 'id'}, text=assertion.id))
                if assertion.flag and assertion.flag != 'error':
                    failed_assert.append(E('xsl', 'attribute', {'name': 'flag'}, text=assertion.flag))
                failed_assert.append(E('xsl', 'attribute', {'name': 'location'}, child=E('xsl', 'apply-templates', {'select': '.', 'mode': 'schematron-select-full-path'})))

                text_parts = assertion.new_text
                text_element = E('svrl', 'text')
                #text_element = E('svrl', 'text', text=text_parts.initial_text)
                text_subelement = None
                for part in text_parts.parts:
                    if type(part) == BasicText:
                        #last_subelement.tail = part.to_string()
                        #text_element.text = text_element.text + part.text
                        if text_subelement is None:
                            text_element.text = part.text
                        else:
                            text_subelement.tail = part.text
                    elif type(part) == NameText:
                        text_subelement = E('xsl', 'value-of', {'select': 'name(%s)' % (part.path or '.')})
                        text_element.append(text_subelement)
                    # The skeleton implementation adds empty xsl:text elements here, why?
                    text_subelement = E('xsl', 'text')
                    text_element.append(text_subelement)
                    #text_element.text = str(text_parts.parts)
                failed_assert.append(text_element)


                for diagnostic_id in assertion.diagnostic_ids:
                    diagnostic = assertion.get_diagnostic(diagnostic_id)
                    diagnostic_reference = E('svrl', 'diagnostic-reference', {'diagnostic': diagnostic_id})
                    if diagnostic.language is not None:
                        diagnostic_attr = E('xsl', 'attribute', {'name': 'xml:lang'}, text=diagnostic.language)
                        diagnostic_attr.tail = diagnostic.text
                        diagnostic_reference.append(diagnostic_attr)
                    else:
                        diagnostic_reference.text = diagnostic.text
                    failed_assert.append(diagnostic_reference)

                otherwise.append(failed_assert)
                choose.append(otherwise)
                rule_element.append(choose)

            # depends on qbinding maybe?
            #rule_element.append(E('xsl', 'apply-templates', {'select': '*|comment()|processing-instruction()', 'mode': "M%d" % mode_count}))
            rule_element.append(E('xsl', 'apply-templates', {'select': apply_templates_select, 'mode': "M%d" % mode_count}))
            root.append(rule_element)
            priority -= 1
        root.append(E('xsl', 'template', {'match': 'text()', 'priority': '-1', 'mode': "M%d" % mode_count}))
        # depends on qbinding maybe?
        #root.append(E('xsl', 'template', {'match': '@*|node()', 'priority': '-2', 'mode': "M%d" % mode_count},
        #              child=E('xsl', 'apply-templates', {'select': '*|comment()|processing-instruction()', 'mode': 'M%d' % mode_count})))
        root.append(E('xsl', 'template', {'match': '@*|node()', 'priority': '-2', 'mode': "M%d" % mode_count},
                      child=E('xsl', 'apply-templates', {'select': apply_templates_select, 'mode': 'M%d' % mode_count})))
        mode_count += 1

    return root
