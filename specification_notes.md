# Specification Notes

## Introduction

These are notes regarding the specification of Schematron and the implementation here.

The specification that this version is based on can be found at at http://standards.iso.org/ittf/PubliclyAvailableStandards/c055982_ISO_IEC_19757-3_2016.zip

## Syntax Elements (Section 5.4)

##### 5.4.1 active element

Not implemented

##### 5.4.2 assert element

Partly implemented

Implemented:
- test
- flag

Not implemented:
- diagnostics
- icon
- see
- fpi
- role
- subject

##### 5.4.3 extends element

Not implemented

##### 5.4.4 include element

Implemented

##### 5.4.5 let element

Partly implemented

Implemented:
- let statements for patterns

Not implemented:
- let statements for schemas
- let statements for phases
- let statements for rules
- let statements without value attribute
- check for multiply defined let statements

##### 5.4.6 name element

Not implemented

##### 5.4.7 ns element

Implemented

##### 5.4.8 param element

Implemented, but currently as if they are variables, which is incorrect.

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

Not implemented

##### 5.4.11 report element

Not implemented

##### 5.4.12 rule element

Partly implemented

implemented:
- context
- flag: warning, error, no flag (interpreted as error)

Not implemented:
- icon
- see
- fpi
- role
- subject
- abstract rules
- rule validation

##### 5.4.13 schema element

Partly implemented

Implemented:
- queryBinding XSLT2
- title

Not implemented:
- schemaVersion check
- queryBinding check
- defaultPhase
- p
- icon
- see
- fpi

##### 5.4.14 value-of element

Not implemented

## Ancillary elements (section 5.5)

None implemented

## Semantics (Section 6)

##### 6.1 validation function

Implemented, insofar the elements from section 5.4 have been implemented.

##### 6.2 Minimal syntax

Partly implemented in the validation, insofar the elements from section 5.4 have been implemented, but cannot be called directly.

##### 6.3 Abstract pattern processing

Implemented but needs verification of the specification.


##### 6.4 Query language binding

Only implemented for XSLT2.

##### 6.5 Order and side-effects

Not fully implemented; all rules are currently checked, instead of the if-then-else structure specified.