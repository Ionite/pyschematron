from lxml import etree
from pyschematron.elements import Schema
from pyschematron.xml.xsl_generator import schema_to_xsl

def main(input_filename, output_stream, output_format):

    schema = Schema()
    schema.read_from_file(input_filename)
    schema.process_abstract_patterns()

    if output_format == 'xslt':
        xsl_root = schema_to_xsl(schema)
        # Normalization: put all namespaces at the top level
        full_nsmap = xsl_root.nsmap
        #print(schema_to_xsl(schema))

        output_stream.write(etree.tostring(xsl_root, pretty_print=True, xml_declaration=True, encoding='utf-8').decode('utf-8'))
    elif output_format == 'minimal':
        output_stream.write(etree.tostring(schema.to_minimal_xml(minimal=True), pretty_print=True).decode('utf-8'))
    else:
        print("Unknown output format: %s" % args.output_format)
        return 1
    return 0
