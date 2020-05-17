import unittest

from lxml import etree

from pyschematron.svrl import SchematronOutput
from test_util import get_file


class TestSVRL(unittest.TestCase):

    def test_sample(self):
        xml_doc = etree.parse(get_file("svrl", "svrl_sample.xml"))
        svrl = SchematronOutput(xml_element=xml_doc.getroot())
        new_xml = svrl.to_xml()

        xml_doc = etree.parse(get_file("svrl", "simple.xml"))
        svrl = SchematronOutput(xml_element=xml_doc.getroot())
        new_xml = svrl.to_xml()

        xml_doc = etree.parse(get_file("svrl", "simple_2.xml"))
        svrl = SchematronOutput(xml_element=xml_doc.getroot())
        new_xml = svrl.to_xml()

        # print(etree.tostring(new_xml, pretty_print=True).decode('utf-8'))
