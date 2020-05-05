# Specification Notes

## Introduction

These are notes regarding the specification of Schematron and the implementation here.

The specification that this version is based on can be found at at http://standards.iso.org/ittf/PubliclyAvailableStandards/c055982_ISO_IEC_19757-3_2016.zip

## Syntax Elements (Section 5.4)

##### 5.4.1 active element

Implemented

##### 5.4.2 assert element

Partly implemented

Implemented:
- test
- flag
- diagnostics

Not implemented:
- icon
- see
- fpi
- role
- subject

##### 5.4.3 extends element

Implemented

##### 5.4.4 include element

Implemented

##### 5.4.5 let element

Implemented

##### 5.4.6 name element

Not implemented

##### 5.4.7 ns element

Implemented

##### 5.4.8 param element

Implemented

##### 5.4.9 pattern element

Partially implemented

Implemented:
- General support for patterns
- id
- abstact patterns
- is-a

Not implemented:
- p
- icon
- see
- title
- fpi
- error checking on conflicting attributes

##### 5.4.10 phase element

Implemented

##### 5.4.11 report element

Implemented

##### 5.4.12 rule element

Partly implemented

implemented:
- context
- flags: warning, error, no flag (interpreted as error)
- abstract rules

Not implemented:
- icon
- see
- fpi
- role
- subject
- rule validation (i.e. whether the rule specification itself is valid)

##### 5.4.13 schema element

Partly implemented

Implemented:
- queryBinding xslt
- queryBinding xslt2
- queryBinding xpath2
- queryBinding check
- defaultPhase
- title

Not implemented:
- schemaVersion check
- p
- icon
- see
- fpi

Need to verify:
- full handling of querybindings as specified in the annexes

##### 5.4.14 value-of element

Not implemented

## Ancillary elements (section 5.5)

None implemented

## Semantics (Section 6)

##### 6.1 validation function

Implemented, insofar the elements from section 5.4 have been implemented.

##### 6.2 Minimal syntax

Implemented

##### 6.3 Abstract pattern processing

Implemented


##### 6.4 Query language binding

Implemented for xslt, xpath2 and xslt2.

##### 6.5 Order and side-effects

Main rule order (match first, skip rest) has been implemented

##### Other

nested elements in texts (such as value-of and emph) are currently not supported. It is likely that only the text up to such elements is shown.