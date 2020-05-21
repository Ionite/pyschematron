from lxml import etree
from pyschematron.elements import Schema
from pyschematron.xml.xsl_generator import schema_to_xsl


def main(input_filename, output_stream, output_format):
    schema = Schema()
    schema.read_from_file(input_filename)
    schema.process_abstract_patterns()

    if output_format == 'xslt':
        xsl_root = schema_to_xsl(schema)
        # Normalization: put all namespaces at the top level, but keep the
        # ones specifically mentioned in the schematron
        full_nsmap = xsl_root.nsmap
        keep_prefixes = []
        for prefix,namespace in schema.ns_prefixes.items():
            full_nsmap[prefix] = namespace
            keep_prefixes.append(prefix)
        etree.cleanup_namespaces(xsl_root, top_nsmap=full_nsmap, keep_ns_prefixes=keep_prefixes)

        output_stream.write(etree.tostring(xsl_root, pretty_print=True, xml_declaration=True, encoding='utf-8').decode('utf-8'))
    elif output_format == 'minimal':
        output_stream.write(etree.tostring(schema.to_minimal_xml(minimal=True), pretty_print=True).decode('utf-8'))
    else:
        print("Unknown output format: %s" % args.output_format)
        return 1
    return 0
