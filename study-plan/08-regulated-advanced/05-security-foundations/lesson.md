# Security Foundations from Scratch

Parent subject: `08-regulated-advanced`
Study time: 3–4 hours
Target: senior backend / AI platform / MLOps interviews

## 1. FOUNDATIONS

### Security is risk management, not a feature checkbox

Information security protects systems and information from unacceptable harm. It is not absolute; organizations identify assets, threats, vulnerabilities, likelihood, impact, and controls, then accept, avoid, transfer, or reduce residual risk. “Use encryption” is not a security design until keys, identities, endpoints, algorithms, rotation, recovery, and threats are specified.

Security must be designed across people, process, technology, suppliers, and lifecycle. A perfectly encrypted database can be exposed by an overprivileged API, stolen admin session, public backup, vulnerable dependency, malicious insider, or incorrect deletion workflow.

### Assets, actors, threats, vulnerabilities, and controls

An **asset** is something valuable: patient data, money, model weights, source, credentials, availability, reputation. A **threat actor** can be external attacker, insider, compromised workload, supplier, bot, or accident. A **threat** is a potential cause of harm. A **vulnerability** is weakness exploitable by a threat. **Exposure** is reachable condition. A **control** changes likelihood/impact/detection/recovery.

Controls may be preventive (least privilege), detective (audit anomaly), corrective (credential rotation), deterrent, compensating, or recovery. **Defense in depth** uses independent layers so one failure does not expose the asset. Redundant controls sharing one identity/config are less independent than they look.

### CIA and additional properties

The CIA triad:

- **Confidentiality:** only authorized disclosure.
- **Integrity:** protected from unauthorized/improper change; correctness/provenance.
- **Availability:** accessible to authorized users when required.

Also authenticity (identity/data genuine), accountability (actions attributable), non-repudiation under defined evidence, privacy, safety, and resilience. In healthcare, integrity/availability can be life-critical; in payments, ledger integrity and non-duplication matter.

### Threat modeling

Threat modeling asks what are we building, what can go wrong, what controls, and whether evidence is sufficient. Draw trust boundaries and data flows. STRIDE categories: Spoofing, Tampering, Repudiation, Information disclosure, Denial of service, Elevation of privilege. It is a prompt, not completeness proof.

For a model inference API: Internet client→gateway→service→feature store/model registry/logs. Threats include stolen token, cross-tenant IDOR, prompt injection/tool abuse, model artifact tampering, sensitive logs, dependency DoS, and poisoned features.

### Identity, authentication, and authorization

An **identity** represents a human/workload/device. **Authentication** verifies claimed identity. **Authorization** decides an action on resource under context. **Accounting/audit** records. Never conflate authenticated with allowed.

Factors: knowledge (password), possession (security key/device), inherence (biometric). MFA combines independent factors; SMS is weaker than phishing-resistant FIDO2/WebAuthn. Passwords should be salted and hashed with adaptive memory-hard function such as Argon2id under current policy, never encrypted/reversibly stored.

Sessions/tokens have issuer, subject, audience, scopes/claims, issue/expiry, signature, and revocation/session state. Validate algorithm, signature, issuer, audience, time, nonce/state where applicable. Decode is not validate. Keep access tokens short-lived, protect refresh tokens, prevent logs/URLs.

Authorization models: RBAC roles, ABAC attributes/context, ReBAC relationships, ACLs, policy engines. Enforce server-side at every object/action. **IDOR/BOLA** occurs when changing `/patients/P2` bypasses object authorization. Tenant ID from user input must match authoritative identity/policy, not become trust.

### Least privilege and zero trust

Grant minimum actions/resources/duration/conditions. Human admin uses federation, MFA, JIT elevation; workloads use managed identity; services have separate roles; break-glass is protected/tested/audited. Zero trust means no implicit trust from network location; continuously verify identity/device/workload and minimize access.

### Cryptography basics

**Encryption** protects confidentiality with a key. Symmetric algorithms such as AES use same secret for encrypt/decrypt and are efficient. Asymmetric algorithms use public/private keys for encryption/key agreement/signatures. Hybrid protocols establish symmetric session keys using asymmetric authentication/key exchange.

Encryption must be authenticated: AEAD modes such as AES-GCM or ChaCha20-Poly1305 provide confidentiality and integrity with nonce requirements. Reusing a GCM nonce with same key can catastrophically break security. Never invent crypto or use AES-ECB.

A cryptographic **hash** maps arbitrary data to fixed digest with preimage/collision resistance goals; no secret key. HMAC authenticates with shared secret. Digital signature uses private signing key and public verification, providing integrity/authenticity under key trust. Encoding/base64 is not encryption.

Keys need generation from secure randomness, storage in KMS/HSM/secret manager, access policy, version, rotation, backup/recovery, revocation/destruction, and audit. Envelope encryption uses a data-encryption key per object/batch protected by a key-encryption key in KMS, reducing exposure and enabling key management.

### Network and transport security

TLS authenticates endpoint and protects data in transit when certificate/hostname verification is correct. mTLS authenticates both peers but authorization remains. Private networks reduce exposure, not replace identity. Firewalls/NSGs constrain reachability; WAF handles some web patterns; DDoS controls protect capacity.

Segment production, management, build, and tenant/data boundaries. Control egress to limit exfiltration. DNS, certificate, proxy headers, and service mesh identities are security dependencies.

### Application security

Treat all external data as untrusted. Validate type, length, range, format, encoding, nesting, and business relation at boundary. Use parameterized SQL; safe templating/contextual output encoding; CSRF defenses for cookie-authenticated state changes; secure cookies; CORS is browser policy, not API authorization.

Prevent SSRF by not accepting arbitrary URLs; allow destinations/schemes, resolve/validate addresses including redirects and DNS rebinding, isolate metadata endpoints, enforce egress. File uploads need type/content/size/name/storage/scanning and separate serving domain. Deserialization of pickle/Java native objects from untrusted sources can execute code.

### Secure development and supply chain

Use reviewed source, branch protection, CI identity, pinned/verified dependencies, SAST/DAST/dependency/container/IaC scans, secret scanning, SBOM, signed provenance, immutable artifacts, and admission policy. Scanners produce false positives/negatives; triage based on reachability/exploitability/impact and remediation deadlines.

Build systems are privileged: they access source, signing, registries, cloud. Isolate untrusted pull requests, use short-lived OIDC credentials, protect caches/artifacts from poisoning, and never expose secrets to forked code.

### Vulnerability and incident basics

A vulnerability has affected versions, conditions, severity, exploitability, and fix/mitigation. CVSS is a standardized severity score, not business risk. Inventory and asset criticality are needed to know exposure. Patch with tests/staged rollout; use compensating controls only with expiry/owner.

Security incidents require containment while preserving evidence: compromised credential rotation, session revocation, isolate workload, block indicators, preserve logs/images according to legal process, assess data/action scope, notify required stakeholders, eradicate/recover, monitor, learn. Do not destroy evidence with ad-hoc cleanup.

## 2. CORE MECHANICS

### 2.1 Threat-model a payment endpoint

Asset: account funds, ledger, PII, availability, credentials. Entry: mobile/web client through gateway. Boundaries: Internet, identity provider, API, DB, payment processor, event broker.

STRIDE:

- spoofing: stolen token→phishing-resistant MFA/session controls;
- tampering: amount/beneficiary→server validation, signed TLS, ledger invariants;
- repudiation: deny transfer→immutable audit with identity/idempotency/outcome;
- disclosure: logs/PAN→tokenization, minimization, redaction/access;
- DoS: retry/flood→rate/admission/bulkhead;
- elevation: object ID swap/admin claim→resource authorization and claim validation.

Document residual risks and tests, not just diagram.

### 2.2 Password storage

On registration, generate per-password salt automatically through vetted Argon2id library; configure memory/time/parallelism from current OWASP guidance and benchmark server. Store algorithm/version/parameters/salt/hash. On login, constant-time library verify; rate-limit/risk detect; rehash on success if parameters obsolete. A pepper in secret manager can add control but complicates rotation/recovery.

Never SHA-256(password+salt): general hashes are too fast, enabling billions of guesses.

### 2.3 Token validation

For JWT: allow expected algorithms, fetch/cache trusted issuer keys securely, verify signature, exact issuer, audience, expiry/not-before with bounded clock skew, token type, and required claims. Then authorize action/resource. Reject `alg=none`, algorithm confusion, arbitrary JWK URL, and token meant for another API.

Token revocation before expiry may use short lifetime, session store, key/subject invalidation, introspection, or denylist depending architecture.

### 2.4 Authorization matrix

Actions rows: read patient, update consent, submit claim, export cohort. Roles/attributes columns: patient self, clinician with active care relationship/purpose, billing agent, researcher with approved dataset, admin. Define resource tenant, relationship, consent/purpose, emergency override, time/location/device. Test allow and deny, cross-tenant IDs, stale relationships, missing attributes, bulk/list endpoints.

Default deny. Admin is not automatic access to clinical content; separate platform operation from data access.

### 2.5 Parameterized SQL

Bad: `"SELECT * FROM patient WHERE id='"+id+"'"`. Good driver placeholder and bound value. Parameters protect values, not dynamic identifiers/order; map allowed external enum to fixed identifiers. DB role should only access needed schema/actions, and row-level/tenant constraints add depth.

### 2.6 Encrypt data

For object: generate random 256-bit data key; random unique nonce per encryption; AES-GCM encrypt plaintext with associated data containing tenant/object/version; KMS wraps data key; store ciphertext, nonce, wrapped key, algorithm/version, AAD identifiers. On read authorize first, unwrap through KMS, verify tag/AAD. Rotate KEK by rewrapping DEKs; rotate DEK by re-encrypting data.

Do not log plaintext/key; prevent nonce reuse; define deletion of keys/ciphertext and backup behavior.

### 2.7 Secret rotation

Issue new credential, deploy consumers able to use new while old valid, verify, revoke old, monitor. For DB passwords, pools hold old sessions; plan connection refresh. For signing keys, publish both public verification keys during overlap and use key IDs. Emergency compromise shortens overlap and prioritizes revocation/containment.

### 2.8 Rate limit and abuse

Token bucket capacity B and refill r permits burst B then sustained r. At B=100,r=20/s, an idle client can send100 immediately then20/s. Key by authenticated tenant/user/action, plus IP/device signals; global and per-tenant bounds. Return 429 with safe retry guidance. Distributed counters trade precision/availability; critical financial limits belong to authoritative transactional rules, not only cache limiter.

### 2.9 Security logging

Record authentication success/failure category, authorization decision/policy version, admin action, key/secret access, deployment, data export, break-glass, and security-control change. Include time, actor/workload, target, action, result, source context, trace, reason; exclude credentials/full sensitive payload. Protect integrity, restricted access, retention, time sync, alerting.

### 2.10 Vulnerability response

Identify affected component/version/location from SBOM/inventory; confirm reachability/config/exposure; classify data/business; apply patch or tested mitigation; stage with rollback; hunt exploitation indicators; verify scanner/version; document exception/expiry if deferred. “CVSS 10 means shut everything now” and “not exploited publicly means ignore” are both inadequate.

## 3. WORKED PROBLEMS

### Problem 1 — Hash or encryption (easy)

Store password for verification later.

**Solution.** Adaptive salted password hash (Argon2id), not encryption; server need not recover password.

**Trap:** AES-encrypt passwords.

### Problem 2 — Authentication versus authorization (easy)

Valid clinician token requests unrelated patient's record.

**Solution.** Authenticated but unauthorized absent relationship/purpose/consent/override. Deny and audit safely.

**Trap:** valid token grants all patient access.

### Problem 3 — Encoding (easy)

Is base64 protection?

**Solution.** No; reversible encoding without secret. It transports bytes.

**Trap:** base64 API keys called encrypted.

### Problem 4 — JWT audience (medium)

Token validly signed for billing API used at clinical API.

**Solution.** Reject audience/type mismatch. Signature only proves issuer/key, not intended recipient/action.

**Trap:** validate signature/expiry only.

### Problem 5 — IDOR (medium)

User changes claim ID in URL and sees another tenant.

**Solution.** Missing object/tenant authorization. Scope query by authoritative tenant and permission; opaque IDs are not control; add tests/log detection.

**Trap:** making IDs harder to guess only.

### Problem 6 — GCM nonce (medium)

Same key and nonce reused for two messages.

**Solution.** Catastrophic confidentiality/integrity risk; ensure unique nonce generation/counter and key lifecycle. Rotate/assess affected data.

**Trap:** nonce treated as secret/password.

### Problem 7 — SSRF (hard)

Webhook tester fetches user URL and can reach `169.254.169.254`.

**Solution.** SSRF to metadata. Allowlist destinations/schemes, resolve and reject private/link-local/loopback across redirects/rebinding, egress firewall/proxy, workload identity hardening, response size/time limits.

**Trap:** regex rejecting literal IP only.

### Problem 8 — Build secret (hard)

Fork PR CI receives cloud deploy credential.

**Solution.** Untrusted code can exfiltrate it. Separate workflows, no secrets/privileged OIDC for forks, approvals/trusted commit, short-lived scoped federation, isolated runners/caches/artifacts.

**Trap:** masking logs as complete protection.

### Problem 9 — Incident cleanup (hard)

Suspected compromised VM; engineer deletes it immediately.

**Solution.** Contain network/credentials while preserving disk/memory/log/control-plane evidence under response plan, snapshot if authorized, replace from trusted artifact, investigate scope. Deletion can destroy evidence and not revoke credentials.

**Trap:** treating host removal as eradication.

## 4. REAL-WORLD / APPLIED CONTEXT

### OWASP Top 10

OWASP Top 10 highlights broken access control, cryptographic failures, injection, insecure design, misconfiguration, vulnerable components, authentication failures, integrity failures, logging/monitoring failures, and SSRF. It is awareness baseline, not full verification standard.

### OAuth 2.0 / OpenID Connect

OAuth delegates authorization; OIDC adds authentication identity. Authorization code with PKCE protects public clients. Resource servers validate access tokens/audience/scope and authorize resource. Do not use ID token as arbitrary API access token.

### Cloud workload identity

Azure managed identity/workload identity lets workloads obtain short-lived tokens without stored client secret. RBAC and federated subject/audience remain critical; overbroad identity is still dangerous.

## 5. COMPARISON TABLE

| Mechanism | Purpose | Key | Reversible | Example |
|---|---|---|---|---|
| Encoding | Representation | None | Yes | Base64 |
| Hash | Fingerprint | None | No intended | SHA-256 artifact digest |
| Password hash | Slow verifier | Salt/optional pepper | No | Argon2id |
| HMAC | Integrity/auth shared | Secret | n/a | Webhook signature |
| Encryption | Confidentiality (+AEAD integrity) | Symmetric/public-key | Yes with key | AES-GCM |
| Digital signature | Integrity/authenticity | Private/public | Verification | Artifact/JWT signature |
| RBAC | Role permissions | Identity/role | n/a | Operator read-only |
| ABAC/ReBAC | Context/relationship | Attributes/graph | n/a | Clinician care relation |

## 6. COMMON MISTAKES & MISCONCEPTIONS

1. Security equals confidentiality—integrity/availability/accountability matter.
2. Risk can be zero—residual risk remains.
3. Authenticated means authorized—it does not.
4. Private network means trusted—identity still needed.
5. JWT is encrypted—typically signed but readable.
6. Decode token means validate—verify every claim/signature.
7. Hashing and encryption interchangeable—different purposes.
8. Base64 is encryption—it is encoding.
9. Encryption at rest solves access control—authorized service can decrypt.
10. WAF fixes insecure app—it is partial compensating control.
11. Scanner clean means secure—coverage/logic/config gaps exist.
12. Delete compromised host resolves incident—credentials/evidence/persistence remain.

## 7. CHEAT SHEET — REVIEW ONLY

Review only, not a substitute for the lesson.

- Asset→threat→vulnerability→control→residual risk.
- CIA plus authenticity/accountability/privacy/safety.
- AuthN identity; AuthZ action/resource/context; audit attribution.
- Default deny, least privilege, short-lived workload identity.
- Passwords: adaptive salted hash, never reversible.
- AEAD encryption; nonce uniqueness; managed key lifecycle.
- Hash fingerprint; HMAC shared auth; signature asymmetric auth.
- TLS verify chain+hostname; private network not authorization.
- Parameterize SQL; validate input/output context; defend SSRF/deserialization.
- Secure CI/artifacts/dependencies and SBOM/provenance.
- Security incident: contain + preserve evidence + revoke/rotate + recover/learn.

## 8. PRACTICE SET FOR SELF-TEST

1. List STRIDE threats for file upload.
2. Distinguish salt, pepper, encryption key.
3. State JWT checks for an API.
4. Design cross-tenant authorization test cases.
5. Choose HMAC or digital signature for third-party webhook with one shared secret versus public verification.
6. Explain envelope encryption.
7. Design safe URL-fetch control.
8. List security audit event fields.
9. Respond to exposed API token in public Git.
10. Prioritize CVE using factors beyond CVSS.

## 9. CURATED RESOURCES

- Ross Anderson, *Security Engineering*, 3rd ed., Chapters 1–4, 6, 8, 12, 21–25 — systems security, protocols, access, banking, network, economics and operations.
- NIST Cybersecurity Framework 2.0 — Govern, Identify, Protect, Detect, Respond, Recover outcomes.
- NIST SP 800-63B Digital Identity Guidelines — authentication, passwords, MFA, session guidance.
- OWASP Application Security Verification Standard 4.0.3 and Cheat Sheet Series — testable auth, session, access, validation, crypto, logging, SSRF and secrets controls.
- OWASP Top 10 2021 — application risk awareness baseline.
- RFC 8446 TLS 1.3, RFC 7519 JWT, OAuth 2.0 Security Best Current Practice RFC 9700, and OpenID Connect Core — primary protocol/security semantics.
- Adam Shostack, *Threat Modeling: Designing for Security*, Chapters 1–4 — practical data-flow/STRIDE threat modeling.
- NIST SP 800-61 Rev. 2, *Computer Security Incident Handling Guide* — preparation, detection/analysis, containment/eradication/recovery and learning.

## 10. RELATED TOPICS BRIDGE

### Before

1. **Networking/TLS/Cloud Identity:** protocol and platform mechanisms.
2. **Application/API/Database:** trust boundaries and data actions.
3. **Incident Operations:** safe response and evidence.

### After

1. **Privacy/Compliance Foundations:** governs personal data purpose/lifecycle/evidence.
2. **Healthcare/Fintech Foundations:** applies confidentiality/integrity/safety to domains.
3. **Security, Privacy and Audit advanced:** deepens tenant isolation, keys, audit chains and supply chain.
4. **LLMOps:** applies injection/tool/data controls.

---ANSWER KEY BELOW---

1. Spoof uploader, tamper content, deny upload, disclose files/metadata, resource DoS, execute/elevate via parser/path; repudiation requires audit.
2. Salt public unique per password; pepper shared secret verifier addition; encryption key decrypts ciphertext.
3. Allowed algorithm, signature/trusted key, issuer, audience, expiry/not-before/skew, type/required claims, then action/resource authorization/revocation policy.
4. Same ID different tenant, list/export/search, nested resource, guessed UUID, changed tenant header/body, admin/operator separation, stale membership, bulk APIs; all deny/audit.
5. HMAC for shared-secret parties; digital signature when signer private and many verifiers public/nonrepudiation context.
6. Random DEK encrypts data; KMS KEK wraps DEK; store wrapped DEK/nonce/AAD; authorization controls unwrap; rotate/rewrap.
7. Allowlist scheme/host, resolve and reject nonpublic/internal ranges at each redirect, pin/validate DNS, egress proxy/firewall, size/time limits, no metadata credentials.
8. Time, actor/workload, action, target, result, source/session/trace, policy/reason, safe change version; protected integrity/retention.
9. Revoke/rotate immediately, audit use, remove from current/history/logs/artifacts as governed, notify, replace with managed identity/secret, assume copied.
10. Affected installed version, reachability/exposure, exploit maturity, asset/data/privilege, compensating controls, business impact, patch risk, detection and regulatory deadline.
