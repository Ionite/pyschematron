import unittest

from lxml import etree

from pyschematron.elements import Schema

from test_util import get_file


class TestValidation(unittest.TestCase):

    def check_schema_validation(self, schema_file, xml_file, expected_errors, expected_warnings):
        """
        expected_errors is a list of the id values of the assertions that should fail with either no flag or flag="error"
        expected_warnings is a list of the id values of the assertions that should fail with either flag="warning"
        """
        schema = Schema(schema_file)
        xml_doc = etree.parse(xml_file)

        report = schema.validate_document(xml_doc)
        errors = report.get_failed_asserts()
        error_id_list = [err.id for err,element in errors if err.flag != 'warning']
        warnings = report.get_failed_asserts()
        warning_id_list = [w.id for w,element in warnings if w.flag == 'warning']
        self.assertEqual(expected_errors, error_id_list)
        self.assertEqual(expected_warnings, warning_id_list)

    def test_valid_documents(self):
        self.check_schema_validation(get_file("schematron", "basic.sch"), get_file("xml", "basic1_ok.xml"), [], [])

    def test_invalid_documents(self):
        self.check_schema_validation(get_file("schematron", "basic.sch"), get_file("xml", "basic1_error_1.xml"), ["1"],
                                     [])
        self.check_schema_validation(get_file("schematron", "basic.sch"), get_file("xml", "basic1_error_2.xml"), ["2"],
                                     [])
        self.check_schema_validation(get_file("schematron", "basic.sch"), get_file("xml", "basic1_warning_3.xml"), [],
                                     ["3"])
        self.check_schema_validation(get_file("schematron", "basic.sch"), get_file("xml", "basic1_warning_4.xml"), [],
                                     ["4"])


class ValidateSchematronFiles(unittest.TestCase):
    """
    Tests the schematron files used in the test cases, validating them against the Schematron schematron from the specification
    """

    def setUp(self):
        self.schema = Schema(get_file("schematron", "schematron.sch"))

    def get_schematron_minimal_xml(self, filename):
        # These are all schematrons, and schematrons with includes can fail
        # the schematron validation (for instance if a pattern which is defined in
        # an included file is referenced in the main file)
        # Therefore, we don't validate it directly, but convert it to a minimal version
        # first
        schema_to_check = Schema(get_file("schematron", filename))
        return schema_to_check.to_minimal_xml_document()

    def test_correct_schematrons(self):
        for filename in ['basic.sch',
                         'schematron.sch',
                         #'unknown_querybinding.sch',
                         'svrl.sch',
                         'full.sch'
                         ]:
            xml_doc = self.get_schematron_minimal_xml(filename)
            report = self.schema.validate_document(xml_doc)
            self.assertEqual([], report.get_failed_asserts(), [a.text for a in report.get_failed_asserts()])

    def test_bad_schematrons(self):
        for filename in ['malformed/bad_is_a_attribute.sch']:
            # These wouldn't even pass our own parsing, to read them directly
            xml_doc = etree.parse(get_file("schematron", filename))
            report = self.schema.validate_document(xml_doc)
            self.assertNotEqual([], report.get_failed_asserts(), [a.to_string() for a,element in report.get_failed_asserts()])

        for filename in ['malformed/bad_active_pattern.sch']:
            xml_doc = self.get_schematron_minimal_xml(filename)
            report = self.schema.validate_document(xml_doc)
            self.assertNotEqual([], report.get_failed_asserts(), [a.to_string() for a,element in report.get_failed_asserts()])