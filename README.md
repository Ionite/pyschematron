# pyschematron

This is a library and toolset for [ISO Schematron](https://http://schematron.com/)

It aims to be a feature-complete python implementation of the Schematron standard, with support for Xpath2.

This library includes two tools:


#####pyschematron-to-xslt.py

This tool converts a schematron file to an XSLT file that can be used with any other program that can handle XSLT(2) files. The resulting XSLT transforms an xml document into an SVRL (Schematron Validation Result Language) report.

##### pyschematron-validate.py

This tool takes a schematron file and an xml document, and directly validates the document against the schematron rules.


### Requirements

- lxml
- elementpath

The version of elementpath we use is currently a development version available at [github](https://github.com/tjeb/elementpath) in the [jelte_fixes](https://github.com/tjeb/elementpath/tree/jelte_fixes) branch.

This branch contains a number of workarounds for issues we encountered while testing with more advanced schematron files. We are working on getting these fixes upstream in elementpath, but for the moment, you'll need to install this particular branch (for instance with _pip install -e_)

### Roadmap

This is an early beta, and it is not feature-complete yet, nor is the API frozen.

Plans for the near feature

- feature compatibility with the skeleton transformators from schematron.com
- improvements in the validator and generator