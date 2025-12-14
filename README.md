# Site Overview 
This site documents the architecture and workflows of the SADE infrastructure.  For further project-level information please visit our public site <a href="https://sites.nd.edu/uli-drone-reputations/" target="_blank" rel="noopener noreferrer">here</a>.


#### SADE [Architecture](pages/architecture.md)
The SADE architecture integrates local ground control, cloud-based UTM services, and trust infrastructure to manage safe drone entry, monitoring, and exit within regulated airspace zones. It combines real-time telemetry, rules-based decision-making, anomaly detection, and auditable certification to support accountable and scalable autonomous operations.

#### Project[Glossary](pages/glossary.md) 
Common project level terms.

#### SADE Workflow:

### SADE On-Entry:
[](pages/entry_handshake.md)
Describes the general flow of messages and function calls during an on-entry event. At the highest level, when a Drone|Pilot|Organization requests entry into the Sade Zone, the SAM_Agent will draw on currently available reputation data to make an initial decision.  IIF needed, it will request additional evidence of flight capability via an additional series of messages.  All requests and all subsequent data is provided using the Formal Language (see next section).

### Formal Language for Data Requests and Evidence
[Requirements and Evidence Grammar](pages/evidence.md)
The SAM-Gateway will use a subset of this language to request evidence, and the Drone|GCS (using services of SafeCert) will provide evidence as meta-data attached to an uploaded certificate using the same language extended to include claims extracted from the safety case.

