# Security, Privacy and Audit for Regulated Platforms

**Parent:** 08 — Regulated and Advanced Systems  
**Target:** Senior Backend / AI Platform / MLOps Engineer  
**Study time:** 3–4 hours plus lab  
**Scope note:** Engineering education, not legal advice; applicability must be confirmed with counsel/compliance.  
**Lab:** [`lab/`](lab/) — a canonical hash-chained audit log with six adversarial tests

## 1. FOUNDATIONS

### Begin with harm and trust boundaries

Security protects systems and information from unauthorized access, change, disclosure and disruption. Privacy governs legitimate processing of information about people—even when every byte is securely encrypted. Auditability supplies evidence of what happened, who or what acted, under which authority, and whether controls operated. They overlap but are not interchangeable: an encrypted database copied by an overprivileged employee is secure in transit yet an unauthorized privacy disclosure; a complete audit log does not make that disclosure lawful.

The classic **CIA triad** is confidentiality, integrity and availability. Regulated platforms add authenticity, accountability, purpose limitation, data minimization and individual rights. A **threat** is a potential cause of harm; a **vulnerability** is a weakness; **risk** combines likelihood and impact under uncertainty; a **control** changes risk. **Residual risk** remains after controls and must be consciously accepted by an authorized owner, transferred, avoided or reduced—not hidden in a spreadsheet.

A **principal** is a human or workload identity. **Authentication** establishes who it is; **authorization** decides what that principal may do to which resource under which context. A **trust boundary** is where identity, privilege or data exposure changes: browser to API, application to database, tenant to tenant, training to production, or company to cloud/provider. **Zero trust** means no implicit trust from network location; each access is explicitly authenticated, authorized and observed. It does not mean trusting nobody or adding MFA to every machine call.

### Privacy vocabulary

**Personal data** relates to an identifiable person under the applicable definition. HIPAA uses **protected health information (PHI)** within covered contexts; electronic PHI is **ePHI**. Payment-card data has account-data categories under PCI DSS. **Data controller/fiduciary** determines purpose and means; a **processor** acts for it, though exact statutory names differ. **Processing** includes collection, use, storage, sharing and deletion.

**Purpose limitation** means data collected for claim adjudication is not automatically available for unrelated advertising. **Data minimization** collects and exposes only what the task needs. **Retention** defines how long data/evidence remains; **deletion** must propagate to primary stores, indexes, caches and governed backup expiry. **Consent** is one possible lawful basis, not a universal permission slip. Consent must not be stretched beyond its stated purpose.

**Pseudonymization** replaces direct identifiers while retaining a controlled link; it remains re-identifiable and usually personal data. **Anonymization** aims to prevent identification with reasonably available means and is much harder. Hashing an email without a secret is not anonymization: an attacker can hash candidate emails. **Tokenization** substitutes a random token whose mapping resides in a protected vault. **Encryption** preserves recoverability through a key.

### Audit and evidence

An **audit event** records a security/business-relevant action. An **audit trail** orders and protects events. **Tamper-evident** means alteration becomes detectable; **tamper-resistant** makes alteration difficult. A SHA-256 hash chain detects changed/deleted/reordered records only if a trusted checkpoint or external anchor preserves the expected chain head. An attacker who can rewrite every event and the final head defeats an unanchored chain.

**Non-repudiation** is a stronger legal/cryptographic claim than “a log line contains a username.” Digital signatures can authenticate a signer under key-management assumptions, but compromised keys and shared accounts undermine attribution. **Chain of custody** documents evidence collection, transfer, storage, analysis and access so integrity and provenance can be defended.

### Regulatory orientation

India's Digital Personal Data Protection Act, 2023 and notified Digital Personal Data Protection Rules, 2025 create obligations and phased commencement that require current applicability review. The design response is a maintained data inventory, purpose/notice/rights workflows, processor governance, safeguards, breach handling and demonstrable deletion—not merely adding a consent checkbox.

HIPAA applies to covered entities/business associates and defined PHI, not to every health-related application. The current HHS Security Rule remains in effect; HHS explicitly describes the December 2024 strengthening as a **proposed** rule, so do not represent proposals as binding final requirements. The current rule calls for administrative, physical and technical safeguards for ePHI; 45 CFR §164.312(b) addresses audit controls.

PCI DSS applies contractually to environments handling payment account data. Scope reduction through hosted payment pages/tokenization is often safer than storing card data. Compliance is not synonymous with security, and one framework certificate does not transfer responsibility for application authorization or privacy.

## 2. CORE MECHANICS

### 2.1 Classify data and map flows

Build a living inventory: data element, subject, source, purpose/legal basis, system, region, owner, consumers, sensitivity, retention and deletion method. Draw flows including logs, analytics, backups, support exports, feature stores, embeddings, prompts and third parties. “Database encrypted” misses copies in Kafka dead-letter topics and observability payloads.

Use an actionable classification, for example Public, Internal, Confidential and Restricted. Restricted may include PHI, bank credentials, authentication secrets and full card data. Classification must drive controls: who can access, allowed regions, encryption, logging prohibition, retention and incident priority. Overclassifying everything makes controls unusable; underclassification creates exposure.

Example: a claims training snapshot contains date of service, diagnosis codes and a pseudonymous patient token. Removing name does not make it anonymous; combinations may identify someone. Restrict it, separate token mapping, minimize columns, enforce workspace purpose and record lineage.

### 2.2 Threat-model the actual design

Define assets, actors, entry points, trust boundaries, abuse cases and mitigations. STRIDE prompts Spoofing, Tampering, Repudiation, Information disclosure, Denial of service and Elevation of privilege. LINDDUN prompts privacy threats such as linkability and identifiability. Frameworks stimulate thinking; they do not replace system-specific reasoning.

For an ML endpoint, threats include cross-tenant object access, stolen workload identity, poisoned training data, malicious pickle, prompt injection, model extraction, membership inference, denial-of-wallet and sensitive logs. For each, write prerequisite, path, impact, prevention, detection and recovery. Rank using evidence; a numeric risk score is not physics.

### 2.3 Authenticate humans and workloads

Use an identity provider, phishing-resistant MFA for privileged humans, short-lived sessions and explicit reauthentication for sensitive operations. Services use managed/workload identity or short-lived certificates/tokens, not passwords embedded in images. Rotate credentials and design clients to reload them without restart where feasible.

OAuth access tokens authorize resource access; ID tokens describe authentication to a client and should not be accepted as API access tokens unless the protocol explicitly requires it. Validate issuer, audience, signature, time bounds and intended token type. Key rotation means verifiers cache JWKS with bounded refresh and reject unknown algorithms rather than accepting `alg=none`.

### 2.4 Authorize every object and action

RBAC maps roles to permissions; ABAC uses attributes such as tenant, region, purpose and claim assignment; relationship-based control uses graph relationships. RBAC is understandable but role explosion appears when context matters. A practical policy may require role `claims_reviewer`, same `tenant_id`, assigned queue, purpose `adjudication`, and active employment.

Check authorization server-side on every resource, including nested exports and cached responses. A valid `/claims/123` identifier is not proof the caller may view claim 123. Default deny. Separate policy decision from enforcement, but fail closed if the decision service is unavailable for sensitive access. Administrative break-glass access needs justification, time bounds, enhanced logging and retrospective review—not a permanent superuser role.

### 2.5 Isolate tenants and environments

Tenant isolation is an invariant across API, cache, queues, database, object storage, search/vector index, telemetry and model artifacts. Carry trusted tenant context from authenticated identity; never trust a request body tenant ID. Enforce row-level/database predicates or physical separation and test negative cross-tenant cases.

Separate production from development identities and data. Developers should not download production PHI to laptops for debugging. Use synthetic/de-identified fixtures, time-bound approved access and audited support tooling. Network segmentation limits paths but never replaces authorization.

### 2.6 Encrypt and manage keys

TLS protects data in transit; authenticated encryption such as AES-GCM protects confidentiality and integrity at rest/application level. Encryption needs key lifecycle: generation, custody, access policy, rotation, versioning, backup, revocation and destruction. Envelope encryption uses a data-encryption key (DEK) for data and a key-encryption key (KEK) in KMS/HSM to wrap DEKs. Rotation can rewrap DEKs without rewriting terabytes.

Do not reuse a nonce with AES-GCM under the same key; it can destroy confidentiality/integrity. Store key/version and nonce with ciphertext, not the plaintext key. Separate key administration from data administration. A KMS key disabled during an incident can make critical healthcare service unavailable, so recovery and break-glass are tested.

Passwords use a slow password-hashing function such as Argon2id with unique salts, not reversible encryption or plain SHA-256. API keys are high-entropy secrets stored as hashes where verification-only is sufficient. Secrets belong in a secret manager and must not enter source, environment dumps, logs, prompts or experiment trackers.

### 2.7 Minimize, pseudonymize and retain deliberately

Collect fields required for the declared decision. Apply field/row/purpose restrictions close to the source. For analytics linkage, an HMAC with a protected key is harder to enumerate than bare hashes, but remains pseudonymous. Use different domain keys/tokens to prevent unintended linking across products.

Retention is a state machine: active → restricted/legal hold → deletion eligible → deleted/tombstoned → backup expiry verified. Legal hold overrides ordinary deletion under controlled authority. Deletion events should be auditable without retaining deleted content. Immutable backups make instantaneous erasure impossible; document isolation and scheduled expiry, and prevent restoration from resurrecting logically deleted records.

### 2.8 Build safe logs and audit events

Operational logs explain software behavior; audit logs prove relevant actions. Both require time, source, action/result and correlation, but audit events need a stable schema, protected retention and review. Record pseudonymous actor ID, action, resource token, decision, reason/policy version, model/release identity and timestamp. Avoid raw patient names, claim narratives, card numbers and bearer tokens.

The lab canonicalizes JSON with sorted keys and compact separators, then hashes each event with `prev_hash`. Its required schema has eight fields. Sequence 1 links to 64 zeroes; sequence 2 links to sequence 1's event hash. Tests mutate content, delete/reorder events, add fields and attempt `access_token`. All are detected/rejected.

Hash chains do not ensure availability or honest event creation. Send events over authenticated channels to append-only storage under a separate security account, checkpoint chain heads to independent storage, synchronize time, restrict deletion, and alert on sequence gaps/export lag. Sign/checkpoint batches when stronger origin evidence is required.

### 2.9 Review access and evidence

Collecting logs without examination is not an audit-control program. Define high-value queries: repeated denials, break-glass use, new admin grants, bulk export, cross-region access, model approval/deploy by the same person, logging disabled and key policy changes. Assign owners and review cadence; retain review evidence and disposition.

Least privilege is continuously verified through access reviews and unused-permission analysis. Joiner/mover/leaver workflows remove privileges promptly. Separation of duties can require one person to build and another to approve/promote a regulated model. Service accounts need owners and expiry/review like people.

### 2.10 Secure the software and ML supply chain

Pin dependencies and base images, scan vulnerabilities/licenses, produce SBOM/provenance, sign artifacts and verify signatures/digests before deployment. Protect CI credentials and branch rules. A signed malicious build remains malicious if the signing pipeline is compromised; harden and isolate builders.

Treat models as code. Pickle deserialization can execute code. Restrict formats/loaders, scan archives against path traversal/decompression bombs, load under sandbox/least privilege and promote from trusted registries. Data poisoning needs source authorization, anomaly checks, snapshot lineage and approval; model extraction needs auth, quotas and monitoring.

### 2.11 Handle incidents and breaches

Prepare detection, triage, containment, evidence preservation, eradication, recovery, notification decision and learning. Do not delete compromised instances before capturing required volatile evidence; isolate them. Rotate credentials based on exposure and dependency order. Preserve who collected what, hashes, time and transfers.

A “security incident” is not automatically a legally reportable breach. Privacy/legal teams determine applicable definitions, risk assessment, affected people and notification clocks. Engineers provide reliable facts: data types, subjects, systems, access evidence, encryption/key exposure, duration and containment. Never delay internal escalation while waiting for certainty.

### 2.12 Test the audit lab

```bash
cd lab
python3 -m unittest -v test_audit_chain.py
```

The six dependency-free tests prove local invariants. Production additionally needs authenticated ingestion, durable ordered partitions, trusted timestamps/checkpoints, retention locks, replication, monitoring and key management.

## 3. WORKED PROBLEMS

### Problem 1 — Security versus privacy (easy)

A properly encrypted claims table is queried by marketing using a valid broad role. Is encryption sufficient?

**Solution.** No. Encryption worked, but purpose and authorization may be invalid. Remove excess access, assess disclosure, narrow policy by purpose/role/tenant, review logs and involve privacy/security. **Mistake:** equating confidentiality controls with lawful processing.

### Problem 2 — Broken object authorization (easy)

User A changes `/claims/C1001` to `/claims/C1002` and sees another tenant's claim.

**Solution.** The API authenticated A but failed resource authorization. Derive tenant from identity, query with tenant predicate, default deny, test horizontal/vertical access, investigate exposure and invalidate affected caches. **Mistake:** treating unguessable IDs as access control.

### Problem 3 — Pseudonymization (medium)

Emails are stored as unsalted SHA-256. Is the dataset anonymous?

**Solution.** No. Candidate emails can be hashed and matched. Use data minimization and, if linkage is required, keyed HMAC/token vault with separated access and domain keys. It remains pseudonymous. **Mistake:** calling deterministic hashes anonymization.

### Problem 4 — Envelope-key rotation (medium)

One million 1-MB objects each use a DEK wrapped by KEK v4. KEK v4 must rotate. Must 1 TB be re-encrypted?

**Solution.** If policy/cryptography permit, unwrap each DEK and rewrap it with KEK v5; object ciphertext stays. Validate access, versions, rollback and completion. A compromised DEK requires its object's data re-encryption. **Mistake:** confusing KEK rotation with DEK compromise.

### Problem 5 — Detect log tampering (medium)

An attacker edits audit event 41 and recomputes hashes through 100. Local verification passes against the rewritten chain.

**Solution.** Compare head 100 with a prior signed/external checkpoint. They differ. Without an independently protected head, the chain alone cannot detect full-history rewrite. **Mistake:** claiming hashes make storage immutable.

### Problem 6 — Calculate audit volume (medium)

At 2,000 events/s and 620 bytes/event, estimate decimal storage/day before replication/indexes.

**Solution.** `2,000×620×86,400=107,136,000,000` bytes ≈107.136 GB/day. Three replicas imply 321.408 GB/day before compression/index overhead. **Mistake:** omitting replication and secondary index cost.

### Problem 7 — Break-glass design (hard)

Clinicians need emergency record access during an identity-policy outage.

**Solution.** Predefine a minimal emergency role, strong alternate authentication, explicit reason, short expiry, patient-context constraint, immediate alert and retrospective review. Keep the path tested and auditable; never use a shared static admin password. **Mistake:** choosing either zero availability or unlimited bypass.

### Problem 8 — Sensitive ML artifact (hard)

An experiment tracker stores 50 misclassified rows including diagnosis, claim ID and analyst notes.

**Solution.** Restrict and preserve evidence, stop further logging, determine access/exposure, delete under retention/incident policy, and replace rows with aggregate/safely governed references. Tracking needs RBAC but minimization remains primary. **Mistake:** assuming internal ML tools are approved PHI repositories.

### Problem 9 — Triage suspected breach (hard)

An object-store access key appeared in logs for 18 minutes; access logs show two reads from a new IP.

**Solution.** Revoke/rotate immediately, isolate affected workload, preserve immutable logs, determine key scope and exact objects/actions, assess data encryption and key access, hunt persistence, recover safely and escalate to incident/privacy/legal teams. Notification is a legal determination based on evidence. **Mistake:** declaring “no breach” because objects were encrypted without checking key/path exposure.

## 4. REAL-WORLD / APPLIED CONTEXT

HHS states the HIPAA Security Rule protects confidentiality, integrity and availability of ePHI through administrative, physical and technical safeguards. Its audit protocol for §164.312(b) asks for mechanisms that record and examine activity—not merely log collection. HHS also says the 2024 Security Rule change is proposed and the current rule remains effective, an important interview distinction.

PCI DSS v4.0.1 organizes requirements around protecting account data, access, monitoring/testing and policy. A sound product reduces cardholder-data scope using a compliant provider/token and prevents full PAN from reaching application logs. Scope must be confirmed with the acquirer/QSA; “we use cloud” does not remove it.

The lab's actual chain contains deterministic canonical bytes and 64-hex SHA-256 links. Six tests execute on the workspace CPython runtime in about a millisecond. This proves functional cases only, not cryptographic system assurance or performance at 2,000 events/s.

## 5. COMPARISON TABLE

| Control | Concrete property | Use | Boundary |
|---|---|---|---|
| RBAC | Role→permission | Stable job duties | Role explosion/context gaps |
| ABAC | Tenant/purpose/time attributes | Context-rich decisions | Policy/testing complexity |
| Shared DB + row policy | Lower cost | Many similar tenants | One predicate bug has broad blast radius |
| Separate DB/account | Stronger boundary, higher ops cost | High-value/regulatory isolation | Fleet/schema overhead |
| Encryption | Reversible with key | Confidential storage/use | Key exposure restores data |
| Tokenization | Mapping isolated in vault | Payment/direct identifiers | Vault availability/security |
| Bare hash | Deterministic, enumerable | Integrity of nonsecret bytes | Not anonymization |
| Hash chain | Detects edits against trusted head | Ordered audit evidence | Cannot stop deletion/full rewrite alone |
| WORM/object lock | Resists deletion for retention | Evidence/backups | Misconfigured retention and cost |
| Pseudonymization | Controlled relinking | Longitudinal analytics | Still personal data |
| Anonymization | Intended irreversible identity removal | Aggregate release | Re-identification risk |

## 6. COMMON MISTAKES & MISCONCEPTIONS

1. Compliance certificate equals security—application threats remain.
2. Internal traffic is trusted—authenticate/authorize workloads across every boundary.
3. JWT validation means authorization—object, tenant, action and context checks remain.
4. Encryption solves privacy—purpose, minimization, rights and retention remain.
5. Hashed identity is anonymous—dictionary/linkage attacks often work.
6. Logs should contain everything—secrets/PHI increase breach scope; log safe evidence.
7. Append-only means immutable—privileged deletion/rewrite and lost checkpoints remain.
8. More retention is safer—unnecessary data increases exposure and cost.
9. Proposed regulation is current law—track status and cite authoritative text/date.
10. Break-glass bypasses audit—emergency access needs stronger, not weaker, accountability.
11. Shared service account identifies an actor—it destroys individual attribution.
12. Backups need no deletion design—restore can resurrect expired/deleted data.

## 7. CHEAT SHEET — REVIEW ONLY

> Review only; not a substitute for the full lesson.

- Inventory data, purpose, flow, owner, region, access, retention and deletion.
- Authentication identifies; authorization decides action/resource/context.
- Derive tenant from trusted identity; default deny; negative-test isolation.
- Envelope encryption: data with DEK, DEK wrapped by KEK; manage full lifecycle.
- Hash/HMAC/token/encryption are not synonyms; pseudonymous is not anonymous.
- Audit event: who/what/when/action/resource/result/reason/policy/model, without payload/secrets.
- Hash chain requires protected external checkpoint.
- Review logs; detect gaps, lag, admin grants, exports and break-glass.
- Models/dependencies are supply-chain artifacts; verify before load.
- Preserve evidence and escalate suspected exposure early; counsel decides notification.

## 8. PRACTICE SET FOR SELF-TEST

1. Explain one case that is secure but privacy-invalid.
2. Why is a user-supplied `tenant_id` unsafe even with a valid JWT?
3. At 750 audit events/s and 800 bytes/event, calculate decimal GB/day before replication.
4. What independent object makes a SHA-256 chain detect a complete history rewrite?
5. Distinguish encryption, tokenization and pseudonymization.
6. Name five fields in a safe model-deployment audit event.
7. A DEK is compromised. Why is rewrapping it with a new KEK insufficient?
8. Give four controls for emergency break-glass access.
9. Why should a proposed HIPAA rule not be described as a current requirement?
10. Name three places a deletion workflow often misses.

## 9. CURATED RESOURCES

1. [India Digital Personal Data Protection Act, 2023 (MeitY)](https://www.meity.gov.in/data-protection-framework) — authoritative statutory starting point and notifications; verify commencement/applicability.
2. [Digital Personal Data Protection Rules, 2025 explanatory note (MeitY)](https://www.meity.gov.in/writereaddata/files/Explanatory-Note-DPDP-Rules-2025.pdf) — official rule structure and phased implementation context.
3. [HHS HIPAA Security Rule](https://www.hhs.gov/hipaa/for-professionals/security/index.html) — current-rule status and administrative/physical/technical safeguard scope.
4. [HHS HIPAA Audit Protocol](https://www.hhs.gov/hipaa/for-professionals/compliance-enforcement/audit/protocol/index.html) — concrete evidence questions for audit controls and integrity.
5. [PCI DSS v4.0.1 Document Library](https://www.pcisecuritystandards.org/document_library/) — authoritative payment-card requirements and versioned supporting guidance.
6. [NIST SP 800-53 Rev. 5](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final) — detailed Access Control, Audit, Identification, System Integrity and PII control families.
7. [NIST Privacy Framework 1.0](https://www.nist.gov/privacy-framework) — Identify-P, Govern-P, Control-P, Communicate-P and Protect-P outcomes.
8. [OWASP ASVS 4.0.3](https://owasp.org/www-project-application-security-verification-standard/) — testable application-security requirements beyond a generic checklist.
9. [RFC 8725: JSON Web Token Best Current Practices](https://www.rfc-editor.org/rfc/rfc8725) — algorithm verification, substitution and cross-JWT confusion defenses.
10. **Ross Anderson, _Security Engineering_, 3rd ed., Chapters 2–6 and 26** — threat/economic thinking, access control, cryptography and logging limits.

## 10. RELATED TOPICS BRIDGE

### Before

1. **Identity and Networking** — supplies workload identity, TLS, private paths and firewall boundaries.
2. **Observability** — supplies safe structured telemetry, detection and correlation.
3. **ML Lifecycle** — supplies lineage, artifact registry and approval evidence.
4. **Distributed Systems** — supplies durable ordering, replay and failure semantics for audit pipelines.

### After

1. **Healthcare and Fintech Design** — applies controls to domain workflows and failure consequences.
2. **GPU Inference** — protects accelerator hosts, model artifacts and shared memory/scheduling.
3. **Multitenancy and FinOps** — deepens isolation, quotas, noisy-neighbor and cost abuse controls.
4. **Incident Response** — operationalizes containment, evidence, notification support and recovery.

---ANSWER KEY BELOW---

1. Marketing accesses encrypted claims using a technically valid role but without compatible purpose/authority.
2. The caller can substitute another tenant; derive tenant membership from authenticated server-side identity and enforce it on the resource query.
3. `750×800×86,400=51,840,000,000` bytes = 51.84 GB/day decimal.
4. A trusted signed/externally protected checkpoint of the expected chain head (plus protected sequence context).
5. Encryption is key-reversible ciphertext; tokenization uses a separate mapping vault; pseudonymization reduces direct identity but retains controlled relinking and remains personal.
6. Pseudonymous actor/workload, timestamp, action, resource token, allow/deny result, reason, policy version, model/release digest—any five.
7. Anyone holding the old DEK can still decrypt old ciphertext. Generate a new DEK and re-encrypt affected data, then revoke old material.
8. Strong alternate authentication, minimal role/scope, justification, short expiry, immediate alert, retrospective review, individual identity—any four.
9. A proposal can change or never become final; current engineering/legal claims must cite the currently effective rule while planning separately for likely change.
10. Search/vector indexes, caches, analytics copies, logs, feature stores, dead-letter topics, third-party processors and backup restoration state—any three.
