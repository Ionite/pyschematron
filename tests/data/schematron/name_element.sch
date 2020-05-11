<?xml version="1.0" encoding="UTF-8"?>
<schema xmlns="http://purl.oclc.org/dsdl/schematron">
  <!-- Examples taken from https://www.data2type.de/en/xml-xslt-xslfo/schematron/schematron-reference/ -->
  <title>Schematron for Noah</title>
  <p>This Schematron schema shall help Noah to accommodate the right animals in the suitable environment.</p>
  <ns uri="http://www.schematron.info/arche" prefix="ark" />

  <pattern id="name">
    <rule context="ark:animal">
      <let name="animalSpecies" value="ark:species" />
      <report id="REPORT" test="count(parent::*/ark:animal[ark:species=$animalSpecies]) &gt; 2">
        There are more than two <name /> elements of this species in this <name path="parent::*" /> element.
      </report>
      <assert id="ASSERT" test="not(count(parent::*/ark:animal[ark:species=$animalSpecies]) &lt; 2)">
        There is no further <name /> element of this species in this <name path="parent::*" /> element.
      </assert>
    </rule>
  </pattern>
</schema>