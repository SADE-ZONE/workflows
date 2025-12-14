# Entry request
An entry request may be made directly by a drone or by the organization (i.e., via a Ground Control Station (GCS)).  The entry request always includes: SADE Zone ID, Pilot ID, Organization ID, Drone ID, Requested Entry Time, and [Request].

The [**Request**] is one of three types:
- **ZONE**: request entry to the entire zone (e.g., *ZONE*)
- **REGION**: request entry to a region within the zone defined as a polygon, plus a ceiling and floor (meters ASL).
  - Example 1: *REGION <Polygon>, ZONE_CEILING, GROUND*
  - Example 2: *REGION <Polygon>, 300m, 250m*
- **ROUTE**: request permission to fly a specific route, defined by a series of waypoints, where each waypoint is defined as *latitude, longitude, altitude(ASL)*.

![On-entry handshake](../figures/svg/sade_entry.svg)

## Entry Decision ##
Entry decisions are made by the **SADE Agent** described here.
An entry decision includes the following response:
- **APPROVED**: request is approved without modification. 
- **APPROVED-CONSTRAINTS**: request is approved with constraints in the following format: *APPROVED-CONSTRAINTS*,(constraint-1, constraint-2,...,constraint-n).  Example constraints include:
  - Maximum speed limit: e.g., *SPEED_LIMIT(7ms)*
  - Maximum altitude: e.g., *MAX_ALTITUDE (300m)*. Note: ZONE_MAX_ALTITUDE >= MAX_ALTITUDE.
  - Reduced or modified waypoints or region perimeter.
- **ACTION-REQUIRED**: the request is denied pending specific actions and/or certifications.  Message is structured as *ACTION-ID,ACTION-REQUIRED,Action-List*. 
- **DENIED**: request is denied. Message is structured as *DENIED,DENIAL_CODE,Explanation*.
  
## Required Actions
There are several types of actions that might be required. In each case, the action required will be clearly specified using pre-defined SADE syntax.  Actions include the following:
- **Additional Evidence**: In this case, the reputation model alone has provided insufficient evidence that the Drone/Pilot/Organization is competent to complete its requested mission. Therefore additional evidence is required in the form of a *certificate*. The certificate is generated in one of two ways:
  - A person (e.g., pilot or other organizational representative) uses the *SafeCert* to produce a safety-case demonstrating the required competency. 
  - The drone and/or pilot executes a series of directed tests in the *proving ground*. If the drone passes the tests, a certificate is generated uses the *SafeCert* structure, and the certificate is automatically sent to the SAM Gateway, and the *Entry Decision* is re-issued as *Approved* or *Approved-Constraints*.
- **Mitigation Needed**: This case occurs when (i) a previous incident has been recorded (from prior flight in a SADE zone, or self-reported incident), (ii) The SADE Agent considers the incident severe enough that a mitigation report is called for, and (iii) no mitigation report has been provided.  

All evidence provided by Pilots and/or other persons representing the organization are electronically signed, stored in the SADE Zone's database, and associated with a small permanent hash record in the blockchain. 

## Action Required: Evidence via Certification
When additional competency evidence is requested, the Pilot/Organization will often choose to provide it in the form of a certificate.  This requires (a) understanding exactly what form of certification is needed, and (b) providing it in the standard format. Certificates are generated in two ways.
- **External FAA approved certificates and waivers**: Example 1: Pilot P holds a Part 107 pilot's license that is valid until Date D; Example 2: Organization X holds an FAA waiver for Y. 
- **Safety Cases**: We construct safety cases using the *SafeCert* which adopts Goal Structure Notation (GSN). This means that each safety case is comprised of a hierarchical set of claims supported by arguments and evidence. A user utilizes the *SafeCert* to create primitive safety-cases which they can then generate into more composite safety-cases. However, notably, the SADE Manager is not expected to analyze the safety case and to extract and evaluate its claims.  This is the responsibility of the *SafeCert*.  Instead the dialog between the SADE-Gateway and the *SafeCert* is as follows:
  - *List of missing evidence is returned to the DPO*: Using a DSL (see link) the SADE_Gateway returns a list of missing evidence to the DPO which forwards it to *SafeCert*.
  - *SafeCert responds* by generating best-effort safety case and best-effort list of matching claims.
  - *Operator inspects* generated safety case and matching claims. If the operator deems that the claims do not match the needed evidence, they iteratively (a) collect additional evidence, (b) utilize *SafeCert* capabilities to enhance the safety case and generate a list of claims that is intended to match the evidence, and (c) inspect the results. This process continues either until *SafeCert* generates a list of claims from the safety case that match the required evidence, or the operator otherwise aborts the process.  If sufficient claims are generated, the operator signs-off on the safety-case and its subsequent claims, submits the safety-case to SADE BlockChain, receives a certificate, and submits the claims + certificate back to the SADE-Gateway in response to the *ACTION-REQUIRED* as *ACTION_ID, Certificate), where the Certificate includes the claims and the hash-code.  (Note: Need clarification on what was agreed here, but this will align with what ISU/Wenyi/Theo agreed).

![Certificate needed](../figures/svg/generate_certificate.svg)

## Communicating Evidence Needs 
The above interaction between the SAM-Gateway and the Drone|GCS is therefore predicated upon a request for action that includes a list depicting the *missing evidence*. We define this using a predefined set of keywords connected with a simple syntax.  

