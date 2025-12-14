# SADE Zone Architecture (High-Level)

<img
  src="../figures/images/SADE-architecture.png"
  alt="SADE Zone architecture diagram"
  width="900"
/>

This system supports **SADE Zone entry/exit decisions, monitoring, and post-mission reporting** for drone operations using a hybrid of local ground-control services and AWS cloud services.

## Main components

- **Drones / Proving Ground**
  - Drones publish telemetry and SADE-zone requests (e.g., status, attitude, battery, and entry/exit intent).
  - The proving ground can observe and validate operations, with cloud-side monitoring via AWS.

- **Ground Control Services (local)**
  - A local **MQTT broker** and ground-control tooling (e.g., digital twin / air-traffic coordination) support mission operations and bridge data flows toward the cloud when needed.

- **AWS IoT Core Message Bus (cloud backbone)**
  - Acts as the central event and telemetry bus for status streams and SADE-zone request/decision messaging.

- **UTM SADE Zone Manager**
  - The cloud-side orchestration layer for SADE-zone workflows, integrating:
    - **SADE Rules Engine** to evaluate entry/exit requests, policy constraints, and detected anomalies.
    - **Persistence** of inbound status messages (e.g., via **AWS Lambda → Amazon DynamoDB**).
    - **Anomaly detection pipeline** (containerized services via **ECR / Fargate**) to analyze telemetry and emit anomaly/incident signals.
    - **Observability** (e.g., **CloudWatch** logs/metrics) for operations and debugging.

- **Web Interface**
  - Supports human-facing workflows such as **incident reporting** and **certificate creation**, and can query for certifications and reputations.

- **Blockchain Layer**
  - Stores/serves **reputation models** and **certificates** to support auditable trust and compliance signals used by the platform.

## Typical data flow

1. **Drones → AWS IoT Core**: publish status and entry/exit requests.
2. **IoT Core → SADE Zone Manager**: routes telemetry and requests to the rules engine, persistence, and anomaly detection services.
3. **Rules/analytics → Decisions & Incidents**: decisions (entry/exit) and anomalies/incidents are emitted back through IoT Core.
4. **Web Interface ↔ Trust artifacts**: users create incident reports/certificates and query reputation/certification data (backed by the blockchain layer).
