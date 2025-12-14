# Grammar supporting Evidence Requests and Responses

## Purpose

The SAM-Gateway needs a way to describe **evidence that is required** in order to admit a Drone|Pilot|Organization (DPO) trio into a SADE Zone, while the Drone|GCS needs a way to **provide evidence and attestations** in response. The language supports two closely related uses:

#### Evidence Requirement
Used by SAM-Gateway to request missing evidence.
#### Evidence Attestation
Used by SafeCert / Drone|GCS to report actual capabilities, certifications, and supporting artifacts. Both share the same core structure:
- One or more **categories**
- Each category contains a list of **requirements**
- Each requirement may include **parameters**
- Attestations may additionally include **metadata**
- Both requirements and attestations are conveyed using the following grammar and specified semantics, and then wrapping the resulting specification into a JSON payload.  As a look-ahead, here is an example of [requirement](../figures/json/evidence_request_payload.json) payload sent from the SAM-Gateway via Drone|GCS to SafeCert, and the resulting [attestation](../figures/json/evidence_attestation_payload.json).  The following sections explain how this is derived.
---

## Categories
All requirements and attestations MUST appear under one of the following categories:
- **CERTIFICATION**  
  Legal or regulatory authorization (pilot, drone, organization)
- **CAPABILITY**  
  Functional abilities of the drone or system
- **ENVIRONMENT**  
  Operational or environmental constraints
- **INTERFACE**  
  Protocols, APIs, or integration requirements
---

## Requirement Structure (Requests)
A requirement has the form:
```text
KEYWORD
KEYWORD(parameter)
KEYWORD(key=value)
KEYWORD(key=value, key=value)
```
Examples:
- `PART_107`
- `BVLOS(FAA)`
- `MAX_WIND_GUST(28mph)`
- `PAYLOAD(weight<=2kg)`
- `SADE_ATC_API(v1)`
These expressions define **constraints or expectations**, not actual values.
---
## Attestation Structure (Responses)

An attestation reuses the requirement syntax and adds a **metadata block** describing:
- Satisfaction status
- Actual values
- Supporting evidence references

General form:
```text
REQUIREMENT { field=value, field=value, ... }
```
Examples:
- `PART_107 {status=SATISFIED, cert_id=107-ABCDE, issuer=FAA}`
- `BVLOS(FAA) {status=SATISFIED, waiver_id=BVLOS-12345}`
- `PAYLOAD(weight<=2kg) {status=SATISFIED, actual_max=7kg}`
- `NIGHT_FLIGHT {status=SATISFIED, actual=true}`

The original requirement constraint remains visible and auditable in the attestation.

---

## Formal Grammar (EBNF)
### Evidence Requirement Grammar
```ebnf
EvidenceSpec      ::= CategoryBlock { ";" CategoryBlock } ;

CategoryBlock     ::= Category ":" RequirementList ;

Category          ::= "CERTIFICATION"
                    | "CAPABILITY"
                    | "ENVIRONMENT"
                    | "INTERFACE" ;

RequirementList   ::= Requirement { "," Requirement } ;

Requirement       ::= Identifier [ "(" ParameterList ")" ] ;

ParameterList     ::= Parameter { "," Parameter } ;

Parameter         ::= Identifier "=" Value
                    | Value ;

Value             ::= Number [ Unit ]
                    | Identifier ;

Identifier        ::= Letter { Letter | Digit | "_" } ;

Number            ::= Digit { Digit | "." } ;

Unit              ::= "mph" | "m" | "kg" | "Hz" ;

Letter            ::= "A" | … | "Z" | "a" | … | "z" ;
Digit             ::= "0" | … | "9" ;
```

### Evidence Attestation Grammar (Extension)
```ebnf
AttestationSpec       ::= CategoryBlock { ";" CategoryBlock } ;

Requirement           ::= BaseRequirement [ AttestationBlock ] ;

BaseRequirement       ::= Identifier [ "(" ParameterList ")" ] ;

AttestationBlock      ::= "{" FieldList "}" ;

FieldList             ::= Field { "," Field } ;

Field                 ::= Identifier "=" Value ;
```
---

## Common Attestation Fields (Non-Normative)
The following fields are preliminary (we will evolve them):
- `status` = SATISFIED | NOT_SATISFIED | PARTIAL | UNKNOWN
- `actual` (boolean or value)
- `actual_max`, `actual_min`
- `cert_id`, `waiver_id`
- `issuer`
- `expires`
- `evidence` (artifact or document reference)
---

## Semantic Layer 
Meaning is defined via **semantic tables**, not grammar. Operators and regulators may extend these tables over time. Examples include the following. ⚠️ TO DO: **Fix these entries** and decide exactly what is in scope for the next 3 months and add as new rows. Goal: 20 initial rows? (Coordinate with ISU). 
| Keyword       | Category      | Parameters             | Example Evidence Types |
|---------------|---------------|------------------------|------------------------|
| PART_107      | CERTIFICATION | Certificate ID         | FAA certificate        |
| BVLOS         | CERTIFICATION | Type, Certificate ID   | FAA waiver             |
| NIGHT_FLIGHT  | CAPABILITY    | none                   | Lighting + SOP         |
| MAX_WIND_GUST | ENVIRONMENT   | Number + mph           | Ops manual, telemetry  |
| SADE_ATC_API  | INTERFACE     | version                | Protocol logs          |
---

## Example: Evidence Requirement
```text
CERTIFICATION: PART_107, BVLOS(FAA);
CAPABILITY: NIGHT_FLIGHT, PAYLOAD(weight<=2kg);
ENVIRONMENT: MAX_WIND_GUST(28mph);
INTERFACE: SADE_ATC_API(v1)
```
## Example: Evidence Attestation
```text
CERTIFICATION:
  PART_107 {status=SATISFIED, cert_id=107-ABCDE, issuer=FAA},
  BVLOS(FAA) {status=SATISFIED, waiver_id=BVLOS-12345};

CAPABILITY:
  NIGHT_FLIGHT {status=SATISFIED, actual=true},
  PAYLOAD(weight<=2kg) {status=SATISFIED, actual_max=7kg};

ENVIRONMENT:
  MAX_WIND_GUST(28mph) {status=SATISFIED, actual_limit=30mph};

INTERFACE:
  SADE_ATC_API(v1) {status=PARTIAL, actual=v1.0}
```
---

