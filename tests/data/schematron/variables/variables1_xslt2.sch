<?xml version="1.0" encoding="UTF-8"?>
<!-- phases not implemented yet, so variables are currently only used in schema, pattern and rule -->

<schema
    xmlns="http://purl.oclc.org/dsdl/schematron"
    queryBinding="xslt2">
    <title>Schematron file to test variable uses</title>

    <let name="text1_schema" value="/Document/Data/TextOne" />

    <pattern xmlns="http://purl.oclc.org/dsdl/schematron" id="basic">
        <let name="text1_pattern" value="/Document/Data/TextOne" />
        <rule context="Document/Data" flag="fatal">
            <let name="text1_rule" value="/Document/Data/TextOne" />
            <!--<assert test="Schema = " id="1" flag="fatal">Each Data element must have a Schema element with value 'schema1'</assert>-->
            <assert test="$text1_schema = 'text1'" id="1" flag="fatal">Each Data element must have a Pattern element with value 'schema1'</assert>
            <assert test="$text1_pattern = 'text1'" id="1" flag="fatal">Each Data element must have a Pattern element with value 'schema1'</assert>
            <assert test="$text1_rule = 'text1'" id="1" flag="fatal">Each Data element must have a Pattern element with value 'schema1'</assert>
        </rule>
    </pattern>
</schema>
