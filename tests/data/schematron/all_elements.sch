<?xml version="1.0" encoding="UTF-8"?>
<schema xmlns="http://purl.oclc.org/dsdl/schematron">
  <!-- Examples taken from https://www.data2type.de/en/xml-xslt-xslfo/schematron/schematron-reference/ -->
  <title>Schematron for Noah</title>
  <p>This Schematron schema shall help Noah to accommodate the right animals in the suitable environment.</p>
  <ns uri="http://www.schematron.info/arche" prefix="ark" />

  <!-- We have a separate phase here for each pattern, for easier testing -->
  <phase id="assert">
    <active pattern="assert" />
  </phase>
  <phase id="diagnostics">
    <active pattern="diagnostics" />
  </phase>
  <phase id="extends">
    <active pattern="extends" />
  </phase>
  <phase id="let">
    <active pattern="let" />
  </phase>
  <phase id="name">
    <active pattern="name" />
  </phase>
  <phase id="noah" is-a="abstractPattern">
    <active pattern="noah" is-a="abstractPattern" />
  </phase>
  <phase id="abstractPattern" abstract="true">
    <active pattern="abstractPattern" abstract="true" />
  </phase>
  <phase id="pattern">
    <active pattern="pattern" />
  </phase>
  <phase id="report">
    <active pattern="report" />
  </phase>
  <phase id="rule">
    <active pattern="rule" />
  </phase>
  <phase id="value-of">
    <active pattern="value-of" />
  </phase>

  <pattern id="assert">
    <rule context="ark:animal">
      <assert test="count(parent::*/ark:animal[ark:species=current()/ark:species])=2">There are less or more than two animals of this species in this accommodation.</assert>
      <assert test="count(parent::*/ark:animal[ark:species=current()/ark:species][@sex='male'])=1">A pair must always consist of one male and one female.</assert>
    </rule>
  </pattern>
  <pattern id="diagnostics">
    <rule context="ark:animal">
      <report test="count(parent::*/ark:animal[ark:species=current()/ark:species]) &gt; 2" diagnostics="number">There are more than two animals of this species in this accommodation.</report>
    </rule>
  </pattern>
  <pattern id="extends">
    <rule context="ark:animal">
      <extends rule="weight" />
    </rule>
    <rule abstract="true" id="weight">
      <report test="parent::*/ark:animal/ark:weight &lt; (ark:weight div 10)">
        Noah, the animal is too heavy for its roommates!
        It could trample down one of them.
      </report>
    </rule>
  </pattern>
  <pattern id="let">
    <rule context="ark:animal">
      <let name="animalSpecies" value="ark:species" />
      <report test="count(parent::*/ark:animal[ark:species=$animalSpecies]) &gt; 2">There are more than two animals of this species in this accommodation.</report>
      <assert test="not(count(parent::*/ark:animal[ark:species=$animalSpecies]) &lt; 2)">There is no pair of this species in this accommodation.</assert>
    </rule>
  </pattern>
  <pattern id="name">
    <rule context="ark:animal">
      <let name="animalSpecies" value="ark:species" />
      <report test="count(parent::*/ark:animal[ark:species=$animalSpecies]) &gt; 2">
        There are more than two
        <name />
        elements of this species in this
        <name path="parent::*" />
        element.
      </report>
      <assert test="not(count(parent::*/ark:animal[ark:species=$animalSpecies]) &lt; 2)">
        There is no further
        <name />
        element of this species in this
        <name path="parent::*" />
        element.
      </assert>
    </rule>
  </pattern>
  <pattern id="noah" is-a="abstractPattern">
    <param name="count" value="parent::*/ark:animal[ark:species=current()/ark:species]" />
  </pattern>
  <pattern id="abstractPattern" abstract="true">
    <rule context="ark:animal">
      <report test="count($count) &gt; 2">There are more than two animals of this species in this accommodation.</report>
      <assert test="not(count($count) &lt; 2)">There is no pair of this species in this accommodation.</assert>
    </rule>
  </pattern>
  <pattern id="pattern">
    <rule context="ark:animal[@carnivore='yes']">
      <report test="parent::*/ark:animal/ark:weight &lt; (ark:weight div 2)">
        Noah, this carnivore is too strong (heavy) for its roommate.
        The carnivore could use it as a food source.
      </report>
    </rule>
    <rule context="ark:animal">
      <report test="parent::*/ark:animal/ark:weight &lt; (ark:weight div 10)">
        Noah, the animal is too heavy for its roommates!
        It could trample down one of them.
      </report>
    </rule>
  </pattern>
  <pattern id="report">
    <rule context="ark:animal">
      <report test="count(//ark:animal[ark:species=current()/ark:species]) &gt; 2">There are more than two animals of this species on the ark.</report>
      <report test="count(parent::*/ark:animal[ark:species=current()/ark:species]) &lt; 2">There are less than two animals of this species in this accommodation.</report>
    </rule>
  </pattern>
  <pattern id="rule">
    <rule context="ark:room[ark:animal[@carnivore='no']]">
      <report test="ark:animal[@carnivore='yes']">
        There are carnivores and herbivores in one accommodation.
        The animals are not a food source!
      </report>
    </rule>
  </pattern>
  <pattern id="value-of">
    <rule context="ark:animal">
      <report test="count(parent::*/ark:animal[ark:species=current()/ark:species]) &gt; 2">
        There are more than two animals of this species in this accommodation (
        <value-of select="ark:species" />
        ).
      </report>
    </rule>
  </pattern>

  <include href="diagnostics.xml" />
</schema>