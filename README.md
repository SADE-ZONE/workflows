# SADE Overview 
This site documents the architecture and workflows of the SADE infrastructure.  For further project-level information please visit our public site <a href="https://sites.nd.edu/uli-drone-reputations/" target="_blank" rel="noopener noreferrer">here</a>.


#### Architecture ([link](pages/architecture.md)).
The SADE architecture integrates local ground control, cloud-based UTM services, and trust infrastructure to manage safe drone entry, monitoring, and exit within regulated airspace zones. It combines real-time telemetry, rules-based decision-making, anomaly detection, and auditable certification to support accountable and scalable autonomous operations.

#### Workflow:
The SADE workflow includes the following critical elements:
- **Entry Request:** A [SADE Zone entry request](pages/entry_handshake.md) may be submitted by a drone or via an organization’s Ground Control Station and specifies the scope of access (entire zone, region, or route) along with required identifiers and timing. The SADE Agent evaluates the request and issues an entry decision that may approve the request with or without constraints, require specific actions, or deny access based on rules, reputation, and prior incidents. When additional evidence or mitigations are needed, these are provided through [signed certifications](pages/certificates.md) or directed tests in a [proving ground](pages/proving_ground.md), with all evidence securely stored and cryptographically anchored for auditability.  
- **In Zone Monitoring:** While flying in the Zone, the SAM performs lightweight monitoring to check for Significant Observable problems (SIGOPs).  This data is collected and aggregated into a **reputation model**. Upon exit from a Zone, flight data is aggregated as a transaction into the [reputation model](pages/reputation_modeling.md).
- **User Interaction:** SADE Zone users are able to view their records [respond to documented SIGOPs](pages/user_response.md) and to voluntarily [report](pages/voluntary_reporting.md) previously unobserved SIGOPS.

## Major Solution Elements
- **Decision making**: Decision making responsibility is assigned to the *SAM Decision-Making Agent*, which retrieves information from the SADE Manager about the operating environment, retrieves information from the reputation model, and, when needed, requests additional information from the Drone|GCS|organization. The agentic approach allows consideration from these heterogenous data sources.
- **Common Data Description Language**: To facilitate this cooperation across the Decision-Maker, Reputation Model, SafeCert, and Proving ground, SADE uses a common specification language to request and provide evidence.  [Link](pages/evidence.md).
- **Runtime Monitoring and Reputation Modeling**: [link](pages/reputation_modeling.md)
- **SafeCert**: [link](pages/certificates.md)
- **Proving Ground**: [link](pages/proving_ground.md)
- **User Input**: [link](pages/user_reponse.md) Users can respond to incidents captured in their reputation models and voluntarily report incidents. 
- **Project Glossary**: [link](pages/glossary.md) 

