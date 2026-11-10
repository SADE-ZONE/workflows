# SafeCert Certificates and SADE Attestations

This page describes what SafeCert does today when SADE asks it for evidence: which SADE keywords it can answer, which certificate answers each one, how it decides whether a certificate counts, and the exact JSON it sends back.

The general request/attestation language is defined in [evidence_data_exchange.md](./evidence_data_exchange.md). The SADE endpoints are documented in the [SADE API reference](./SADE_AWS_API/API_REFERENCE.md#safecert-api).

## How it works

Certificates are earned **before** SADE asks for them. A pilot fills in a certificate form in SafeCert, such as the Wind Certificate, and SafeCert evaluates the answers against a GSN safety-case argument. The result is a stored certificate that has passed or failed and has an expiry date. Proving-ground tests produce a second kind of certificate, a signed PG deposit for a drone.

When SADE sends an `EVIDENCE_REQUIREMENT`, SafeCert does **not** compute anything from the request's `params`. For each requirement, it looks up the pilot's existing certificates for that `keyword` and checks whether one of them counts. The one exception is `MAX_WIND_GUST`, whose gust speed is checked against the Wind Certificate (see [Parameters](#parameters)).

1. SADE posts the request to SafeCert at `POST /api/sade/saveNotification`.
2. If every requirement is met, SafeCert immediately sends SADE an `EVIDENCE_ATTESTATION` with every requirement marked `SATISFIED`. This closes the request on SafeCert's side.
3. If any requirement is not met, SafeCert immediately sends an attestation that marks the met requirements `SATISFIED` and the rest `NOT_SATISFIED`, each with a reason. The request **stays open** in SafeCert.
4. An open request is answered with a full `SATISFIED` attestation later, as soon as it can be met. That happens in one of three ways:
   - the pilot submits a form that produces the last missing certificate;
   - a proving-ground deposit arrives for the request's drone;
   - the pilot clicks **Submit to SADE** on the SADE history page. This only sends an attestation when every requirement is met; it never sends a partial answer.

Attestations go to SADE at `POST https://api.sadezone.org/attestation-submission` over mutual TLS. SADE's decision is read back afterwards from `GET /actions/{action_id}`.

## Supported keywords

| SADE keyword | Answered by | Must be for the request's drone? |
| --- | --- | --- |
| `MAX_WIND_GUST` | Wind Certificate (form). The gust in `params` is checked. | Yes |
| `WIND` | Wind Certificate (form). `params` are not checked. | Yes |
| `PART_107` | Experience Certificate (form) | No |
| `BVLOS` | BVLOS Certificate (form) | Yes |
| `TEMPERATURE` | Temperature Certificate (form). This keyword is SafeCert's guess and has not been confirmed with SADE. | Yes |
| `PROVE_WIND_CAPABILITY` | Proving-ground Wind certificate (`PG_Wind_Certificate`, from the PG Wind Test) | Yes |
| `CONFIGURATION` | Configuration Certificate (form). SADE has no matching keyword yet. | No |

The Configuration Certificate exists, but SADE does not send a matching keyword yet.

**Any other keyword** (for example `PAYLOAD`, `PROVE_PAYLOAD_CAPABILITY`, `NIGHT_FLIGHT` or `SADE_ATC_API`) is answered `NOT_SATISFIED` with the reason `SafeCert has no certificate for <KEYWORD>`. A request that contains such a keyword therefore can never be fully satisfied by SafeCert. SafeCert has no payload certificate yet.

SafeCert ignores the `category` of each requirement and echoes it back unchanged. If a keyword appears more than once in a request, the same certificate answers every occurrence.

## When a certificate counts

A **form certificate** satisfies a requirement when all of these are true:

- its type is one of the certificates listed for the keyword above;
- it belongs to the request's `subject.pilot_id`;
- it passed its evaluation;
- it has not expired;
- it is for the request's `subject.drone_id`, when the requirement is about the drone. That is the case when the requirement's `applicable_scopes` includes `"UAV"`. If a request sends no `applicable_scopes`, the drone must match for the Wind, Temperature and BVLOS certificates (the ones issued for a specific drone).
- it meets the requirement's parameters, where SafeCert checks them (only `MAX_WIND_GUST`).

If several certificates qualify, the newest is used.

A **proving-ground certificate** names a drone, not a pilot. The pilot therefore can't be checked; instead the deposit must meet all of these:

- it is for the request's `subject.drone_id`;
- the test was a real flight, not a simulation;
- it is fully verified: signature, certificate chain, signer role, integrity, digest and envelope checks all passed;
- its `PG_Wind_Certificate` evaluation passed;
- its signed `valid_until` date is in the future.

## Parameters

Only `MAX_WIND_GUST` parameters are checked. The rule is:

> requested gust (mph) ≤ the Wind Certificate's `MAX_WINDSPEED` × `SUSTAINED_WINDS_PERCENT`

`MAX_WINDSPEED` is in mph and `SUSTAINED_WINDS_PERCENT` is a fraction, for example 0.8. The gust can be given in any of these forms:

- **Plain strings:** `"params": ["28mph"]`
- **Key/value pairs whose key contains `gust`, `wind` or `speed`:** `"params": [{"key": "gust_now_knots", "value": "24"}]`. The unit comes from the value or from a suffix on the key (`_mph`, `_kt`, `_kts`, `_knots`, `_mps`, `_kmh`, `_kph`).
- **In `expr` when `params` is empty:** `"expr": "MAX_WIND_GUST(28mph)"`

The accepted units are mph, kt / knots, m/s and km/h. If several speeds are given, the highest is used. A speed that can't be read makes the requirement `NOT_SATISFIED`.

For every other keyword, including `WIND`, the `params` are echoed back but not checked.

## Certificate inputs

These are answered by the pilot in SafeCert's forms, not sent by SADE.

| Certificate | Main inputs (units) |
| --- | --- |
| Wind Certificate | drone, `SUSTAINED_WINDS` (mph), `MAX_WINDSPEED` (mph), `SUSTAINED_WINDS_PERCENT`, plus yes/no answers on forecast, monitoring, operating within limits and a return-to-launch plan |
| Temperature Certificate | drone, `temp_at_takeoff`, `min_temp`, `max_temp`, `temp_buffer` (°F), `density_alt_at_takeoff`, `max_alt`, `density_alt_buffer` (ft), plus yes/no answers on forecast and monitoring |
| BVLOS Certificate | drone, operating and coordinator hours, `ADSB_detection_range` and `flight_range` (miles), plus yes/no answers on training, Remote ID, ADS-B, detect-and-avoid, airspace and NOTAMs |
| Experience Certificate | `part_107` (yes/no), `date_last_pilot_training_date` |
| Configuration Certificate | yes/no answers on whether the configuration was flown, simulated, checked and tuned |

## Example request from SADE

This is the shape SADE sends today. SafeCert requires `request_id`, `subject.pilot_id` and at least one requirement with a `keyword`; otherwise it replies 400. A repeated `request_id` gets 409. If the request includes an `action_id`, SafeCert stores it.

```json
{
  "type": "EVIDENCE_REQUIREMENT",
  "spec_version": "1.0",
  "request_id": "c556d770-1d35-4bfb-b805-6b42d1cf9d27",
  "subject": {
    "sade_zone_id": "PPT-SADE-1",
    "pilot_id": "FA34567890",
    "organization_id": "ORG-789",
    "drone_id": "2IVJG8QD9N"
  },
  "categories": [
    {
      "category": "ENVIRONMENT",
      "requirements": [
        {
          "requirement_id": "req-max-wind-gust",
          "expr": "MAX_WIND_GUST(28mph)",
          "keyword": "MAX_WIND_GUST",
          "params": ["28mph"],
          "applicable_scopes": ["UAV"]
        },
        {
          "requirement_id": "req-part-107",
          "expr": "PART_107",
          "keyword": "PART_107",
          "params": [],
          "applicable_scopes": ["PILOT"]
        }
      ]
    }
  ]
}
```

## Example attestation sent to SADE

In this example the pilot has a qualifying Wind Certificate for drone `2IVJG8QD9N` but no Experience Certificate. One requirement is `SATISFIED` and the other is `NOT_SATISFIED`. The ids and timestamps are illustrative.

```json
{
  "idempotency_key": "3f1c9a52-7d0e-4b8a-9c61-2e5f8d7a4b10",
  "submission_time_utc": "2026-11-10T15:04:12.345Z",
  "type": "EVIDENCE_ATTESTATION",
  "spec_version": "1.0",
  "attestation_id": "ATT-c556d770-1d35-4bfb-b805-6b42d1cf9d27",
  "in_response_to": "c556d770-1d35-4bfb-b805-6b42d1cf9d27",
  "subject": {
    "sade_zone_id": "PPT-SADE-1",
    "pilot_id": "FA34567890",
    "organization_id": "ORG-789",
    "drone_id": "2IVJG8QD9N"
  },
  "categories": [
    {
      "category": "ENVIRONMENT",
      "requirements": [
        {
          "requirement_id": "req-max-wind-gust",
          "applicable_scopes": ["UAV"],
          "expr": "MAX_WIND_GUST(28mph)",
          "keyword": "MAX_WIND_GUST",
          "params": ["28mph"],
          "status": "SATISFIED",
          "issued_at_utc": "2026-11-01T14:20:00.000Z",
          "expires_at_utc": "2027-11-01T14:20:00.000Z",
          "evidence_ref": "attestation:6730a1f2c4e5b8d9a1b2c3d4",
          "signature_ref": null,
          "meta": {
            "status": "SATISFIED",
            "cert_id": "6730a1f2c4e5b8d9a1b2c3d4",
            "issuer": "SafeCert"
          }
        },
        {
          "requirement_id": "req-part-107",
          "applicable_scopes": ["PILOT"],
          "expr": "PART_107",
          "keyword": "PART_107",
          "params": [],
          "status": "NOT_SATISFIED",
          "meta": {
            "issuer": "SafeCert",
            "status": "NOT_SATISFIED",
            "reason": "No Experience Certificate was found for pilot FA34567890."
          }
        }
      ]
    }
  ],
  "signatures": [
    {
      "signer": "ORG-789",
      "signature_type": "DIGITAL_SIGNATURE",
      "signature_ref": "6730a1f2c4e5b8d9a1b2c3d4"
    }
  ],
  "evidence_refs": [
    {
      "evidence_id": "EVID-6730a1f2c4e5b8d9a1b2c3d4",
      "kind": "DOCUMENT_OR_ARTIFACT",
      "ref": "6730a1f2c4e5b8d9a1b2c3d4"
    }
  ]
}
```

### Field notes

- **`attestation_id`** is always `ATT-<request_id>`. A later full attestation for the same request reuses it, with a new `idempotency_key`.
- **`in_response_to`** is the `action_id` from SADE's request if there was one, otherwise the `request_id`.
- **`requirement_id`, `applicable_scopes`, `expr`, `keyword` and `params`** are echoed back from the request. If a request has no `requirement_id`, SafeCert derives one from the keyword, for example `req-max-wind-gust`.
- **A `SATISFIED` requirement** also carries:
  - `issued_at_utc`, the date the certificate was created;
  - `expires_at_utc`, the certificate's expiry date, or `null` if it has none;
  - `evidence_ref` of the form `attestation:<cert_id>`;
  - `signature_ref: null`.

  `cert_id` is SafeCert's id for the certificate: a form submission, or a PG deposit for `PROVE_WIND_CAPABILITY`.
- **A `NOT_SATISFIED` requirement** has only `meta.issuer`, `meta.status` and `meta.reason`, following the example the SADE team sent on 2026-11-09. The reason says either that no certificate exists or why the newest one fails. Examples:
  - `No Wind Certificate was found for pilot FA34567890 and drone blue. The pilot has one only for drone 2IVJG8QD9N.`
  - `The Wind Certificate for drone 2IVJG8QD9N issued 2026-11-01 does not meet MAX_WIND_GUST(60mph): the drone's allowed wind (35 mph x 0.8 = 28.0 mph) is below the 60.0 mph gust.`
  - `The Wind Certificate for drone 2IVJG8QD9N issued 2026-11-01 did not pass. Failed: "Operator will return to launch if wind conditions warrant." ([RETURN_TO_LAUNCH_PLAN] == true).`
  - `No certificate was found: SafeCert has no certificate for PAYLOAD.`
- **`signatures`** has one entry, signed as the request's `organization_id`, when any certificate was used. It is `[]` when nothing was satisfied. **`evidence_refs`** lists every certificate used.

## Open questions

- Confirm SADE's keyword for temperature. SafeCert currently uses `TEMPERATURE`.
- Should `WIND(<speed>)` be checked against the Wind Certificate the way `MAX_WIND_GUST` is? Today its speed is ignored.
- A payload certificate is needed for `PAYLOAD` / `PROVE_PAYLOAD_CAPABILITY`.
- Is there a SADE keyword for the Configuration Certificate?
