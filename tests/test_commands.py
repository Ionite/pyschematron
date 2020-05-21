import unittest
from io import StringIO

from lxml import etree

from pyschematron.commands import validate
from pyschematron.commands import convert

from test_util import get_file


class TestValidateCommand(unittest.TestCase):
    def setUp(self):
        self.output_stream = StringIO()
        self.rcode = None

    def run_command(self, sch_file, xml_file, expected_result=0, output_type='text', verbosity=1):
        self.output_stream = StringIO()
        self.rcode = validate.main(sch_file, xml_file, output_stream=self.output_stream, output_type=output_type, verbosity=verbosity)
        self.assertEqual(expected_result, self.rcode)

    def test_validate(self):
        """Test whether the commands run, complete, and return the correct result code. We do not verify the actual output in this test"""
        self.run_command("data/schematron/all_elements.sch", "data/xml/diagnostics/more_than_three_animals.xml", 21)
        self.run_command("data/schematron/advanced_text.sch", "data/xml/basic1_ok.xml")
        self.run_command("data/schematron/diagnostics.sch", "data/xml/diagnostics/more_than_three_animals.xml", 3)

    def test_validate_to_svrl(self):
        self.run_command("data/schematron/all_elements.sch", "data/xml/diagnostics/more_than_three_animals.xml", output_type='svrl')


class TestConvertCommand(unittest.TestCase):
    def run_command(self, sch_file, expected_result=0, output_format='xslt'):
        self.output_stream = StringIO()
        self.rcode = convert.main(sch_file, output_stream=self.output_stream, output_format=output_format)
        self.assertEqual(expected_result, self.rcode)

    def test_convert(self):
        """Test whether the commands run, complete, and return the correct result code. We do not verify the actual output in this test"""
        self.run_command("data/schematron/advanced_text.sch")
        self.run_command("data/schematron/all_elements.sch")
        self.run_command("data/schematron/basic.sch")
        self.run_command("data/schematron/diagnostics.sch")
        self.run_command("data/schematron/full.sch")
        self.run_command("data/schematron/multilingual.sch")
        self.run_command("data/schematron/name_element.sch")
        self.run_command("data/schematron/schematron.sch")
        self.run_command("data/schematron/svrl.sch")

    def test_convert_to_minimal(self):
        self.run_command("data/schematron/advanced_text.sch", output_format='minimal')
        self.run_command("data/schematron/all_elements.sch", output_format='minimal')
        self.run_command("data/schematron/basic.sch", output_format='minimal')
        self.run_command("data/schematron/diagnostics.sch", output_format='minimal')
        self.run_command("data/schematron/full.sch", output_format='minimal')
        self.run_command("data/schematron/multilingual.sch", output_format='minimal')
        self.run_command("data/schematron/name_element.sch", output_format='minimal')
        self.run_command("data/schematron/schematron.sch", output_format='minimal')
        self.run_command("data/schematron/svrl.sch", output_format='minimal')
