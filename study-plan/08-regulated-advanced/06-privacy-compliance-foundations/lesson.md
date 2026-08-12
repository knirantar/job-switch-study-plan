# Privacy, Audit, Risk, and Compliance Foundations

Parent subject: `08-regulated-advanced`
Study time: 3–4 hours
Target: senior backend / AI platform / MLOps interviews

## 1. FOUNDATIONS

### Privacy is about people and legitimate use

Privacy concerns appropriate collection, use, sharing, retention, and control of information about people. Security protects data and systems against unauthorized harm, but a perfectly secured system can still violate privacy by collecting excessive data, using it for an incompatible purpose, retaining it forever, or making an unfair automated decision.

Privacy requirements come from laws, regulations, contracts, professional ethics, organizational policy, and user expectations. They differ by jurisdiction, sector, role, data, and processing purpose. Engineers should know the vocabulary and build enforceable mechanisms, while qualified legal/privacy/compliance owners interpret obligations. This lesson is engineering education, not legal advice.

### Personal data and sensitive data

**Personal data** identifies or relates to an identifiable person directly or indirectly. Names and IDs are obvious; IP addresses, device IDs, location, behavioral history, and combinations can identify. **Sensitive** or special-category data often includes health, biometrics, financial/account information, sexuality, religion, caste, and credentials depending law.

**Direct identifiers** identify alone. **Quasi-identifiers** such as age, postcode, admission date can re-identify in combination. **Derived/inferred data**—risk score, predicted disease, credit propensity—is still personal and can be more consequential than raw input.

Data about companies can contain personal contacts. “Publicly available” does not mean unlimited reuse. Synthetic data can leak training records or preserve re-identification patterns; assess generation and utility/privacy empirically.

### Roles and actors

Terminology varies. GDPR uses data subject, controller (determines purpose/means), processor (acts for controller), subprocessor, and supervisory authority. India's Digital Personal Data Protection Act uses Data Principal, Data Fiduciary, Data Processor, and Consent Manager concepts. HIPAA uses covered entity, business associate, protected health information. PCI DSS defines merchants/service providers and cardholder data environment.

The same company can be controller/fiduciary for one processing and processor for another. Role determines contract, instructions, rights, breach, and deletion obligations. Architecture should record tenant/customer role, purpose, subprocessor chain, and geography rather than label the entire platform once.

### Data lifecycle

Map data from collection/generation through transmission, storage, use, derivation, sharing, archival, and deletion. For each element record source, subject, purpose, legal basis/authority, classification, schema, location/region, encryption/key, access, recipients/subprocessors, retention, deletion method, backup behavior, and owner.

Unknown “dark data” cannot be protected or deleted. Data catalogs and lineage help, but telemetry, caches, notebooks, support exports, model features, embeddings, prompts, backups, and dead-letter queues are often omitted.

### Privacy principles

Widely recurring principles:

- lawfulness/fairness/transparency;
- purpose limitation;
- data minimization;
- accuracy;
- storage limitation;
- integrity/confidentiality;
- accountability;
- individual participation/rights.

Minimization means collect/use only what is adequate, relevant, and necessary for defined purpose. It reduces breach impact, cost, and bias. “Could be useful for ML later” is not a purpose.

### Consent and other bases

Consent, where used, should be informed, specific, freely given where applicable, affirmative, recorded, and withdrawable as easily as granted. Bundled or forced consent may be invalid. Consent is not always the correct basis; healthcare treatment, contract, legal obligation, legitimate use, public interest, or other statutory bases may apply depending law.

Consent state includes subject, controller, purpose, data categories, recipients, versioned notice, grant time/method, expiry, withdrawal, authority/guardian, and evidence. Withdrawal stops future processing under that basis and triggers downstream action; it does not necessarily erase data retained under another lawful obligation. Do not model consent as one global boolean.

### Individual rights

Depending jurisdiction: access, correction, deletion/erasure, restriction, objection, portability, information, grievance, nomination, and protections around automated decision-making. A rights workflow must authenticate requestor without collecting excessive new data, discover systems, apply exceptions/retention/legal holds, coordinate processors, meet deadlines, provide understandable output, and record evidence.

Deletion is a distributed workflow. Live DB, replicas, indexes, caches, object versions, feature store, vector index, logs, support exports, and backups have different semantics. Backups may age out under documented retention rather than surgical deletion, with controls preventing restored data from re-entering active use.

### De-identification and pseudonymization

**Pseudonymization** replaces identifiers with a token while a separately protected mapping can reconnect; data remains personal. **Anonymization** aims to make re-identification not reasonably possible under the applicable standard and context; it is difficult and can degrade as auxiliary data grows.

Hashing an email without secret is often reversible by dictionary and linkable across datasets. Use keyed tokenization/HMAC with domain separation and protected keys for pseudonymous joins, while treating outputs as personal. Encryption is reversible and not anonymization.

k-anonymity requires each quasi-identifier combination appear at least k times; it does not prevent attribute disclosure or background knowledge. Differential privacy provides a mathematical bound on how much one individual's inclusion changes output distribution, using epsilon/delta and privacy budget, but implementation/accounting/utility require specialists.

### Privacy by design and impact assessments

Privacy by design embeds controls from requirements through deletion: safe defaults, minimization, purpose-tagged access, isolation, transparency, secure lifecycle, and demonstrable compliance. A privacy impact assessment/DPIA identifies processing, necessity/proportionality, subjects, risks, safeguards, residual risk, consultation, and approvals—especially for large-scale sensitive monitoring or high-impact automated decisions.

AI assessment includes training provenance, lawful basis, representation, sensitive inference, explainability, human oversight, contestability, security, model memorization, downstream uses, and monitoring. A model card alone is not an impact assessment.

### Compliance and controls

**Compliance** means satisfying applicable obligations. A **control objective** states desired outcome; a **control** implements it; evidence demonstrates operation; testing evaluates design and effectiveness. Policies say what/why, standards mandatory specifics, procedures how, guidelines recommended.

Frameworks such as ISO/IEC 27001, SOC 2 Trust Services Criteria, NIST Privacy Framework, HIPAA safeguards, PCI DSS, RBI directions, and India's DPDP regime overlap but differ. Certification/attestation has scope and period; it does not prove every product/config secure or legally compliant.

### Audit and evidence

Auditability means reconstructing who did what, to which resource/data, when, from where/context, why/authority, outcome, and policy/version. Audit logs should be append-oriented, access-controlled, time-synchronized, integrity-protected, retained, searchable, and monitored. They should minimize sensitive payload.

Evidence includes policy approval, access review, role grants, deployment/provenance, consent record, processing inventory, risk assessment, vendor due diligence, training, vulnerability/patch, incident response, backup/restore test, deletion completion, and control test. Screenshots alone are weak: prefer system-generated, immutable, time-bounded evidence linked to scope and identity.

**Chain of custody** records evidence collection, handling, transfer, storage, hash, and access so integrity is defensible. Audit-log hashing can detect modification under assumptions but does not make false events truthful or prevent deletion without external anchoring/retention.

### Third parties and cross-border data

Vendors/subprocessors introduce data access, locations, security, incident, deletion, business continuity, and subcontractor risk. Due diligence precedes access; contracts define instructions, confidentiality, security, breach notification, assistance, return/deletion, audit, and location. Continuously inventory and reassess.

Cross-border transfer rules and localization vary and change. Record actual data flows, storage/backup/support locations, remote access, subprocessors, and legal mechanism. A cloud region selection alone does not control telemetry, support, identity, or SaaS integrations.

### Breach and notification

A personal-data breach can involve confidentiality, integrity, or availability. Response: contain, preserve evidence, determine data/categories/subjects/locations/encryption, likelihood and harm, notify internal legal/privacy/security, regulators/subjects/partners within applicable rules, remediate and document. Do not delay escalation waiting for perfect record counts.

Security incident and reportable privacy breach are related but not identical; designated owners make notification decisions with evidence.

## 2. CORE MECHANICS

### 2.1 Build a data inventory row

`claim_document`: subject patient; source hospital upload; purposes adjudication/legal record; fields diagnoses/invoices/IDs; sensitive health+financial; controller hospital, processor platform; India region; encrypted object store; access adjudicator and scoped service; retention seven years per approved policy (example, verify law/contract); subprocessors OCR; deletion/hold behavior; owner Claims Privacy.

Include copies: thumbnail, OCR text, embedding, prompt context, logs, backup. Each has lineage and retention.

### 2.2 Minimize an API

Fraud model needs age band, amount, velocity, merchant risk—not full date of birth, name, address, PAN. Tokenize account, derive age band upstream, avoid raw identifiers in feature store, set feature TTL, and document purpose. Test that disallowed columns never enter payload/log.

Minimization can reduce debugging; provide governed break-glass access to source where necessary rather than copying everywhere.

### 2.3 Model purpose-bound consent

```text
ConsentGrant(id, subject, controller, purpose_code, data_categories,
 notice_version, recipients, granted_at, expires_at, withdrawn_at,
 authority, evidence_uri, status_version)
```

Authorization checks current grant plus purpose, resource, relationship, expiry, withdrawal, and overriding legal rule. Cache must honor revocation boundedly. Events carry grant ID/version, not full sensitive content.

### 2.4 Execute a rights request

1. Receive and assign case/deadline.
2. Verify identity/authority proportionately.
3. Determine jurisdiction/role/scope/exception.
4. Search catalog/lineage by subject tokens and direct identifiers.
5. Place legal hold conflict for review.
6. Export/correct/delete/restrict across systems/processors.
7. Validate, obtain processor attestations, prevent cache/index resurrection.
8. Provide safe response and grievance route.
9. Retain minimal case evidence.

Never send raw data to an unverified email based only on matching name.

### 2.5 Retention policy

Define trigger (claim closure), duration, basis, object categories, legal hold, archive, deletion method, backup expiry, derived data, owner, and evidence. Lifecycle automation marks eligible, checks holds, deletes in bounded batches, records non-sensitive evidence, retries/quarantines failures, and reports exceptions. Test clock boundaries and immutable storage locks.

### 2.6 Pseudonymous token

Use HMAC-SHA-256 with separate secret key and domain context: token=`HMAC(key,"patient-id:v1:"||normalized_id)`. This prevents simple dictionary without key and cross-purpose linking if distinct keys/domains. Normalize unambiguously, rotate/version keys while supporting joins, restrict mapping/source. Treat token as personal.

### 2.7 Access review

Quarterly/system-risk-based review lists identity, role/permissions, resource/data classification, owner, grant reason, last use, expiry, segregation conflicts. Managers/data owners attest or revoke; dormant/terminated users auto-disable. Evidence includes input snapshot, decisions, completion, exceptions and remediation. A spreadsheet emailed around without system enforcement is weak.

### 2.8 Audit event

```json
{"event":"patient_record_read","time":"...","actor":"clinician:tokenized",
 "resource":"patient:tokenized","tenant":"T1","purpose":"treatment",
 "policyVersion":"authz-42","decision":"ALLOW","traceId":"...",
 "breakGlass":false}
```

Record denied attempts and break-glass reason/approval. Do not include diagnosis/document. Hash-chain batches and write to immutable retention where warranted; restrict queries and monitor audit access itself.

### 2.9 Risk assessment

Scenario: cross-tenant vector retrieval leaks clinical chunks. Assets/subjects sensitive; threat could be query/user/injection; likelihood from shared index/filter defect; impact severe confidentiality/regulatory. Controls: tenant-scoped index/filter at query, authoritative ACL before context, post-check, test, audit/DLP, canary. Residual risk accepted by accountable owner only after evidence, with review date.

Simple likelihood×impact ranks but do not compare false precision; document assumptions and catastrophic scenarios.

### 2.10 Vendor review

For LLM provider: data use/training, retention/zero-retention, regions/transfers, subprocessors, encryption/keys, identity/private networking, logging, incident notification, deletion, model isolation, prompt/output access, compliance reports scope, availability/exit. Test configuration and contract. Never send PHI/financial data because vendor has a generic compliance badge alone.

## 3. WORKED PROBLEMS

### Problem 1 — Personal data (easy)

Is a stable device ID personal if no name?

**Solution.** Often yes: singles out/links a person/device and combines with other data. Classification depends context/law, but treat cautiously.

**Trap:** only names/emails are personal.

### Problem 2 — Pseudonymization (easy)

Replace patient ID with reversible token. Anonymous?

**Solution.** No; pseudonymous and re-linkable, still protected personal data.

**Trap:** tokenized equals outside privacy scope.

### Problem 3 — Purpose (easy)

Use claims collected for payment to train unrelated advertising model?

**Solution.** Requires new compatibility/lawful authority/transparency assessment; likely incompatible/high risk. Do not assume possession authorizes reuse.

**Trap:** terms saying “improve services” as unlimited purpose.

### Problem 4 — Consent withdrawal (medium)

User withdraws research consent; treatment record retained legally.

**Solution.** Stop future research processing/sharing under consent, remove/restrict research copies/derived data per policy, retain treatment record under distinct basis/retention, record evidence and inform processors.

**Trap:** delete everything or do nothing.

### Problem 5 — Hash email (medium)

SHA-256 lowercase email anonymous?

**Solution.** No. Email space dictionary-attacked and stable hash linkable. Use keyed purpose-specific token, still pseudonymous.

**Trap:** cryptographic hash means irreversible in practice.

### Problem 6 — Backup deletion (medium)

Must immediately edit every immutable backup for erasure?

**Solution.** Depends applicable rules/policy. Common design: isolate backups, prevent ordinary use, expire on bounded schedule, and reapply deletion on restore. Document/approve; not an excuse for indefinite retention.

**Trap:** backups exempt forever.

### Problem 7 — Audit payload (hard)

Log full patient record to prove what was viewed?

**Solution.** Excessive duplicate breach surface. Log protected identifiers, action, purpose, policy/version, result, trace and content/version digest where necessary; source record remains authoritative.

**Trap:** more audit data always better.

### Problem 8 — Model deletion (hard)

One subject requests deletion from a trained model.

**Solution.** Determine role/basis/applicable right and whether record was training data; remove source/future datasets, prevent retraining, assess model memorization/influence and available unlearning/retrain; document proportional validated action. Models complicate deletion and require upfront governance.

**Trap:** deleting training row automatically changes existing weights.

### Problem 9 — Compliance report (hard)

Vendor has SOC 2; safe to send PHI?

**Solution.** Not by itself. Review report scope/period/exceptions, contract/role, healthcare obligations, data use/region/subprocessors, configuration, controls, breach/deletion, and risk approval.

**Trap:** badge transfers accountability.

## 4. REAL-WORLD / APPLIED CONTEXT

### India's DPDP Act

India's Digital Personal Data Protection Act 2023 establishes obligations for digital personal data, Data Fiduciaries/Processors, notice/consent and certain legitimate uses, Data Principal rights/duties, security safeguards and breach notification, with details dependent on commencement/rules. Engineers must verify current official rules and organizational counsel rather than rely on static summaries.

### HIPAA

US HIPAA Privacy/Security/Breach rules govern covered entities/business associates and PHI/ePHI under defined scope. The minimum necessary standard, safeguards, BA agreements, risk analysis, access/audit and breach processes influence platforms handling US healthcare—but HIPAA does not cover all health data or replace state/other laws.

### PCI DSS

PCI DSS protects account data in card payment environments. Tokenization and outsourcing can reduce scope only when designed/validated. Sensitive authentication data such as CVV must not be stored after authorization under PCI rules. Prefer provider-hosted/tokenized flows to minimize card data touching systems.

## 5. COMPARISON TABLE

| Technique | Re-identifiable | Utility | Main purpose | Limitation |
|---|---|---|---|---|
| Encryption | Yes with key | Full | Confidentiality | Authorized decrypt/access remains |
| Tokenization | Yes via vault/mapping | High | Reduce identifier exposure/scope | Mapping security/linkability |
| Keyed pseudonym | Via source/key/context | Join utility | Controlled pseudonymous linkage | Still personal, dictionary if key leaks |
| Generalization | Sometimes | Reduced | k-anonymity-like grouping | Attribute/background attacks |
| Aggregation | Depends cell/query | Aggregate | Reporting | Small groups/differencing |
| Differential privacy | Bounded individual influence | Noise tradeoff | Statistical release | Budget/implementation complexity |
| Deletion | Intended removal | None for removed use | Lifecycle/rights | Distributed copies/backups/models |
| Access control | Data unchanged | Full for authorized | Limit use | Misconfiguration/insider/overprivilege |

## 6. COMMON MISTAKES & MISCONCEPTIONS

1. Privacy equals security—legitimate overcollection/misuse can be secure.
2. No name means anonymous—quasi-identifiers/linkage identify.
3. Public data is free for any purpose—context/law/expectation apply.
4. Consent is universal legal basis—it may be inappropriate/invalid.
5. Consent is one boolean—purpose/version/expiry/withdrawal matter.
6. Encryption anonymizes—it is reversible.
7. Hashing identifiers anonymizes—dictionary/linkability persist.
8. Delete one DB row completes erasure—copies/derived/processors remain.
9. Audit should store full payload—minimize and protect evidence.
10. Compliance certification means secure product—it has scope/period.
11. Cloud region alone solves localization—support/telemetry/backups matter.
12. Model weights are automatically outside privacy—they can memorize/infer.

## 7. CHEAT SHEET — REVIEW ONLY

Review only, not a substitute for the lesson.

- Inventory direct, quasi, derived, telemetry, model/embedding data.
- Record role, purpose/authority, location, access, recipients, retention, owner.
- Minimize before encrypting.
- Consent is purpose/version/subject/evidence/expiry/withdrawal, not boolean.
- Rights workflow authenticates, discovers, applies exceptions, validates downstream.
- Pseudonymous remains personal; anonymization is contextual/difficult.
- Retention has trigger, period, hold, deletion, backup and evidence.
- Audit actor/action/resource/purpose/policy/result—not sensitive payload.
- Control objective→control→evidence→test→exception/remediation.
- Vendor badge is input, not approval.
- Escalate suspected breach early; preserve evidence and assess scope.

## 8. PRACTICE SET FOR SELF-TEST

1. Classify IP, employee ID, diagnosis inference, aggregate of two people.
2. Design consent record for research use.
3. List data lifecycle locations for RAG.
4. Explain keyed pseudonym versus anonymous data.
5. Outline an access request workflow.
6. Define retention for failed payment events.
7. Design minimal audit event for export.
8. List vendor assessment fields for feature store SaaS.
9. Explain legal hold conflict with deletion.
10. Describe privacy impact assessment for clinical AI.

## 9. CURATED RESOURCES

- NIST Privacy Framework 1.0 — Identify-P, Govern-P, Control-P, Communicate-P, Protect-P outcomes and privacy risk management.
- ISO/IEC 27701:2019 overview and organizational licensed standard — privacy information management extension to ISO 27001/27002.
- India Code, *Digital Personal Data Protection Act, 2023*, plus current official MeitY rules/notifications — primary Indian law; verify commencement and rules at study/use time.
- EU GDPR official text, Articles 5–6, 12–22, 25, 28, 30, 32–35, 44+ — principles, bases, rights, design, processor, records, security, breach, DPIA and transfers.
- US HHS official HIPAA Privacy, Security, and Breach Notification Rule resources — authoritative covered-role/PHI/safeguard/breach guidance.
- PCI Security Standards Council, *PCI DSS v4.0.1* — official cardholder data environment requirements and testing procedures.
- Ann Cavoukian, *Privacy by Design: The 7 Foundational Principles* — canonical proactive/default/embedded/full-lifecycle framework.
- NIST SP 800-122, *Guide to Protecting the Confidentiality of PII* — PII impact levels and safeguards.

## 10. RELATED TOPICS BRIDGE

### Before

1. **Security Foundations:** identities, access, crypto, logging, incidents.
2. **Data/ML Lifecycle:** lineage, schemas, models, derived data.

### After

1. **Healthcare/Fintech Domain Foundations:** applies data roles and sector obligations.
2. **Security, Privacy and Audit advanced:** implements tamper evidence, isolation and lifecycle.
3. **Healthcare/Fintech Design:** applies consent, FHIR, ledger and oversight.
4. **Multitenancy/FinOps:** tracks tenant purposes, location, isolation and deletion.

---ANSWER KEY BELOW---

1. First three generally personal; tiny aggregate can be re-identifiable and needs disclosure control.
2. Subject/authority, controller, specific research purpose, categories, recipients, notice version, grant method/time, expiry, withdrawal, evidence, version.
3. Source docs, chunk store, embeddings/vector index, metadata/ACL, query/prompt, model provider, cache, logs/traces/evals, feedback, backup/DLQ.
4. Keyed pseudonym supports controlled relinking/joins and remains personal; anonymous aims no reasonable re-identification under context.
5. Intake/deadline, proportional identity, role/jurisdiction/scope, catalog search, exceptions/holds, processors, secure export, validation, response/evidence.
6. Purpose/fraud/legal/audit basis, trigger, exact period approved by owners, immutable ledger relationship, hold, archive/delete and backup expiry/evidence.
7. Time, actor/workload, tenant, export action, dataset/query/version, purpose/approval, record count/destination classification, result, trace—no exported rows.
8. Role/purpose/data use, security/IAM/encryption, region/transfers/subprocessors, retention/deletion, incident, availability/DR, audit, exit, compliance scope.
9. Hold suspends destruction for scoped records under authority; restrict other use, document, resume deletion after release.
10. Processing/necessity, subjects/data/flows, model/data provenance, risks/bias/safety/rights, security, human oversight/contestability, controls/evidence, residual approval/monitoring.
