# pyschematron

This is a library and toolset for [ISO Schematron](https://http://schematron.com/)

It aims to be a feature-complete python implementation of the Schematron standard, with support for Xpath2.

Right now it is in an early alpha stage, and is not nearly feature complete.

This library includes two tools:


##### pyschematron-to-xslt.py

This tool converts a schematron file to an XSLT file that can be used with any other program that can handle XSLT(2) files. The resulting XSLT transforms an xml document into an SVRL (Schematron Validation Result Language) report.

##### pyschematron-validate.py

This tool takes a schematron file and an xml document, and directly validates the document against the schematron rules.


### Requirements

- lxml
- elementpath (1.4.4 or higher)

The version of elementpath we use is currently a development version available at [github](https://github.com/tjeb/elementpath) in the [jelte_fixes](https://github.com/tjeb/elementpath/tree/jelte_fixes) branch.

This branch contains a number of workarounds for issues we encountered while testing with more advanced schematron files. We are working on getting these fixes upstream in elementpath, but for the moment, you'll need to install this particular branch (for instance with _pip install -e_)

### Roadmap

This is an early beta, and it is not feature-complete yet, nor is the API frozen.

Currently, validation works for a number of schematron files, and XSLT generation is partially complete.

Plans for the (near) future

- go through the specification, and mark its element and sections as implemented/roadmap/not planned
- implement the processing steps as defined in section 6
- additional documentation
- add support for output formats of validator (text, svrl, json (format to be defined))
