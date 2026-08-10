# Incident Response and Post-Incident Learning

**Parent:** 06 — SRE and Observability  
**Target:** senior backend / AI-platform / MLOps engineering  
**Study time:** 3–4 hours plus the executable incident-record lab

## 1. FOUNDATIONS

An **event** is an observable occurrence. An **alert** is a notification that a defined condition needs evaluation. An **incident** is an unplanned event that degrades or threatens service, security, privacy, correctness or business operations and requires coordinated response. Not every alert is an incident, and a serious incident may begin with a support report rather than an alert.

Incident **resolution** restores acceptable operation or reaches a stable safe state. **Mitigation** reduces current impact without necessarily removing the underlying cause. **Remediation** changes the system to remove or reduce a contributing condition. A rollback can mitigate in five minutes while the true defect takes days to understand and fix. Waiting for root cause before mitigating leaves users exposed.

Incident response exists because cognition and communication degrade under pressure. Multiple engineers independently change production, stakeholders interrupt responders, theories become facts, and evidence disappears. Emergency services developed the Incident Command System to create clear command, roles and coordination. Google adapted this into incident management emphasizing three Cs: coordinate, communicate and maintain control.

The core roles are an **Incident Commander (IC)** who owns priorities, structure and decisions; an **Operations Lead** who coordinates technical diagnosis/mitigation; a **Communications Lead** who gives accurate internal/external updates; and a **Scribe** who maintains timeline, hypotheses, actions and decisions. One person may initially hold several roles, but a major incident should separate them. The most senior engineer need not be IC; technical expertise is often better used in operations.

**Severity** communicates impact and response expectations, not engineering difficulty or blame. A sample scheme: SEV-1 is widespread critical impact, safety/security/data-loss risk or existential business failure; SEV-2 is significant degraded function with workaround/limited scope; SEV-3 is localized nonurgent impact. Each organization must define exact triggers, paging, update cadence and authority before incidents.

Operational response broadly proceeds through preparation; detection/validation; declaration/triage; containment/mitigation; recovery/verification; closure; and learning. Security incident guidance such as NIST SP 800-61 Rev. 3 integrates preparation, detection, response and recovery into ongoing cybersecurity risk management rather than treating response as an isolated afterthought.

A **runbook** gives known operational steps for a symptom or component. A **playbook** coordinates a class of scenario such as credential compromise or regional outage. A **timeline** records observations and actions with timestamps/sources. A **postmortem** is the reviewed record of impact, timeline, contributing factors, response and corrective actions. “Blameless” means examining why actions were reasonable given the information, incentives and controls at the time; it does not mean avoiding accountability, rigor or misconduct investigation.

Without a practiced process, incident work becomes a chat room full of competing commands. Changes collide, customers receive contradictory messages, exhausted responders make irreversible moves, security evidence is overwritten and the same defect returns because follow-up actions are vague. The objective is controlled restoration of user outcomes and durable learning.

## 2. CORE MECHANICS

### 2.1 Preparation before the page

Maintain service ownership, escalation paths, severity policy, communication templates, dependency maps, SLO dashboards, safe access, break-glass procedure, runbooks and tested backups. The on-call must have current access but not standing unlimited privilege. Exercise through game days/tabletops and verify that alert, conferencing, status, ticket and credential systems remain available when the primary service/identity provider fails.

Every runbook should state trigger, preconditions, expected evidence, commands/tool versions, safety checks, rollback, verification and escalation. A command copied from a wiki is not safe merely because it once worked. Prefer automation with dry-run, scoped targets and audit. Keep an offline or independent incident-document path; do not depend solely on the failing product.

### 2.2 Detection and validation

An actionable page states user symptom, scope, threshold/window, current value, owner and initial dashboard/runbook. Acknowledge promptly, but validate using independent signals. Check whether the alert is stale, monitoring is broken or planned change explains it. Validation is not delay: when safety, privacy or active exploitation is plausible, declare/contain early while facts develop.

Establish initial facts: when impact began; affected journeys/regions/tenants; what remains healthy; SLO/budget burn; recent changes; security/data indicators; and whether the response tools work. Distinguish observation (“403 rose from 0.05% to 4.1% at 09:58”) from hypothesis (“OIDC rollout caused it”).

### 2.3 Declare early and choose severity

Declaration summons structure and creates one source of truth; it is not admission of failure. Declare when impact/severity thresholds are met, coordination spans teams, risk is uncertain but potentially high, or one responder cannot safely manage. Set incident ID, severity, IC, channel/bridge, state document and next update time.

Severity can change. Upgrade on wider impact, safety/security/data evidence, increasing burn or failed mitigation. Downgrade only when evidence supports reduced impact and response load. Do not lower severity to improve metrics. Record the reason/time.

### 2.4 Command and roles

The IC sets objectives such as “stop unauthorized responses, preserve evidence, restore authorized reads.” They assign operations, communications and specialist leads, control risky changes, track responder fatigue, resolve conflicting priorities and request escalation. The IC should avoid becoming absorbed in shell debugging.

Operations uses hypothesis-driven work and reports results. Communications reports verified facts and explicitly labels unknowns. The scribe records timestamped impact, hypotheses, decisions, commands/change IDs, owners and outcomes. Legal/privacy/security/support/vendor liaisons join based on scope but do not create competing command trees.

A handoff is explicit: incoming IC receives current impact, objectives, mitigations, risks, hypotheses, pending decisions, roles and next update; both acknowledge transfer; the channel/document announces it. Silent shift changes create command ambiguity.

### 2.5 Stabilize and control changes

Stop unrelated production changes when they complicate diagnosis or add risk. Inventory in-flight deployments/config jobs and preserve their IDs. Establish one change queue: proposal, expected effect, risk/blast radius, precheck, owner, approver, start/end, observation and rollback trigger. Two “safe” changes at once destroy causal evidence and can interact.

Prefer the smallest reversible mitigation: disable a feature flag, stop rollout, route around a failed region, shed noncritical load, revoke compromised identity, scale a known bottleneck. But “rollback first” is not universal. A rollback may be incompatible with migrated schema, re-enable vulnerability or destroy forensic state. Perform a quick safety check and define verification.

### 2.6 Hypothesis-driven troubleshooting

Form a falsifiable hypothesis tied to evidence: “Change CHG-8421 altered West India federated credential claims, so only that region gets authorization 403.” Predict what else should be true: start aligns with rollout, East India unaffected, token audience/subject mismatch visible, rollback should recover. Run the cheapest/safest discriminating query or experiment. Record result and update confidence.

Do not randomly restart everything. A restart erases memory/queues and temporarily masks leaks. Use binary narrowing across time, region, version, route, dependency and identity. Compare known-good versus bad cohorts. Inspect SLO symptom first, then correlated traces/logs/config changes and saturation. Assign parallel workstreams only when independent and coordinated.

### 2.7 Containment: operational and security

Operational containment reduces user impact: traffic shift, capacity, feature disable, degradation or admission control. Security containment also prevents adversary movement/exfiltration: revoke tokens/keys, isolate workloads/subnets, block indicators, preserve affected instances, disable vulnerable integration. The fastest operational fix—restarting compromised hosts—may destroy volatile evidence; coordinate with security/forensics.

Containment has side effects. Revoking one shared identity may take down healthy services. Network isolation can stop clinical access. Decide using explicit risk, scope and fallback; use least-blast controls and continuously verify both harm reduction and critical-service continuity.

### 2.8 Evidence preservation and chain of custody

For ordinary outages, preserve dashboards/query snapshots, trace/log references, deployment/config versions, command output and timeline. For suspected security/privacy incidents, follow legal/security evidence procedures: record collector, timestamp/time zone, source, method, hash, storage, transfers and access. Prefer snapshots/images and write-protected copies where required. Do not copy regulated data into broad chat or postmortem documents.

Clock synchronization matters. Keep source timestamps and note skew rather than “fixing” evidence. Hash proves bytes did not change after capture, not that the source was truthful. Access-controlled audit storage may require different durability/retention from diagnostic telemetry.

### 2.9 Communications

Internal updates answer: current impact, known facts, actions/owners, risks/unknowns, next update time. External updates describe user impact and action without speculation, secrets, blame or unsupported recovery estimates. Use absolute timestamps and consistent timezone. Say “next update by 10:30 UTC” even if nothing changes.

The lab enforces at most 15 minutes between updates for its sample SEV-1. That is a scenario policy, not a universal standard. Communication frequency should reflect severity, stakeholder needs and responder capacity. Communications Lead shields technical responders from repeated inquiries and coordinates support/legal/regulatory statements.

Never disclose patient/account details, internal credentials, exploitable paths or unconfirmed attribution. Regulatory and contractual notification clocks vary by jurisdiction and incident facts; involve privacy/legal/security immediately rather than relying on an engineer's remembered deadline.

### 2.10 Recovery and verification

Mitigation is not recovery. Define exit criteria before acting: user success/latency and burn normal for N consecutive windows, queues draining, correctness/audit invariants pass, capacity/headroom stable, no continuing adversary indicators, and synthetics/critical journeys succeed from affected locations. Verify from user/edge and independent audit—not only the changed component's health endpoint.

Restore gradually: canary traffic, bounded cohorts, monitored step-up. Watch for delayed backlog, retry storm, cache warm-up, data reconciliation and recurrence. If data may be missing/duplicated/corrupt, stop normal closure until reconciliation defines authoritative state and compensations. Recovery includes credential rotation, clean rebuild and persistence removal for security events.

### 2.11 Closure and residual risk

The IC closes only after impact ended, recovery criteria met, monitoring stable, ownership returns to normal, stakeholders receive final operational update, evidence is preserved and follow-up/postmortem owner is assigned. Record unresolved risks and temporary controls with expiry. “No alerts for five minutes” is insufficient.

Distinguish impact start/end, detection, declaration, mitigation and resolution. **MTTD** may mean mean time to detect, **MTTA** acknowledge, **MTTM** mitigate and **MTTR** repair/restore/resolve—define the R. Averages hide distributions and severe outliers; report percentiles and phase durations while avoiding incentives to under-declare/close early.

### 2.12 Timeline and incident document

Keep summary/state/impact/roles/next update at top. Timeline entries use UTC timestamps, actor/source, observation/action, result and links. Preserve original statements and add corrections rather than rewriting history. Track hypotheses as proposed/supported/rejected and decisions with rationale.

The sample runs 09:58–10:43 impact: 45 minutes, detects/declares at 10:04 (six minutes), begins rollback at 10:24, observes recovery at 10:34, confirms audit isolation at 10:44 and resolves at 10:49. It reports 7,812 failed among 182,440 valid requests, `4.282%` failed. Against a 99.9% objective, this interval's point burn is roughly `42.82×`, though full SLO consumption needs window traffic.

### 2.13 Postmortem structure

Trigger criteria may include user impact above threshold, data loss, security/privacy event, manual intervention, extended resolution or monitoring failure. The postmortem states executive summary, measurable impact, detection/response, timeline, contributing factors, what went well/poorly/luck, causal analysis, and prioritized actions. Review and publish to the broadest appropriate audience without user-sensitive evidence.

Avoid “root cause: engineer deployed bad config.” Ask why the change was allowed: ambiguous claim semantics, missing negative region test, review tooling hid effective diff, no canary, rollback slow, alert lacked region. Complex incidents have interacting contributing conditions; one root may be misleading.

Blameless language describes context: “The responder used the documented rollback, which omitted identity cache invalidation,” not “the responder forgot.” Accountability means owners complete improvements and leaders fix incentives/process, not punishment for reasonable action. Deliberate policy violations can use a separate fair HR/security process without corrupting technical learning.

### 2.14 Corrective actions that work

An action is specific, owned, due, prioritized and verifiable. “Improve monitoring” is not an action. “Claims team adds regional authorization bad-ratio recording rule and stages a wrong-region federation exercise; alert fires within ten minutes; due Aug 18” is. Include immediate containment cleanup, prevention, detection, mitigation speed and systemic actions.

Track action state to completion and verify effect. Prevent a graveyard of P0 tasks by limiting high-priority actions to causal leverage, funding them and escalating overdue risk. Search past incidents for recurring themes such as credential scope, schema rollout or DNS; organizational trend analysis is often more valuable than polishing one document.

### 2.15 On-call health and humane operations

Pages must be actionable and sustainable. Define secondary escalation, rotate long incidents, enforce breaks and handoffs, and provide psychological safety/support. Exhaustion increases error. An individual handling a multi-team SEV-1 alone is a process failure, not heroism.

Measure page volume, night interruptions, false/actionable ratio and post-incident load. Automate toil, eliminate noisy alerts and staff for expected operations. After a traumatic security/safety incident, provide support and delay blame-laden performance judgments.

### 2.16 Healthcare, fintech and AI specifics

Healthcare incidents may involve availability, integrity, confidentiality, patient-safety workflows and reportable privacy breach. Fintech incidents add duplicate/incorrect transactions, reconciliation, market/payment deadlines and fraud. Correctness cannot be hidden inside availability percentage. Preserve immutable transaction/audit evidence and coordinate legal/compliance.

AI platform incidents include wrong model/version, data leakage, model quality/drift, unsafe output, training-data contamination, GPU capacity and lineage failure. Stop or roll back a model by immutable digest, preserve evaluation/input lineage without copying sensitive prompts, and verify tenant/model routing. A healthy Kubernetes deployment can still serve the wrong model, so runtime and model-quality incident criteria must meet.

## 3. WORKED PROBLEMS

### Problem 1 — Declare and assign roles

**Statement.** At 10:04, one region has 4.1% authorization failures after a rollout; three teams are debugging in chat with no owner. What do you do?

**Solution.** Declare the severity dictated by regional critical journey/burn and potential security ambiguity. Name IC, Ops, Comms and scribe; open incident record/bridge; freeze unrelated change; state impact/known facts; assign rollout comparison/identity evidence workstreams; set next update within policy. Do not wait for root cause.

**Mistake caught:** treating declaration as requiring certainty.

### Problem 2 — Calculate incident facts

**Statement.** The sample has 7,812 failures among 182,440 requests from 09:58–10:43. Compute failure, success and point burn for 99.9%.

**Solution.** Failure `7,812/182,440≈4.282%`; success ≈95.718%. Allowed failure 0.1%, so point burn ≈42.82×. Impact duration 45 minutes. Do not claim entire monthly budget use without full-window counts.

**Mistake caught:** confusing interval burn with full-window consumption.

### Problem 3 — Safe change queue

**Statement.** One engineer wants restart, another scale, another rollback identity config simultaneously.

**Solution.** IC/Ops serializes by discriminating value and risk. Evidence aligns with identity rollout/region, so propose bounded rollback with precheck (schema/credential compatibility), expected effect, owner, observation window and abort. Hold restart/scale unless saturation evidence supports them. Record result before next change.

**Mistake caught:** parallel changes that erase causality and interact.

### Problem 4 — Security containment conflict

**Statement.** A shared secret may be stolen, but immediate revocation disconnects a hospital integration.

**Solution.** Declare security/privacy escalation; map use and exposure; establish alternate credential/path; restrict network/source/scope if it safely reduces exposure; rotate/revoke urgently with hospital/comms/legal coordination; monitor misuse and critical service. Preserve evidence before destructive rebuild where feasible. Risk ownership is explicit—not silent delay.

**Mistake caught:** treating containment as impact-free or waiting indefinitely.

### Problem 5 — Verify recovery

**Statement.** Pod health is green five minutes after rollback. Can IC resolve?

**Solution.** No. Verify edge user success and burn across defined windows, affected region/tenants, synthetics, authorization/cross-tenant audit invariant, queues/retries, capacity and recurrence. Preserve evidence and assign postmortem. Only then close with residual risks documented.

**Mistake caught:** component health equals user recovery.

### Problem 6 — Handoff

**Statement.** IC has worked four hours and leaves a message: “Seattle has it.” Evaluate.

**Solution.** Unsafe. Conduct live briefing; transfer impact/state/objectives, mitigations, hypotheses, risks, roles, changes and next update. Incoming IC explicitly accepts; outgoing IC announces handoff and stays until acknowledgment. Rotate Ops/Comms as needed.

**Mistake caught:** asynchronous assumption of command transfer.

### Problem 7 — Postmortem causal analysis

**Statement.** Draft says “Root cause: developer used wrong region.” Improve it.

**Solution.** Describe the config/claim mismatch and conditions: region field ambiguous; generated diff did not show effective subject; tests covered correct claims only; rollout lacked regional canary; alert aggregated regions; rollback instructions omitted cache. Explain why action was locally reasonable and create controls at multiple layers.

**Mistake caught:** stopping causal analysis at the nearest human.

### Problem 8 — Evidence handling

**Statement.** Suspected data exfiltration; responder pastes raw access logs with patient IDs into public incident chat.

**Solution.** Stop further disclosure, involve security/privacy/legal, restrict/delete under approved evidence-preserving process, assess secondary breach and rotate exposed credentials if any. Collect original evidence into authorized immutable storage with source/time/hash/custody; share redacted aggregates/references in incident doc.

**Mistake caught:** confusing collaboration convenience with evidence/privacy governance.

### Problem 9 — Action quality

**Statement.** Action items are “be careful,” “improve tests,” and “watch dashboard.” Rewrite one.

**Solution.** “Identity team, by 2026-08-16, adds CI negative test deploying a West India token against East India-only federated subject and proves Azure exchange is denied; pipeline artifact/result linked; control owner reviews quarterly.” It has owner, date, exact control and verification.

**Mistake caught:** nonverifiable learning theater.

## 4. REAL-WORLD / APPLIED CONTEXT

Google's SRE Workbook incident-response chapter documents Incident Command System-derived roles and the three Cs, including cases where early declaration and formal roles improved complex response. Its example PagerDuty case rotated responders/IC about every four hours during a long NTP incident and required service-owner validation before closure.

NIST SP 800-61 Rev. 3 (April 2025) supersedes Rev. 2 and integrates cybersecurity incident response throughout CSF 2.0 risk management. Security response is not simply SRE outage handling with a different label: evidence, adversary containment, legal/privacy notification and eradication need specialized authority.

The included incident JSON contains a 45-minute impact, six updates no more than ten minutes apart, four named roles, three evidence links and two owned/verifiable actions. Its validator/reference command and six unit tests passed. It is a structural teaching control—not proof that a narrative is truthful, a substitute for legal review or a complete incident-management platform.

## 5. COMPARISON TABLE

| Concept | Primary goal | Ends when | Common confusion |
|---|---|---|---|
| Mitigation | reduce current user/risk impact | impact controlled | assumed to remove defect |
| Resolution/recovery | restore verified acceptable operation | exit criteria met | pod green treated as enough |
| Remediation | reduce recurrence/contributing condition | verified fix/control delivered | promised action treated as complete |
| Containment | limit spread/harm | threat/impact boundary controlled | may conflict with availability/evidence |

| Role | Owns | Must avoid |
|---|---|---|
| Incident Commander | priorities, roles, control, decisions | deep solo debugging |
| Operations Lead | technical workstreams/mitigation | uncoordinated changes |
| Communications Lead | timed accurate stakeholder updates | speculation/unsupported ETA |
| Scribe | live facts/timeline/decisions | rewriting inconvenient history |
| Security/privacy/legal liaison | adversary, evidence, obligations | parallel command ambiguity |

## 6. COMMON MISTAKES & MISCONCEPTIONS

1. **Wait for certainty before declaring.** Declaration provides structure for uncertainty.
2. **Severity means complexity.** It represents impact/risk and response need.
3. **Most senior person must command.** Best coordinator commands; experts investigate.
4. **IC debugs deeply.** They lose situational control. Delegate Ops.
5. **Everyone changes production.** Use one logged change queue and approval.
6. **Restart first.** It destroys evidence/masks state and may worsen impact.
7. **Rollback is always safe.** Schema/security/state may be incompatible. Precheck and verify.
8. **Root cause before mitigation.** Stop harm with reversible evidence-based action first.
9. **Hypothesis stated as fact.** Label and test predictions.
10. **Silence means progress.** Stakeholders need timed updates even with no change.
11. **Give optimistic ETA.** Communicate facts/actions/next update, not invented recovery.
12. **Raw sensitive data in chat.** Use restricted evidence store and redacted references.
13. **Hash proves original truth.** It only supports integrity after capture.
14. **Operational response equals security response.** Adversary/evidence/legal needs differ.
15. **Pod healthy means recovered.** Verify user SLI, data/audit invariants and backlog.
16. **No page means no incident.** Monitoring can fail; support/security may detect first.
17. **Close to reduce MTTR.** Premature closure games metrics and risks recurrence.
18. **MTTR is universally defined.** State whether restore, repair, resolve, etc.
19. **Average incident time is enough.** Use percentiles/phases and severe outliers.
20. **Blameless means no accountability.** It enables honest learning; actions still have owners.
21. **Human error is root cause.** Investigate controls, context, incentives and latent conditions.
22. **Postmortem document equals learning.** Reviewed, funded, verified actions create change.
23. **“Improve monitoring” is an action.** Specify signal/query/test/owner/due/verifier.
24. **Heroes are healthy response.** Rotation, escalation and sustainable on-call reduce risk.

## 7. CHEAT SHEET — REVIEW ONLY, NOT A SUBSTITUTE FOR THE SECTIONS ABOVE

`prepare → detect/validate → declare/triage → contain/mitigate → recover/verify → close → learn/verify actions`

- Declare early; incident ID, severity, IC, channel/doc, next update.
- IC coordinates; Ops investigates/changes; Comms updates; scribe records.
- Facts ≠ hypotheses. Hypothesis → prediction → discriminating test → result.
- One change queue: expected effect, risk, owner, approver, rollback, observation.
- Mitigation reduces impact; resolution restores verified state; remediation prevents/reduces recurrence.
- Security: contain adversary, preserve custody, involve security/privacy/legal early.
- Updates: impact, facts, action/owner, unknown/risk, next time—no secret/PII/speculative ETA.
- Recovery: user SLI + critical segments + correctness/audit + queues/capacity + recurrence window.
- Handoff is live, explicit and acknowledged.
- Postmortem: impact, timeline, contributing factors, response, learning, owned/due/verifiable actions.

## 8. PRACTICE SET FOR SELF-TEST

1. Write declaration and first 15-minute plan for 8% payment timeouts in one region after a database migration.
2. Calculate impact duration, failure ratio and 99.95% point burn for 24,000 failures among 1.2 million requests over 32 minutes.
3. Prioritize rollback, traffic shift, scale and restart hypotheses for a release-correlated CPU/latency incident; define safe tests.
4. Draft three internal and two external updates for a 45-minute incident without speculative ETA or sensitive details.
5. Design a live IC handoff checklist for a cross-time-zone, eight-hour incident.
6. Create containment/recovery plan for a leaked Azure deployment credential used by a critical healthcare service.
7. Convert “operator deleted wrong database” into a five-layer contributing-factor analysis and actions.
8. Define recovery gates for Kafka consumer corruption and backlog after a bad schema release.
9. Create an evidence manifest/chain-of-custody outline for suspected model artifact tampering.
10. Write five specific actions spanning prevention, detection, mitigation speed, process and verification for the sample identity incident.

## 9. CURATED RESOURCES

1. Betsy Beyer et al., *Site Reliability Engineering*, Chapter 14, [“Managing Incidents”](https://sre.google/sre-book/managing-incidents/). Command, state documents, handoffs and coordinated response.
2. Betsy Beyer et al., *The Site Reliability Workbook*, Chapter 9, [“Incident Response”](https://sre.google/workbook/incident-response/). ICS/three-Cs roles and detailed Google/PagerDuty cases.
3. Betsy Beyer et al., *Site Reliability Engineering*, Chapter 15, [“Postmortem Culture”](https://sre.google/sre-book/postmortem-culture/). Trigger criteria, blameless writing, review and organizational learning.
4. Google SRE Book, Appendix C, *Example Incident State Document*, and Appendix D, *Example Postmortem*. Concrete living-document and final-analysis structures.
5. NIST SP 800-61 Rev. 3, *Incident Response Recommendations and Considerations for Cybersecurity Risk Management* (Nelson, Rekhi, Souppaya, Scarfone, April 2025). Current CSF 2.0-integrated security response guidance.
6. CISA, *Federal Government Cybersecurity Incident and Vulnerability Response Playbooks*. Concrete preparation/detection/coordination/containment steps for cyber scenarios; adapt authority to your organization.
7. RFC 2350, *Expectations for Computer Security Incident Response*. Canonical CSIRT service/communication expectations.
8. John Allspaw, *The Infinite Hows* and Sidney Dekker, *The Field Guide to Understanding Human Error*. Systems-oriented learning that avoids stopping at operator blame.
9. PagerDuty, *Incident Response Documentation*. Public role/process templates and practical response mechanics, checked against your organization's policy.

## 10. RELATED TOPICS BRIDGE

### Before

1. **SLIs, SLOs and Error Budgets:** quantifies impact/burn and determines urgency/recovery.
2. **Metrics, Logs and Traces:** detects symptoms, tests hypotheses and preserves operational evidence.
3. **CI/CD Supply Chain:** change/provenance makes release correlation and rollback trustworthy.
4. **Distributed Systems:** partial failure, retries, ordering and consistency shape incident behavior.

### After

1. **Capacity and Disaster Recovery:** provides failover/restoration drills and measurable RTO/RPO.
2. **MLOps Monitoring:** adds model/data incidents and immutable lineage/recovery.
3. **Regulated System Design:** defines breach/safety notification, evidence, access and retention duties.
4. **Behavioral Interview Narrative:** incident leadership becomes evidence through precise situation/actions/outcomes/learning.

---ANSWER KEY BELOW---

1. Declare appropriate high severity; IC/Ops/Comms/scribe; state 8% regional payment timeout, start/change correlation and unknown correctness; freeze unrelated releases. First 15 minutes: verify edge/SLO and transaction correctness/duplicates, stop migration/rollout safely, compare unaffected region/schema compatibility, prepare route shift/rollback with capacity/data prechecks, involve DB/payment owners and set next update.
2. Failure ratio `24,000/1,200,000=2%`; success 98%. Allowed failure for 99.95% is 0.05%, so point burn `2/.05=40×`. Duration is 32 minutes; full-window budget consumption needs the SLO-window denominator, not just this interval.
3. Confirm release/time/cohort and saturation. Stop rollout first if reversible. Traffic shift only after destination capacity/data-consistency check. Rollback after schema/config/security compatibility check with canary. Scale if CPU/useful throughput evidence says capacity, not if retry/lock collapse. Restart last when a specific state/leak hypothesis and evidence preservation support it. Serialize and observe each.
4. Internal examples at declaration/15/30 minutes state measured region/journey impact, facts versus hypotheses, current owner/action/risk and exact next time. External examples say some regional payment attempts are delayed/failing, team is mitigating, customers should avoid duplicate retries unless instructed, and next update time; later report recovery monitoring. No root-cause claim, names, credential/schema detail or invented ETA.
5. Checklist: current severity/impact/start and SLO; safety/security/data status; objectives/exit gates; roles/contacts; changes/mitigations/results; active/rejected hypotheses/evidence links; risks/temporary controls; pending decisions/workstreams/owners; stakeholder status/next update; responder fatigue/access. Incoming says “I accept IC,” outgoing confirms in bridge and document/channel.
6. Declare security/privacy incident, map secret scope/use/log exposure, preserve identity/cloud audit, restrict/revoke federation/secret with least-disruptive replacement path, isolate suspicious principals/workloads, rotate dependent credentials, monitor activity and patient-access continuity, involve privacy/legal/comms, clean rebuild if compromise, reconcile unauthorized access, verify new identity and audit, then satisfy notification/evidence policy.
7. Analyze misleading naming/default target, destructive command UX, overbroad credential, missing production confirmation/two-person control, backup/restore readiness, alert delay and fatigue/pressure. Actions: resource lock/deny, scoped identity, typed tooling requiring immutable resource ID/environment and dry-run, peer approval, tested point-in-time restore, destructive audit alert and runbook/game day—each owned/due/tested.
8. Stop bad producers/consumers and preserve offsets/schema/artifacts; protect sink from further corruption; identify last-known-good boundary; deploy compatible code/schema; restore/reconcile authoritative records and quarantine poison; replay idempotently with rate limits so sinks remain healthy; verify counts/checksums/per-key ordering, lag-age drain, duplicates and user correctness; resume staged and monitor recurrence.
9. Manifest includes incident/evidence ID, collector/authority, UTC capture time/time source, source URI/system/region, acquisition command/tool/version/read-only method, original size and SHA-256, encryption/storage/access classification, custody transfers with from/to/time/purpose/signature, analysis copies/hashes, retention/legal hold and final disposition. Hash integrity does not prove source truth.
10. Examples: CI negative regional claim test; typed federation generator with reviewed effective subject; regional 403 SLI/multi-window page; canary identity exchange/read test before traffic; one-command scoped rollback plus cache-invalidation verification. Each names team owner, due date, linked ticket, expected artifact/test and independent closure reviewer.
