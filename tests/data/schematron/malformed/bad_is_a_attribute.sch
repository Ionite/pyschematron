<?xml version="1.0" encoding="UTF-8"?>
<!--
     This schematron file is to be extended with all features as they are tested and developed
     Such as includes, abstract patterns and rules, rich documentation, etc.
-->
<schema xmlns="http://purl.oclc.org/dsdl/schematron" queryBinding="xslt2">
  <title>Full schematron</title>
  <pattern xmlns="http://purl.oclc.org/dsdl/schematron" id="builtin" abstract="true">
    <rule context="Document/Data" flag="builtin_role">
      <assert test="Name" id="builtin_1" flag="builtin_existence">Document data must have a name</assert>
      <assert test="Number" id="builtin_2" flag="builtin_existence">Document data must have a number</assert>
    </rule>
    <rule context="Document/Data/Number">
      <assert test=". &gt; $number_minimum" id="builtin_3" flag="builtin_value">Number too low</assert>
    </rule>
    <rule context="Document/Data/Name">
      <assert test="ends-with(., 'ello')" id="builtin_4" flag="builtin_value">Name should end with 'ello'</assert>
    </rule>
  </pattern>
  <pattern is-a="doesnotexist">
      <param name="foo" value="bar" />
  </pattern>
</schema>