# Site Overview
This site documents the architecture and workflows of the SADE infrastructure.  The overall project goals are described [here](https://sites.nd.edu/uli-drone-reputations/)

# SADE Architecture

### Project Glossary: 
[Glossary](documentation/glossary.md) 
Update shared vocabulary to this file.  Use it throughout project documentation.


### SADE On-Entry:
[Field Integration](documentation/workflow/entry_handshake.md)
Describes the general flow of messages and function calls during an on-entry event. At the highest level, when a Drone|Pilot|Organization requests entry into the Sade Zone, the SAM_Agent will draw on currently available reputation data to make an initial decision.  IIF needed, it will request additional evidence of flight capability via an additional series of messages.  All requests and all subsequent data is provided using the Formal Language (see next section).


### Formal Language for Data Requests and Evidence
[Requirements and Evidence Grammar](documentation/workflow/evidence.md)
The SAM-Gateway will use a subset of this language to request evidence, and the Drone|GCS (using services of SafeCert) will provide evidence as meta-data attached to an uploaded certificate using the same language extended to include claims extracted from the safety case.

