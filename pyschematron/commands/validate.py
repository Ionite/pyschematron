import sys

from lxml import etree
from pyschematron.elements import Schema

def main(schematron_file, xml_file, phase="#DEFAULT", verbosity=1):

    schema = Schema(verbosity=verbosity)
    schema.read_from_file(schematron_file)
    schema.process_abstract_patterns()

    doc = etree.parse(xml_file)
    report = schema.validate_document(doc, phase=phase)
    # Split up the failed asserts by flag; assert with flag
    # 'warning' are considered warnings, asserts with any
    # other flag are considered errors
    failed_asserts = report.get_failed_asserts_by_flag()
    warnings = failed_asserts.pop('warning', [])
    errors = []
    for error_list in failed_asserts.values():
        errors.extend(error_list)

    if verbosity > 0:
        for error, element in errors:
            #print("Error: %s" % error.text)
            print("Error: %s" % error.to_string(resolve=True, xml_doc=doc, current_element=element, namespaces=schema.ns_prefixes))
            for d_id in error.diagnostic_ids:
                if d_id in error.get_schema().diagnostics:
                    print("Proposal for solution: %s" % error.rule.pattern.schema.diagnostics[d_id].text)
        for warning, element in warnings:
            #print("Warning: %s" % warning.text)
            print("Warning: %s" % warning.to_string(resolve=True, xml_doc=doc, current_element=element, namespaces=schema.ns_prefixes))

            for d_id in warning.diagnostic_ids:
                if d_id in warning.rule.pattern.schema.diagnostics:
                    print("Proposal for solution: %s" % warning.rule.pattern.schema.diagnostics[d_id].text)

    if verbosity > 0:
        print("File: %s" % xml_file)
    if len(errors) > 0:
        if verbosity > 0:
            print("%d errors in document" % len(errors))
        return -1
    if len(warnings) > 0:
        if verbosity > 0:
            print("%d warnings in document" % len(warnings))
        return 1
    if len(errors) == 0 and len(warnings) == 0:
        if verbosity > 0:
            print("All tests passed, no errors or warnings")
        return 0
