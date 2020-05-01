# pyschematron

This is a library and toolset for [ISO Schematron](https://http://schematron.com/)

It aims to be a feature-complete python implementation of the Schematron standard, with support for Xpath2.

Right now it is in an early alpha stage, and is not nearly feature complete. See the file specification_notes.md for more information on which parts of the specification have been implemented.

This library includes two tools:

##### pyschematron-to-xslt.py

This tool converts a schematron file to an XSLT file that can be used with any other program that can handle XSLT(2) files. The resulting XSLT transforms an xml document into an SVRL (Schematron Validation Result Language) report.

##### pyschematron-validate-xml.py

This tool takes a schematron file and an xml document, and directly validates the document against the schematron rules.


### Requirements

- lxml
- elementpath (1.4.4 or higher)

### Roadmap

This is an early beta, and it is not feature-complete yet, nor is the API frozen.

Currently, validation works for a number of schematron files, but XSLT generation is only partially complete.

Plans for the (near) future
- refactor Assert and Report classes into subclasses of one superclass
- rename tools
- cleanup and docstrings
- extend the Report data structure to output svrl
- go through the specification, and mark its element and sections as implemented/roadmap/not planned
- implement the other processing steps as defined in section 6
- additional documentation
- add support for output formats of validator (text, svrl, json (format to be defined))
- diagnostics support

Other things to work on:
- performance improvement
- XSD schema validation of input files (both schematron itself and optional xsd schemas for input xml documents) 
- more output format options
- Do we need a stand-alone xslt(2) transformer too?
- Would a code generator make sense?