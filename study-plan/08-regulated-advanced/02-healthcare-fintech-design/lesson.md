# Healthcare and Fintech System Design: Correctness Under Human Consequence

**Parent:** 08 — Regulated and Advanced Systems  
**Target:** Senior Backend / AI Platform / MLOps Engineer  
**Study time:** 3–4 hours plus lab  
**Scope:** Architecture education, not medical, financial or legal advice  
**Lab:** [`lab/`](lab/) — deterministic advisory claims routing with eight tests

## 1. FOUNDATIONS

Healthcare and fintech look different, but both transform sensitive facts into consequential, time-bound decisions. A duplicate payment can remove money twice; a missing allergy can injure a patient; an incorrect fraud flag can freeze access; a stale medication record can mislead a clinician. Senior design therefore begins with domain invariants and recovery, not endpoint diagrams.

An **invariant** must always hold: a ledger remains balanced; one idempotency key has one semantic result; one patient's record never crosses to another; a model score never silently becomes an adverse final decision. A **workflow** is a state machine whose transitions carry authority and evidence. A **system of record** is authoritative for a fact; a read model/search index is usually derived. **Reconciliation** compares independent records and resolves mismatches. **Compensation** is a new business action that counteracts an earlier committed action; it is not database rollback across organizations.

Healthcare semantics include patient, practitioner, encounter, observation, medication, order, claim, consent and provenance. Clinical data has event time, recorded time, status and author. “Latest” is dangerous: a lab result may be corrected, preliminary, entered late or refer to a specimen collected earlier. Clinical **safety** concerns patient harm; **privacy** concerns appropriate use; **security** supports both but does not define clinical meaning.

Fintech semantics include customer, account, authorization, capture, transfer, settlement, refund, reversal, dispute and ledger entry. An **authorization** reserves/approves funds; **capture** realizes it; **settlement** moves net funds between institutions; a **reversal** releases/corrects an incomplete flow; a **refund** is a later new credit. A **double-entry ledger** records equal debits and credits so postings balance, but balanced fraud or a posting to the wrong account remains possible.

Regulation and scheme rules vary by entity, product, jurisdiction and date. Architecture must map obligations to evidence with counsel/compliance. ABDM's Health Data Management Policy emphasizes consent-based exchange; HL7 FHIR defines interoperable resources and transactions. RBI/NPCI materials govern relevant Indian regulated entities/payment participants and change over time. Never turn an interview answer into “FHIR/HIPAA/PCI makes us compliant.”

## 2. CORE MECHANICS

### 2.1 Model the domain before services

Write states, allowed transitions, actors, clocks and irreversible effects. A claim might move `RECEIVED → VALIDATED → ADJUDICATING → APPROVED/REJECTED → PAID`, with `PENDED` and appeal paths. A payment might move `CREATED → AUTHORIZED → CAPTURED → SETTLED`, or to `DECLINED/REVERSED/REFUNDED`. Reject impossible transitions: a settled transfer cannot be erased; post a reversal/refund with linkage.

Persist state version and transition event atomically. Optimistic concurrency (`WHERE version=7`) prevents two reviewers from both transitioning version 7. Return conflict and reload instead of last-writer-wins. Record business effective time separately from database commit time.

### 2.2 Exact money and dimensional correctness

Never use binary floating point for ledger amounts. `0.1 + 0.2` is not exactly 0.3 in IEEE-754 binary. Use integer minor units where currency exponent is known or fixed-precision decimal with explicit currency and rounding. INR ₹18,500.00 can be 1,850,000 paise. JPY has different minor-unit conventions; do not assume two decimals globally.

A money type is `(amount, currency)`, not a naked decimal. Reject adding ₹100 to $5. Define rounding per product/regulation at a named step. For a 2.5% fee on ₹19.99: exact ₹0.49975; half-up to paise is ₹0.50, but repeated per-item rounding can differ from rounding an aggregate. State which is authoritative.

The lab uses Python `Decimal`, rejects negative/non-finite amount and rejects NaN scores. `Decimal('NaN')` is a boundary candidates often miss because comparisons can raise or behave unexpectedly.

### 2.3 Ledger as immutable postings

Use accounts and balanced journal entries. A ₹1,000 wallet transfer from A to B posts debit A ₹1,000 and credit B ₹1,000 (sign conventions vary); sum by currency is zero. Store entry ID, transaction ID, accounts, amount/currency, effective/recorded time, status and reference. Corrections append reversing entries; never update history in place.

Available balance can differ from ledger balance because authorizations/holds are pending. Cache balances only as rebuildable projections, updated transactionally or from an ordered event stream. Reconcile projection totals to ledger regularly. Database serializability helps local concurrency; it does not make a bank/network call atomic.

### 2.4 Idempotency and exactly-once business effect

Clients retry timeouts because “unknown” is not failure. An idempotency key scopes one intended operation. Store `(tenant, operation, key)` with request fingerprint, status and response in the same transaction as the business write. Same key/same fingerprint returns the recorded response; same key/different amount rejects conflict.

Suppose a ₹2,500 transfer commits but response is lost. Retry with key K must return original transfer T, not create T2. Retention must cover realistic retry/dispute windows. A broker may deliver at least once; consumers deduplicate by event ID and make downstream effects idempotent. “Exactly once” at transport does not cover emails, bank APIs or human actions.

### 2.5 Orchestrate distributed workflows with sagas

A saga coordinates local transactions with events/commands and compensations. Orchestration centralizes state; choreography lets services react to events. For claim payment: reserve funds → record payable → initiate bank transfer → confirm settlement. If transfer fails before settlement, release reservation. If an irreversible transfer settles but notification fails, retry notification—not refund money.

Use an outbox: commit domain change and outgoing event in one database transaction; a relay publishes it. Consumers are idempotent. Inbox/dedup records received IDs. Timeouts create an `UNKNOWN` state requiring status query/reconciliation, not automatic retry of every monetary command.

### 2.6 Reconcile independent truth

Reconciliation compares internal ledger, processor/network reports and bank settlement. Match stable references, amount/currency, state and business date; classify missing/duplicate/mismatched/late. Never “fix” by overwriting one side. Produce controlled adjustments with approval and audit links.

Example: internal shows 10,000 transfers totaling ₹48,250,000; network shows 9,998 totaling ₹48,242,500. Difference is two transfers/₹7,500. Find references, query status, create reversals or missing recognition based on authoritative evidence. Track unresolved ageing and customer impact.

### 2.7 Preserve clinical meaning and provenance

FHIR is an exchange specification, not a database prescription. Resources have identity and version metadata; references connect them. A transaction Bundle is atomic: HL7 FHIR R4 says accept all actions or reject all, while a batch processes independently. Use `Observation` for measured facts, not every clinical statement; status/code/unit/reference range and subject/time are essential.

Terminology systems matter: code plus system/version, not display text alone. `"Glucose"` is ambiguous without specimen/context/unit. Preserve original source, author, timestamps, correction status and transformation provenance. Never silently convert mg/dL to mmol/L without exact analyte conversion and recorded units.

Patient matching is probabilistic and hazardous. Do not merge solely on name/date of birth. Use governed identifiers, match confidence, human resolution and reversible merge/unmerge. Duplicate records and wrong merges are both safety problems.

### 2.8 Consent, purpose and emergency access

Consent is scoped by person, requester, data categories, purpose, time and possibly frequency. Validate current authorization before disclosure; record consent/policy version. Revocation stops future sharing but cannot undo already lawful processing. Some care/emergency/legal bases may differ; encode policy through authoritative governance, not developer guesses.

Break-glass access needs identified clinician, emergency reason, minimum scope/time, immediate alert and retrospective review. It should not become a general outage bypass. Cache authorization carefully: a 24-hour cache can ignore revocation. For unavailable consent infrastructure, choose fail-closed or narrowly governed emergency behavior based on clinical risk and law.

### 2.9 Separate clinical/financial rules from ML advice

Models estimate; policies decide. The lab routes risk `>=0.60` to human review and never denies. Claims `>=₹500,000.00` also review. Missing verified consent/authority is a hard stop that an ordinary override cannot bypass. Record score, threshold, feature/model/policy versions, reasons and final human action.

Avoid automation bias: show limitations and relevant evidence, not a magical “92% confidence.” Calibrated probability is not certainty and may not be individual causal risk. Monitor overrides and outcomes by meaningful slices, but do not punish clinicians/analysts for justified disagreement. Appeals and adverse-action explanations require domain/legal design.

### 2.10 Human-in-the-loop as an engineered queue

Define who may review, what evidence appears, SLA/priority, double-review thresholds, conflict of interest, escalation and timeout. Queue assignment must preserve tenant/patient authorization. A reviewer decision includes structured reason, free text under safe handling, policy version and identity. High-value or irreversible actions may require four-eyes approval.

Measure queue age and downstream harm, not only model throughput. At arrival 100 cases/hour and service 110/hour, net drain is 10/hour; a 500-case backlog takes 50 hours while arrivals continue. Adding ML that sends 30% more cases to review can collapse operations even if AUC rises.

### 2.11 Availability with safe degradation

Classify dependencies. If a recommendation model is down, a clinician may continue without it with a visible warning; if patient identity is ambiguous, fail closed. If a fraud scorer is down, low-risk payments might follow a conservative limit while high-value operations pend—only if policy approves. Never return a fabricated “low risk” default.

Use timeouts, circuit breakers and bounded queues. Preserve requests for asynchronous workflows and expose `PENDING/UNKNOWN` rather than lying. Multi-region active-active money writes require single-writer/consensus or partitioned authority; accepting conflicting balance updates in a network partition violates safety.

### 2.12 Privacy, security and audit in workflows

Derive tenant/patient/account scope from identity. Encrypt, minimize, tokenize direct identifiers and isolate prod. Logs carry correlation and pseudonymous references, not diagnoses/card/auth tokens. Audit access, consent evaluation, model recommendation, override, ledger posting, reconciliation and export.

Detect insider/bulk patterns and review them. Separate maker/checker and model builder/approver. Supply-chain controls cover clinical libraries, payment SDKs and models. Incident runbooks distinguish confidentiality breach, incorrect clinical data, duplicate money effect and availability outage; each has different containment and reconciliation.

### 2.13 Run the policy lab

```bash
cd lab
python3 -m unittest -v test_decision_policy.py
```

Eight tests verify exact inclusive thresholds, high-value routing, model non-denial, authority hard stop, NaN rejection and override evidence. It is educational: production needs authenticated context, durable state/idempotency, policy engine, audit sink and human workflow.

## 3. WORKED PROBLEMS

### Problem 1 — Money representation (easy)

Store ₹18,500.75 as integer minor units.

**Solution.** INR uses paise here: `18,500.75×100=1,850,075` paise, with currency `INR`. Validate exponent from currency metadata. **Mistake:** storing only 1,850,075 without currency/exponent.

### Problem 2 — Idempotent retry (easy)

Transfer ₹2,500 with key K commits; response times out; retry K carries ₹2,600.

**Solution.** Look up K and compare fingerprint. Reject conflict because semantic input differs; return neither a new transfer nor original success as if ₹2,600 executed. **Mistake:** deduplicating on key without request identity.

### Problem 3 — Balance a journal (medium)

A ₹700 refund moves merchant liability back to customer wallet. Construct postings.

**Solution.** Debit merchant/refund funding account ₹700; credit customer wallet liability ₹700 under the system's sign convention; same currency sum is zero. Link original payment and refund ID. **Mistake:** editing the original payment.

### Problem 4 — FHIR transaction versus batch (medium)

Create Patient and Observation; Observation validation fails. What differs?

**Solution.** In a transaction Bundle, the server rejects all actions; in a batch, Patient can succeed and Observation fail with per-entry response. Choose transaction when atomic clinical consistency is required. **Mistake:** assuming every Bundle is atomic.

### Problem 5 — Backlog drain (medium)

Review queue has 1,200 cases; arrivals 80/hour, capacity 140/hour.

**Solution.** Net drain `140−80=60/hour`; ideal drain is `1,200/60=20 hours`. If arrivals reach ≥140, it never drains. **Mistake:** dividing backlog by gross 140.

### Problem 6 — Unknown payment state (medium)

Bank call times out after debit request. Retry immediately?

**Solution.** Persist UNKNOWN, query by stable reference/idempotency key, reconcile and retry only under provider semantics. Blind retry can debit twice. Communicate pending status. **Mistake:** treating timeout as failure.

### Problem 7 — Human override boundary (hard)

Score .92 recommends review; analyst wants straight-through with evidence. Consent is valid.

**Solution.** If policy permits, authorized reviewer records identity, ticket and reason; audit model/policy/recommendation and final route. Monitor outcome. This differs from missing consent hard stop, which ordinary override cannot bypass. **Mistake:** either forbidding all model disagreement or allowing unaudited bypass.

### Problem 8 — Patient merge (hard)

Two records share name and DOB but different national identifiers.

**Solution.** Do not auto-merge. Surface governed identifiers and provenance to authorized matching workflow; assess duplicates/input errors, require review, preserve aliases/history and support unmerge. **Mistake:** prioritizing deduplication rate over wrong-patient harm.

### Problem 9 — Reconciliation discrepancy (hard)

Internal total ₹48,250,000/10,000; network ₹48,242,500/9,998.

**Solution.** Difference ₹7,500 and two records. Match references, identify missing/late/duplicate states, query authority, then append controlled adjustments/reversals. Preserve original ledger and reconciliation evidence. **Mistake:** forcing totals equal by editing history.

## 4. REAL-WORLD / APPLIED CONTEXT

HL7 FHIR R4 defines resources with identity/version and Bundle types. Its transaction processing is all-or-nothing, while batch responses describe each entry. Version-specific references such as `Observation/1/_history/2` support precise provenance; interoperability still requires profiles, terminology and authorization.

ABDM's official Health Data Management Policy describes consent-based health-data exchange and notices/rights. It is a governance source, not permission to centralize every record. Verify current ABDM specifications and applicable Indian law before implementation.

NPCI publishes UPI status, reversal and ecosystem statistics; official FAQs acknowledge cases where debit is not immediately reversed and customers check/raise grievances. This demonstrates why payment APIs expose pending/failed/reversed distinctly and reconcile later instead of mapping every timeout to failure.

The local lab runs eight deterministic CPython tests in roughly a millisecond. That proves policy edge cases, not throughput or regulatory compliance.

## 5. COMPARISON TABLE

| Choice | Concrete behavior | Prefer | Failure boundary |
|---|---|---|---|
| Integer minor units | Exact, currency exponent required | Payment ledger | Multi-exponent/micro-unit complexity |
| Decimal | Exact base-10 with rounding context | Fees/claims | Inconsistent scale/rounding |
| Float | Binary approximation | Scientific non-money values | Ledger equality/rounding |
| FHIR transaction | All entries pass/fail | Atomic related updates | Larger contention/failure scope |
| FHIR batch | Per-entry outcome | Independent bulk work | Partial clinical state |
| Orchestrated saga | Central visible workflow | Complex consequential flows | Coordinator coupling |
| Choreography | Loose event coupling | Simple independent reactions | Hidden cycles/debugging |
| Auto decision | Low latency/cost | Low-impact validated rules | Bias/harm/appeal risk |
| Human review | Judgment/evidence | High-value/uncertain cases | Queue capacity/variability |
| Active-active writes | Regional availability | Partitioned/consensus authority | Conflicting balances/records |
| Single writer + failover | Clear ordering | Ledger/critical record | Failover latency |

## 6. COMMON MISTAKES & MISCONCEPTIONS

1. FHIR means interoperable—profiles, terminology and workflow semantics still differ.
2. HTTP timeout means failure—the remote effect may have committed.
3. Exactly-once broker means exactly-once payment—external effects need idempotency/reconciliation.
4. Double-entry prevents fraud—it ensures balance, not legitimacy/account correctness.
5. Decimal alone solves money—currency, scale and rounding policy remain.
6. Latest clinical value is best—status, event/recorded time and correction matter.
7. Consent is blanket and permanent—scope/purpose/time/revocation matter.
8. Human-in-loop guarantees safety—poor evidence, automation bias and overloaded queues fail.
9. Model confidence is certainty—calibration and individual uncertainty matter.
10. Fail open improves care/finance availability—some identity/authority failures must hard-stop.
11. Reconciliation is a monthly report—it is an operational correctness loop with ageing/escalation.
12. Compensation erases history—it is a new linked business event.

## 7. CHEAT SHEET — REVIEW ONLY

> Review only; not a substitute for the lesson.

- Start with states, actors, authority, clocks, irreversible effects and invariants.
- Money = exact amount + currency + rounding; ledger corrections append.
- Idempotency key + request fingerprint + stored outcome, atomically with effect.
- Timeout → UNKNOWN until status/reconciliation proves outcome.
- Outbox/inbox + idempotent consumers bridge local transactions/events.
- FHIR transaction atomic; batch per-entry; preserve identity/version/provenance.
- Consent: person/requester/data/purpose/time; emergency access is scoped/audited.
- Model recommends; versioned policy decides; adverse actions need oversight/explanation.
- Human queues need capacity, SLA, authorization, evidence and override audit.
- Reconcile independent truth; never overwrite history to force agreement.

## 8. PRACTICE SET FOR SELF-TEST

1. Convert ₹9,876.54 to paise.
2. Why must an idempotency record include request fingerprint?
3. A queue has 900 items, arrival 70/h, service 100/h. Ideal drain time?
4. State the ledger treatment for correcting a settled ₹400 overcharge.
5. When should a FHIR transaction be preferred over batch?
6. Name four dimensions of consent authorization.
7. Why is `UNKNOWN` safer than `FAILED` after a remote timeout?
8. A score equals threshold .60. Under the lab policy, where does it route?
9. Give three controls against automation bias.
10. Internal system has 50,005 payments; network 50,000. What is the first response?

## 9. CURATED RESOURCES

1. [HL7 FHIR R4 Resource](https://hl7.org/fhir/R4/resource.html) — exact resource identity/version foundations.
2. [HL7 FHIR R4 Bundle](https://hl7.org/fhir/R4/bundle.html) and [HTTP transactions](https://hl7.org/fhir/R4/http.html) — normative batch/transaction structure and atomicity.
3. [ABDM Health Data Management Policy](https://abdm.gov.in/static/media/health_management_policy_bac9429a79.80f74bc3e039c00acd4f.pdf) — official consent, notice, rights and health-data governance context.
4. [NPCI UPI FAQs](https://www.npci.org.in/what-we-do/upi/faqs) — official customer-facing pending/reversal/grievance semantics.
5. [RBI Master Directions and Guidelines index](https://www.rbi.org.in/Scripts/BS_ViewMasterDirections.aspx) — current authoritative banking/digital-payment direction entry point; select by regulated entity/product/date.
6. **Martin Kleppmann, _Designing Data-Intensive Applications_, Chapters 7, 9 and 11** — transactions, consistency and stream-processing foundations.
7. **Chris Richardson, _Microservices Patterns_, Chapters 4 and 10** — sagas, transactional outbox and testing distributed workflows.
8. **Eric Evans, _Domain-Driven Design_, Chapters 4–6 and 14** — aggregates, value objects, bounded contexts and model integrity.
9. [WHO, _Ethics and Governance of Artificial Intelligence for Health_ (2021)](https://www.who.int/publications/i/item/9789240029200) — human autonomy, safety, transparency and accountability beyond model accuracy.
10. [NIST AI RMF 1.0](https://www.nist.gov/itl/ai-risk-management-framework) — Govern/Map/Measure/Manage evidence for consequential ML.

## 10. RELATED TOPICS BRIDGE

### Before

1. **Security, Privacy and Audit** — supplies authority, data handling and evidence.
2. **Transactions and Isolation** — supplies concurrency and atomic local updates.
3. **Messaging and Event Streaming** — supplies outbox, delivery and replay.
4. **ML Lifecycle** — supplies versioned evaluation and approval.

### After

1. **GPU Inference** — sizes specialized serving without weakening domain guardrails.
2. **Multitenancy and FinOps** — isolates customers and allocates shared platform cost.
3. **Incident Response** — handles data integrity, money mismatch and clinical-safety incidents.
4. **System Design Practice** — combines ledger/clinical store, workflows, models and human operations.

---ANSWER KEY BELOW---

1. 987,654 paise, with currency INR.
2. It detects reuse of the same key for a different amount/payee/operation rather than returning a misleading old result.
3. Net drain `100−70=30/h`; `900/30=30 hours` ideally.
4. Append a linked ₹400 correcting refund/reversal with balanced postings; never edit the settled entry.
5. When related resource changes must commit all-or-nothing to preserve clinical consistency.
6. Person, requester, data categories, purpose, time window/frequency—any four.
7. The remote side may have committed; FAILED can trigger a duplicate effect, while UNKNOWN drives status lookup/reconciliation.
8. HUMAN_REVIEW; the threshold comparison is inclusive.
9. Display evidence/limitations, require structured human reason, monitor overrides/outcomes, train reviewers, avoid misleading confidence—any three.
10. Do not edit totals. Match stable references, classify five missing/duplicate/late records, query authoritative status and create audited adjustments if warranted.
