
# Threat Model

The repository models and tests at minimum:

- schema-valid but semantically false records;
- silent term mutation;
- codebook version skew;
- missing parent state;
- forged authority metadata;
- replay attacks;
- stale messages;
- hash mismatch;
- claim-register misuse;
- envelope bypass;
- malformed protocol-exception handling;
- self-asserted conformance without validation;
- semantic compression that violates the fidelity floor.
