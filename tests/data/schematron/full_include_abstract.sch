<pattern xmlns="http://purl.oclc.org/dsdl/schematron" abstract="true" id="included-abstract">
    <rule context="$context" flag="included_role">
        <assert test="$name" id="included_1" flag="included_existence">Document data must have a name</assert>
        <assert test="$number" id="included_2" flag="included_existence">Document data must have a number</assert>
    </rule>
    <rule context="$context_number">
        <assert test=". &gt; 0" id="included_3" flag="included_value">Number should be positive</assert>
    </rule>
    <rule context="$context_name">
        <assert test="ends-with(., 'ello')" id="included_4" flag="included_value">Name should end with 'ello'</assert>
    </rule>
</pattern>
