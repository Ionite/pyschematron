import sys

from lxml import etree
from pyschematron.elements import Schema

def main(schematron_file, xml_file, phase="#DEFAULT", output_type="text", output_stream=sys.stdout, verbosity=1):

    schema = Schema(verbosity=verbosity)
    schema.read_from_file(schematron_file)
    schema.process_abstract_patterns()

    doc = etree.parse(xml_file)
    if output_type == 'text':
        return validate_to_text(schema, doc, xml_file, phase, output_stream, verbosity)
    elif output_type == 'svrl':
        svrl = schema.validate_document_to_svrl(doc, phase)
        output_stream.write(etree.tostring(svrl.to_xml(), pretty_print=True, xml_declaration=True, encoding='utf-8').decode('utf-8'))
        output_stream.write("\n")
        return 0
    else:
        raise Exception("Unknown output type: %s" % output_type)



def validate_to_text(schema, doc, xml_file, phase="#DEFAULT", output_stream=sys.stdout, verbosity=1):
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
            #output_stream.write("Error: %s\n" % error.text)
            output_stream.write("Error: %s\n" % error.to_string(resolve=True, xml_doc=doc, current_element=element, namespaces=schema.ns_prefixes))
            for d_id in error.diagnostic_ids:
                if d_id in error.get_schema().diagnostics:
                    output_stream.write("Proposal for solution: %s\n" % error.get_schema().diagnostics[d_id].text)
        for warning, element in warnings:
            #output_stream.write("Warning: %s\n" % warning.text)
            output_stream.write("Warning: %s\n" % warning.to_string(resolve=True, xml_doc=doc, current_element=element, namespaces=schema.ns_prefixes))

            for d_id in warning.diagnostic_ids:
                if d_id in warning.rule.pattern.schema.diagnostics:
                    output_stream.write("Proposal for solution: %s\n" % warning.rule.pattern.schema.diagnostics[d_id].text)

    if verbosity > 0:
        output_stream.write("File: %s\n" % xml_file)
    if len(errors) > 0:
        if verbosity > 0:
            output_stream.write("%d errors in document\n" % len(errors))
        return -1
    if len(warnings) > 0:
        if verbosity > 0:
            output_stream.write("%d warnings in document\n" % len(warnings))
        return 1
    if len(errors) == 0 and len(warnings) == 0:
        if verbosity > 0:
            output_stream.write("All tests passed, no errors or warnings\n")
        return 0
