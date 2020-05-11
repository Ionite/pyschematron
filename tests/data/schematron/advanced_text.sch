<?xml version="1.0" encoding="UTF-8"?>
<!-- This is an example with all advanced text elements -->
<!-- using the pdf at https://www.mulberrytech.com/quickref/schematron_rev1.pdf for a reference on the formatted text options -->
<!-- as well as https://www.data2type.de/en/xml-xslt-xslfo/schematron/schematron-reference/ -->
<schema
    xmlns="http://purl.oclc.org/dsdl/schematron"
    queryBinding="xslt2">
    <title>Advanced text schematron</title>
    <p>This is a test for the advanced formatting options of schematron, e.g elements like p, span, emph, name and value-of</p>

    <pattern xmlns="http://purl.oclc.org/dsdl/schematron" id="basic">
        <rule context="Document/Data/Number">
            <assert test=". &gt; 0" id="3" flag="fatal">
                The element <name /> in this <name path="parent::*"/> has the wrong value.
                It is <value-of select="."/> but it should be positive
                <emph>This is important!</emph>
                <dir value="ltr">Left-to-right</dir>
                <dir value="rtl">Right-to-left (not supported)</dir>
            </assert>
        </rule>
    </pattern>
</schema>
