<?xml version="1.0" encoding="UTF-8"?>
<schema
    xmlns="http://purl.oclc.org/dsdl/schematron"
    queryBinding="xpath2">
    <title>Basic schematron</title>
    <pattern>
        <rule id="r1" context="a"><assert test=".=1">The a element should have a value of 1, for no reason</assert></rule>
        <rule id="r2" context="b"><assert test=".=1">The b element should have a value of 1, for no reason</assert></rule>
        <rule id="r3" context="c"><assert test=".=1">The c element should have a value of 1, for no reason</assert></rule>
        <rule id="r4" context="c | d"><assert test=".=1">The d element should have a value of 1, for no reason</assert></rule>
        <rule id="r5" context="*"><assert test="@id">Elements not a,b,c,d should have an attribute id, for no reason</assert></rule>
    </pattern>
</schema>
