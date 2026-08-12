# Healthcare and Fintech Domain Foundations from Scratch

Parent subject: `08-regulated-advanced`
Study time: 3–4 hours
Target: senior backend / AI platform / MLOps interviews

## 1. FOUNDATIONS

### Why domain semantics determine architecture

Healthcare and fintech systems process high-impact facts. A technically consistent system can still be wrong if it confuses an order with an administration, authorization with settlement, a diagnosis code with clinical truth, or a displayed balance with ledger evidence. Domain terminology is part of correctness.

These industries also differ across countries, organizations, products, and rails. Learn the conceptual actors and flows, then verify exact regulations, standards, payer/network rules, and contracts. This is engineering education, not medical, financial, or legal advice.

## Healthcare foundations

### Actors and care workflow

Actors include patient, caregiver/guardian, clinician, hospital/clinic, laboratory, pharmacy, insurer/payer, claims administrator, public health body, researcher, regulator, and technology vendor. One organization may play several roles.

A simplified journey: registration/identity→appointment/encounter→history/exam→orders→tests/results→diagnosis/assessment→care plan/prescription→administration/dispense→billing/claim→adjudication/payment→follow-up. Emergency, inpatient, chronic, telehealth, and public-health workflows differ.

**Encounter** is an interaction context. **Observation** is a measured/asserted result. **Condition** represents a clinical problem/diagnosis. **Service request** orders an activity. **Medication request** is prescription/order; **dispense** is pharmacy supply; **administration** records giving medicine. They are not interchangeable.

### Clinical record and provenance

An electronic health record is longitudinal information with authorship, time, source, corrections, legal status, access controls, and clinical context. Clinical data is not ordinary mutable CRUD. Corrections often add amendments/version history rather than erase original; late results and revised diagnoses are expected.

Provenance answers who/what created, when, from which source/transformation, and what it affected. A lab value needs unit, reference range, specimen, method, status (preliminary/final/corrected), effective time and issued time. A bare `glucose=100` is ambiguous and unsafe.

### Identity

Patient matching is difficult: names vary, identifiers change, duplicates/merges exist, newborns/emergencies may lack ID. A medical record number is organization-scoped, not global. Never match solely by name/date of birth. Use governed master patient index/identifiers, probabilistic review where approved, merge/unmerge audit, and human resolution.

India's Ayushman Bharat Health Account (ABHA) and ABDM ecosystem provide national digital health identity/interoperability concepts, but implementation/consent/current specifications must be verified officially. Having an identifier does not authorize record access.

### Clinical terminologies and units

Terminologies encode concepts: ICD for classifications/reporting, SNOMED CT for clinical concepts, LOINC for observations/tests, RxNorm (US) or local drug vocabularies, UCUM for units. Codes have systems and versions; `1234` without system is meaningless. Licensing/geographic use varies.

Store original source text/code and normalized mapping with version/provenance. Mapping is not always one-to-one and can lose nuance. Unit conversion must be exact and clinically validated; mg versus mcg is 1,000× error.

### Interoperability and HL7 FHIR

HL7 v2 messaging is widely used for event-based hospital integration. CDA represents clinical documents. FHIR (Fast Healthcare Interoperability Resources) defines modular resources, RESTful interactions, search, profiles, terminology bindings, extensions, bundles, and versioning.

FHIR resource has `resourceType`, logical `id`, `meta`, data elements, references, and extensions. Example Observation references Patient, uses coded test and Quantity with UCUM unit. FHIR base specification is flexible; an **implementation guide/profile** constrains cardinality, terminology, must-support, extensions, and operations for a use case.

Resource reference can be relative/absolute/logical/contained; resolve under authorization and version context. A Bundle can be transaction/batch/search/document/message; semantics differ. FHIR REST 200 does not mean clinical validation beyond server profile/rules.

### Consent and clinical access

Access depends on patient authorization/consent where applicable, treatment/payment/operations or other authority, clinician relationship, purpose, sensitivity, jurisdiction, emergency/break-glass, and minimum necessary. Consent can permit some data/purposes/recipients/time. Break-glass should require reason, elevated audit, notification/review, not become an admin bypass.

### Clinical decision support and AI

AI output is evidence/recommendation, not automatically clinical truth. Define intended use/population, contraindications, performance slices, calibration, uncertainty, workflow, human oversight, override, explanation/provenance, monitoring, and incident recall. Distribution shift across hospitals, devices, coding and demographics is common.

A safe system distinguishes missing data, not measured, normal, unavailable, and not applicable. It should abstain or route human review when evidence is insufficient. Measure patient/clinical outcomes, not only model AUC/API uptime.

## Fintech foundations

### Actors and accounts

Actors include customer, merchant, issuer (customer bank/card), acquirer (merchant bank), payment processor/gateway, card/network/UPI/NPCI, wallet, clearing house, settlement bank, lender, bureau, regulator, fraud/AML teams. Exact roles vary by rail.

An **account** is a domain entity holding rights/obligations. A **ledger account** records debits/credits. A bank account/wallet/customer display is not necessarily identical to internal ledger account. Available balance, current/ledger balance, pending/held amount, credit limit, and settled balance differ.

### Exact money

Money requires amount plus currency and scale. Store integer minor units (`129900` paise=₹1,299) or fixed decimal with explicit scale/rounding. Never binary float. ISO 4217 currencies have different minor units; JPY commonly zero, KWD three, and special/nonstandard assets vary. Do not assume two decimals.

Operations must prohibit accidental currency mixing. FX conversion includes source amount/currency, rate type/value, quote/expiry, fees, target amount, rounding mode/residual, provider and time.

### Double-entry ledger

Each economic transaction creates postings whose debits and credits balance per currency under accounting convention. The ledger is append-only: corrections use reversing/adjusting entries, not update history. Transaction has stable ID, effective/booking time, status, external reference, postings, provenance and idempotency.

Example customer pays merchant ₹1,000, ignoring fees:

- debit customer liability/account ₹1,000 according to chart convention;
- credit merchant payable ₹1,000.

Signs depend on account type/accounting representation; invariant is sum of signed postings zero per currency. Do not present debit/credit universal as plus/minus without chart.

Balances are derived sums/materialized views and can be rebuilt/reconciled. An account constraint can prevent available funds below allowed limit using serialized/escrow logic. A ledger database transaction atomically writes all postings and idempotency record.

### Payment lifecycle

Card-like flow separates **authorization** (issuer approves/reserves), **capture** (merchant confirms amount), **clearing** (network exchanges financial records), and **settlement** (fund transfer). Reversal releases authorization; refund is a new reverse economic operation after capture/settlement; chargeback/dispute follows separate process.

A success response from gateway may mean authorization, not settlement. Webhooks/events can arrive late, duplicated, and out of order. Store provider event ID/version, verify signature, fetch authoritative status when needed, and model explicit state transitions.

UPI and bank transfer flows have different participant/status semantics; consult current NPCI/RBI/provider specs. Never reuse card state machine blindly.

### Idempotency and state machines

Network retries and timeouts create ambiguous outcomes. Client supplies stable idempotency key scoped to merchant/operation; server stores key+request fingerprint+outcome atomically. Same request replays outcome; different payload conflicts. External provider call also uses supported idempotency/reference and reconciliation.

State machine declares allowed transitions. Payment `CREATED→AUTHORIZED→CAPTURED→SETTLED`; branches failed/expired/reversed/refunded/disputed. Out-of-order event may be ignored, stored pending, or trigger authoritative query. Do not simply assign latest-arrival status.

### Clearing, settlement, and reconciliation

**Clearing** calculates obligations/exchanges transaction data; **settlement** transfers funds. Reconciliation compares independent records: internal ledger, provider/network report, bank statement, merchant orders. Match by reference, amount, currency, date/window/status; classify missing/duplicate/amount/status/timing differences.

Reconciliation is a control because distributed exactly-once is unrealistic. It creates cases, retry/correction, ownership, evidence, and aging. Totals alone can balance while individual records mismatch; compare counts, sums, and row-level identity.

### Fraud, KYC, AML, credit

KYC identifies/verifies customer under applicable rules. AML includes customer due diligence, sanctions/PEP screening, transaction monitoring, suspicious activity workflows, recordkeeping. Engineers implement policy systems but compliance owners define rules/reporting; protect secrecy of investigations.

Fraud models trade loss and customer friction. Thresholds depend on amount/customer/merchant/rail and review capacity. Use step-up authentication, holds, decline, manual review, and post-transaction monitoring. Ensure fairness, explainability/contestability, model governance and adversarial adaptation.

Credit models estimate default/risk; labels mature over months, selection bias and economic shift matter. Regulatory requirements may require adverse-action reasons and prohibit certain discrimination. A high AUC is not approval policy.

## 2. CORE MECHANICS

### 2.1 Model a clinical observation

Required: observation ID/version, patient, encounter, code system+code+display, value type, value, UCUM unit/system/code, effective time, issued time, performer/device/specimen, status, reference range, interpretation, provenance. Validate profile and permitted units/ranges; preserve original.

Example BP uses components systolic/diastolic, both mm[Hg], not one string "120/80" if computable interoperability required.

### 2.2 FHIR resource example

```json
{"resourceType":"Observation","id":"obs-1","status":"final",
 "code":{"coding":[{"system":"http://loinc.org","code":"718-7","display":"Hemoglobin"}]},
 "subject":{"reference":"Patient/p-1"},
 "effectiveDateTime":"2026-08-12T09:30:00+05:30",
 "valueQuantity":{"value":13.2,"unit":"g/dL","system":"http://unitsofmeasure.org","code":"g/dL"}}
```

This is illustrative; validate against intended FHIR version/profile and clinical range. Decimal JSON handling and provenance/version matter.

### 2.3 Consent-aware FHIR query

Authenticate clinician, derive tenant/facility, check active role/relationship/purpose/consent/sensitivity, scope search to patient and allowed resource categories/date, enforce row/document ACL, log decision. Pagination cursor retains scope; bulk export requires separate approval. References returned must not leak inaccessible resource metadata.

### 2.4 Ledger postings

Transaction T ₹1,299 fee ₹29: customer funds decrease 1,299; merchant gets1,270; platform fee29. One representation signed postings: customer funding -129900, merchant payable +127000, fee revenue +2900; sum0. Account-type accounting signs need documented chart. Store INR and prohibit mixing currencies in one balance check.

Use integers: `-129900+127000+2900=0`.

### 2.5 Atomic posting/idempotency

Begin DB transaction; insert idempotency `(tenant,key,fingerprint)` unique; if existing same, return recorded outcome; otherwise lock/conditional update available funds, insert ledger transaction and balanced postings, update derived balance/outbox, store response, commit. Publish event via outbox. Failure rolls back all local changes.

External processor cannot join DB transaction; saga/status/reconciliation handles it.

### 2.6 State transition

Apply event only if provider transaction matches merchant/amount/currency and transition allowed. Keep event inbox unique. A `SETTLED` event arriving before `CAPTURED` may permit direct transition under provider truth or be held/query provider—define per rail. Never regress SETTLED to AUTHORIZED because an older webhook arrives later.

### 2.7 Reconciliation sample

Internal: P1 ₹1000 settled, P2 ₹500 settled, P3 ₹700 pending. Bank: P1 ₹1000, P2 ₹450, P4 ₹200. Results: P1 match; P2 amount mismatch₹50; P3 missing/timing; P4 external-only. Totals internal settled₹1500 vs bank₹1650 difference−₹150, but row cases explain. Aging/window may resolve P3.

### 2.8 Decimal/rounding

₹100 split three ways: 10,000 paise/3=3333 remainder1. Allocate 3334,3333,3333 by documented largest-remainder/order rule so sum exact. Never give each ₹33.33 and lose ₹0.01 without residual account/allocation.

FX ₹1,000 at rate .012345 USD/INR gives $12.345; if USD cents, rounding mode yields $12.35 and residual/accounting documented.

### 2.9 Model decision policy

Fraud score .8 alone is not decline. Policy checks model/version/calibration, amount, rule hits, customer authentication, review capacity, legal/fairness. Outputs approve, step-up, review, decline with reason codes/evidence. Failures: model unavailable may route rules/review, never default approve for high risk.

Clinical score similarly routes recommendation/human, intended-use constraints and contraindications; no automatic extrapolation to unseen population.

### 2.10 Audit and correction

Healthcare correction creates new resource version/amendment with reason/author/time, preserves prior access-controlled history. Financial correction creates reversal and corrected postings linked to original. Both avoid destructive update, preserve provenance, and limit who can correct.

## 3. WORKED PROBLEMS

### Problem 1 — Order versus administration (easy)

Prescription exists. Can system say dose given?

**Solution.** No. MedicationRequest is intent/order; administration record is actual giving; dispense is supply.

**Trap:** conflating workflow events.

### Problem 2 — Unit (easy)

1 mg equals how many mcg?

**Solution.** 1,000 micrograms. Unit code/system and decimal precision essential.

**Trap:** treating unit as display only.

### Problem 3 — Money (easy)

₹1,299.50 in paise.

**Solution.** 129,950 paise.

**Trap:** float multiplication/truncation.

### Problem 4 — Ledger balance (medium)

Customer -50000, merchant +48000, fee +2000.

**Solution.** Sum zero; balanced under stated sign chart.

**Trap:** omitting fee leg and accepting -2000.

### Problem 5 — Authorization timeout (medium)

Gateway times out after issuer may authorize.

**Solution.** Unknown; query/retry with same idempotency/reference, process signed webhook, reconcile. Do not create another payment with new key.

**Trap:** timeout means declined/no hold.

### Problem 6 — Refund versus reversal (medium)

Payment settled, customer returned item.

**Solution.** Refund/new reverse economic transaction, not authorization reversal. Preserve original and link.

**Trap:** overwrite payment status/value.

### Problem 7 — FHIR profile (hard)

Resource valid base FHIR but missing required local field. Accept?

**Solution.** Not for local workflow if implementation guide/profile requires it. Validate FHIR version+profile+terminology and business invariants.

**Trap:** base schema validation equals interoperability.

### Problem 8 — Reconciliation totals (hard)

Internal rows +100,-100; external +200,-200: totals both zero. Reconciled?

**Solution.** No; totals hide identity/amount mismatches. Match transaction references/counts/amount/currency/status/window.

**Trap:** aggregate sum only.

### Problem 9 — Missing clinical feature (hard)

Model fills missing oxygen saturation with zero.

**Solution.** Zero is physiologically meaningful/extreme, not missing. Use missingness indicator/imputation trained/validated, distinguish not measured/unavailable, and route safety/human review.

**Trap:** numeric default for absence.

## 4. REAL-WORLD / APPLIED CONTEXT

### HL7 FHIR

FHIR R4/R4B/R5 coexist; implementation guides constrain base resources. India ABDM publishes FHIR implementation guidance for health information exchange. Servers must advertise CapabilityStatement and support/version/profile explicitly.

### UPI

India's UPI connects participants through NPCI-defined rails with PSPs/banks/apps and asynchronous outcomes. Status, reversal, dispute and reconciliation follow network/provider specs. Use provider transaction references and signed/authenticated interfaces; verify current NPCI/RBI rules.

### Double-entry systems

Stripe/Airbnb-style engineering literature emphasizes immutable ledger entries, balanced transactions, idempotency and reconciliation. Exact proprietary designs differ, but core accounting invariants provide recoverability and audit beyond a mutable balance column.

## 5. COMPARISON TABLE

| Concept | Healthcare | Fintech | Shared invariant |
|---|---|---|---|
| Intent | Service/medication order | Payment command/authorization request | Not proof of completion |
| Completion | Result/admin/dispense | Capture/settlement | Explicit event/state/provenance |
| Correction | amended/new version | reversal+corrected postings | Never erase history casually |
| Identity | patient/facility scoped IDs | customer/account/merchant IDs | Scope and match carefully |
| Vocabulary | SNOMED/LOINC/ICD/UCUM | ISO currency/rail reason codes | system+version+code |
| Source truth | signed clinical record/source system | balanced ledger/provider statement | Reconcile derived caches/views |
| Human oversight | clinician review | fraud/credit/compliance review | High-impact automation bounded |

## 6. COMMON MISTAKES & MISCONCEPTIONS

1. Healthcare record is CRUD row—versions/provenance/corrections matter.
2. Patient identifier means authorization—it does not.
3. Order means performed—intent versus event differ.
4. Code alone is meaningful—system/version/context required.
5. FHIR base validity means local clinical validity—profiles/terminology/business rules remain.
6. Every currency has two decimals—minor units vary.
7. Float is acceptable for money—it is not.
8. Gateway success means settled—lifecycle stages differ.
9. Timeout means payment failed—outcome unknown.
10. Refund and reversal are same—they apply at different stages.
11. Balance column is ledger—evidence is balanced postings.
12. Totals matching proves reconciliation—row identity/status matters.

## 7. CHEAT SHEET — REVIEW ONLY

Review only, not a substitute for the lesson.

- Healthcare: patient→encounter→orders→results/administration→claim/follow-up.
- Intent/order ≠ dispense/admin/result.
- Clinical value includes code system/version, unit, time, status, source/provenance.
- FHIR resource+profile+terminology+authorization, not JSON shape alone.
- Money=amount+currency+scale; integer minor/fixed decimal.
- Ledger append-only balanced postings per currency; balances derived.
- Auth→capture→clearing→settlement; reversal/refund/dispute differ.
- Timeout creates unknown; idempotency+status+reconciliation.
- Webhooks duplicate/reorder; validate signature/reference/state transition.
- High-impact models require intended use, slices, calibration, human/abstain/audit.

## 8. PRACTICE SET FOR SELF-TEST

1. Distinguish Observation, Condition, ServiceRequest, MedicationAdministration.
2. List fields needed for laboratory result.
3. Explain patient merge/unmerge audit.
4. Convert ₹2,345.67 to paise.
5. Balance ₹500 payment with ₹10 fee.
6. Design payment idempotency record.
7. Handle captured webhook before authorized event.
8. Reconcile internal/external sample with missing/duplicate/mismatch.
9. Explain why credit/fraud threshold is policy not model-only.
10. Compare clinical correction and ledger correction.

## 9. CURATED RESOURCES

- HL7 FHIR R4 specification: “Overview,” “Resource,” “References,” “RESTful API,” “Bundle,” “Observation,” “Consent,” and “Provenance” — primary interoperability semantics.
- ABDM official Health Data Management Policy and current FHIR Implementation Guide — Indian health data exchange, consent and profiles; verify current versions.
- SNOMED International, LOINC, ICD-11, and UCUM official documentation — authoritative terminology/unit purpose and use.
- Eric Evans, *Domain-Driven Design*, chapters on knowledge crunching, ubiquitous language, entities/value objects/aggregates — modeling domain semantics with experts.
- PCI SSC PCI DSS v4.0.1 and RBI/NPCI current official payment/UPI guidance — primary payment security/rail obligations relevant to India.
- Richard Gendal Brown, *A Simple Model for Payments* and payment ledger engineering literature — conceptual payment states and ledger separation.
- Martin Kleppmann, *Designing Data-Intensive Applications*, Chapters 9 and 11 — consistency/transactions/stream processing relevant to ledgers/events.
- WHO, *Ethics and Governance of Artificial Intelligence for Health* — intended use, safety, human autonomy, transparency, accountability and equity.

## 10. RELATED TOPICS BRIDGE

### Before

1. **Security Foundations:** identity/access/crypto/integrity.
2. **Privacy/Compliance:** consent, purpose, data lifecycle, audit.
3. **Database/Distributed Systems:** transactions, events, idempotency, consistency.

### After

1. **Healthcare and Fintech Design advanced:** implements FHIR/consent, ledger/sagas/reconciliation and oversight.
2. **Security, Privacy and Audit:** enforces isolation/evidence.
3. **ML Lifecycle:** governs clinical/fraud/credit models.
4. **SRE:** treats correctness and recovery as critical service outcomes.

---ANSWER KEY BELOW---

1. Measured/asserted result; health problem; request/order; actual medication given.
2. Patient/encounter, test code system/version, value/type/unit UCUM, reference/interpretation, specimen/method, effective/issued time, status, performer/device, provenance/version.
3. Link duplicate IDs under governed review, preserve aliases/history/references; unmerge restores wrongly combined records with full audit and downstream correction.
4. 234,567.
5. Example customer -50,000; merchant +49,000; fee revenue +1,000 =0 under documented chart.
6. Tenant+key unique, operation, request hash, state/outcome/response reference, created/expiry, resource/provider reference; atomic with local transaction.
7. Validate provider truth and rail state machine; allow direct monotonic transition or query/hold; do not regress on later older event; inbox deduplicate.
8. Full outer match by stable ref+currency, classify internal-only/external-only/duplicates/amount/status/timing, age and resolve/reverse with evidence.
9. Costs, capacity, fairness, regulation, authentication, amount/context and human review determine action; score is input.
10. New amended/versioned clinical fact with provenance; reversing/adjusting financial entries linked to original; both preserve history.
