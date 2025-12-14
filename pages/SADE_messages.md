# APIs and Message Formats

⚠️ **TODO** Discuss (@Theo,@Jane) sequence diagram flow and message format. Note: Where differences exist, we can adapt the syntax documented in this repo, but not the flow. We will need to modify the flow according to these documented processes. 

⚠️ **TODO** We need to add blockchain calls to this file.  Note this file is almost entirely auto-generated from the sequence diagrams. I'd like to create additional sequence diagrams showing BlockChain interactions etc and this file *must* match.

SADE relies on structured message exchanges between architectural components.  
Each message below is documented using a common template derived from the system’s sequence diagrams.  
**This section defines structure only; semantics and deployment details are intentionally left unspecified.**

---

## SADE Entry Workflow 
![On-entry handshake](../figures/svg/sade_entry.svg)

#### MESSAGE: `requestEntry(..)

**Caller:**  
Drone|GCS

**Callee:**  
SAM-Gateway

d**Context:**  
SADE Zone entry workflow

**Transport:**  
⚠️ How is it it sent? What does it look like.  What is the payload?

**Signature:**  
`<topic | endpoint | action>`

**Payload (structure only):**
```json
{
  "SADE_ZONE_ID": "",
  "PILOT_ID": "",
  "ORGANIZATION_ID": "",
  "DRONE_ID": "",
  "REQUESTED_ENTRY_TIME": "",
  "DURATION":"",
  "REQUEST": {
    "TYPE": "ZONE | REGION | ROUTE",
    "DETAILS": {}
  }
}
```

**Expected Responses:**  
- `<ENTRY_DECISION_MESSAGE_NAME>`

---

#### MESSAGE: `<ENTRY_DECISION_MESSAGE_NAME>`

**Caller:**  
`<Component from diagram>`

**Callee:**  
`<Component from diagram>`

**Context:**  
SADE Zone entry decision

**Transport:**  
`<MQTT | HTTP | IoT Core | Other>`

**Signature:**  
`<topic | endpoint | action>`

**Payload (structure only):**
```json
{
  "DECISION": "APPROVED | APPROVED_CONSTRAINTS | ACTION_REQUIRED | DENIED",
  "DETAILS": {}
}
```

---

#### MESSAGE: `<ACTION_REQUIRED_MESSAGE_NAME>` (optional)

**Caller:**  
`<Component from diagram>`

**Callee:**  
`<Component from diagram>`

**Context:**  
Additional evidence or mitigation required

**Transport:**  
`<MQTT | HTTP | IoT Core | Other>`

**Payload (structure only):**
```json
{
  "ACTION_ID": "",
  "ACTIONS_REQUIRED": []
}
```

---

## Diagram: Certificate Generation Workflow (`generate_certificate.svg`)

### MESSAGE: `<CERTIFICATE_REQUEST_MESSAGE_NAME>`

**Caller:**  
`<Component from diagram>`

**Callee:**  
`<Component from diagram>`

**Context:**  
Certificate generation request

**Transport:**  
`<MQTT | HTTP | IoT Core | Other>`

**Signature:**  
`<topic | endpoint | action>`

**Payload (structure only):**
```json
{
  "REQUEST_ID": "",
  "CERTIFICATE_TYPE": "",
  "SUBJECT": {
    "DRONE_ID": "",
    "PILOT_ID": "",
    "ORGANIZATION_ID": ""
  }
}
```

---

### MESSAGE: `<CERTIFICATE_ISSUED_MESSAGE_NAME>`

**Caller:**  
`<Component from diagram>`

**Callee:**  
`<Component from diagram>`

**Context:**  
Certificate successfully generated

**Transport:**  
`<MQTT | HTTP | IoT Core | Other>`

**Payload (structure only):**
```json
{
  "CERTIFICATE_ID": "",
  "HASH_REFERENCE": "",
  "ISSUED_TIMESTAMP": ""
}
```

---

### MESSAGE: `<CERTIFICATE_FORWARDING_MESSAGE_NAME>`

**Caller:**  
`<Component from diagram>`

**Callee:**  
`<Component from diagram>`

**Context:**  
Certificate forwarded for entry reassessment

**Transport:**  
`<MQTT | HTTP | IoT Core | Other>`

**Payload (structure only):**
```json
{
  "CERTIFICATE_ID": "",
  "ASSOCIATED_REQUEST_ID": ""
}
```

---

## Common Message Template

```md
### MESSAGE: <MESSAGE_NAME>

**Caller:**  
<component>

**Callee:**  
<component>

**Context:**  
<workflow or diagram name>

**Transport:**  
<MQTT | HTTP | IoT Core | Other>

**Signature:**  
<topic | endpoint | action>

**Payload (structure only):**
```json
{
}
```

**Responses / Follow-on Messages:**  
- <message name>
```
