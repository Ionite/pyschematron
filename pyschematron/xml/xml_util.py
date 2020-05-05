"""
This module contains helper functions to create XML elements
"""
from lxml import etree

def create(element_name, namespace="http://purl.oclc.org/dsdl/schematron", add_nsmap=False):
    el_name = "{%s}%s" % (namespace, element_name)
    if add_nsmap:
        return etree.Element(el_name, nsmap={'sch': 'http://purl.oclc.org/dsdl/schematron'})
    else:
        return etree.Element(el_name)

def set_attr(element, name, value):
    if value is not None and value != '':
        element.attrib[name] = value

def create_variable(name, value):
    var_element = create("let")
    set_attr(var_element, 'name', name)
    set_attr(var_element, 'value', value)
    return var_element

def set_variables(element, variables):
    for name,value in variables.items():
        element.append(create_variable(name, value))
