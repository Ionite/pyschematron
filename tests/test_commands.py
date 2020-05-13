import unittest
from io import StringIO

from lxml import etree

from pyschematron.commands import validate

from test_util import get_file


class TestValidateCommand(unittest.TestCase):
    def test_validate(self):
        # We don't actually verify the output here, but we pass an output stream object so we can set verbosity > 0 and not have the output printed
        output = StringIO()
        result = validate.main("data/schematron/all_elements.sch", "data/xml/diagnostics/more_than_three_animals.xml", output_stream=output, verbosity=1)
        self.assertEqual(-1, result)

        output = StringIO()
        result = validate.main("data/schematron/advanced_text.sch", "data/xml/basic1_ok.xml", output_stream=output, verbosity=1)
        self.assertEqual(0, result)

        output = StringIO()
        result = validate.main("data/schematron/diagnostics.sch", "data/xml/diagnostics/more_than_three_animals.xml", output_stream=output, verbosity=1)
        self.assertEqual(-1, result)

    def DISABLED_test_validate_svrl(self):
        result = validate.main("data/schematron/all_elements.sch", "data/xml/diagnostics/more_than_three_animals.xml", output_type='svrl', verbosity=0)
        #result = validate.main("data/schematron/all_elements.sch", "data/xml/diagnostics/more_than_three_animals.xml", output_type='svrl', phase='name', verbosity=0)
        print(etree.tostring(result.to_xml(), pretty_print=True).decode('utf-8'))
        #self.assertEqual(0, result)