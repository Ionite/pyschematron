<?xml version="1.0" encoding="UTF-8"?>
<schema
    xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
    xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
    xmlns:ubl="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
    xmlns:cn="urn:oasis:names:specification:ubl:schema:xsd:CreditNote-2"
    xmlns="http://purl.oclc.org/dsdl/schematron"
    queryBinding="some-unknown-binding">
    <title>Basic schematron</title>

    <pattern xmlns="http://purl.oclc.org/dsdl/schematron" id="basic">
        <rule context="Document/Data" flag="fatal">
            <assert test="Name" id="1" flag="fatal">Document data must have a name</assert>
            <assert test="Number" id="2" flag="fatal">Document data must have a number</assert>
        </rule>
        <rule context="Document/Data/Number">
            <assert test=". &gt; 0" id="3" flag="warning">Number should be positive</assert>
        </rule>
        <rule context="Document/Data/Name">
            <assert test="ends-with(., 'ello')" id="4" flag="warning">Name should end with 'ello'</assert>
        </rule>
    </pattern>
</schema>
