# Site Overview 
This site documents the architecture and workflows of the SADE infrastructure.  For further project-level information please visit our public site <a href="https://sites.nd.edu/uli-drone-reputations/" target="_blank" rel="noopener noreferrer">here</a>.


#### SADE Architecture ([link](pages/architecture.md)).
The SADE architecture integrates local ground control, cloud-based UTM services, and trust infrastructure to manage safe drone entry, monitoring, and exit within regulated airspace zones. It combines real-time telemetry, rules-based decision-making, anomaly detection, and auditable certification to support accountable and scalable autonomous operations.

#### SADE Workflow:
The SADE workflow includes the following critical elements:
- **Entry Request:** A [SADE Zone entry request](pages/entry_handshake.md) may be submitted by a drone or via an organization’s Ground Control Station and specifies the scope of access (entire zone, region, or route) along with required identifiers and timing. The SADE Agent evaluates the request and issues an entry decision that may approve the request with or without constraints, require specific actions, or deny access based on rules, reputation, and prior incidents. When additional evidence or mitigations are needed, these are provided through [signed certifications](pages/certificates.md) or directed tests in a [proving ground](pages/proving_ground.md), with all evidence securely stored and cryptographically anchored for auditability.  
- **In Zone Monitoring:** While flying in the Zone, the SAM performs lightweight monitoring to check for Significant Observable problems (SIGOPs).  This data is collected and aggregated into a **reputation model**. Upon exit from a Zone, flight data is aggregated as a transaction into the [reputation model](pages/reputation.md).
- **User Interaction:** SADE Zone users are able to view their records [respond to documented SIGOPs](pages/user_response.md) and to voluntarily [report](pages/voluntary_reporting.md) previously unobserved SIGOPS.

#### 
### Formal Language for Data Requests and Evidence
[Requirements and Evidence Grammar](pages/evidence.md)
The SAM-Gateway will use a subset of this language to request evidence, and the Drone|GCS (using services of SafeCert) will provide evidence as meta-data attached to an uploaded certificate using the same language extended to include claims extracted from the safety case.

#### Project [Glossary](pages/glossary.md) 
Common project level terms.
