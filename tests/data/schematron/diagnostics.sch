<?xml version="1.0" encoding="UTF-8"?>
<schema xmlns="http://purl.oclc.org/dsdl/schematron">
  <ns uri="http://www.schematron.info/arche" prefix="ark"/>
  <pattern>
    <rule context="ark:animal">
      <assert test="count(parent::*/ark:animal[ark:species=current()/ark:species]) &gt; 1">There must be at least two animals of this species</assert>
      <report test="count(parent::*/ark:animal[ark:species=current()/ark:species]) &gt; 2" diagnostics="number">There are more than two animals of this species in this accommodation.</report>
    </rule>
  </pattern>
  <diagnostics>
    <diagnostic id="number">
      Noah, you must remove as many animals from the ark so that
      only two of one species live in this accommodation.
    </diagnostic>
  </diagnostics>
</schema>