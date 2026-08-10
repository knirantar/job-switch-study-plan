# Terraform and Infrastructure as Code

**Parent:** 05 — Cloud Platform  
**Target:** senior backend / AI-platform / MLOps engineering  
**Study time:** 3–4 hours plus validated Terraform exercises

## 1. FOUNDATIONS

Infrastructure as Code (IaC) expresses infrastructure intent in versioned machine-readable configuration and uses automation to reconcile actual resources toward that intent. The value is not that text creates a virtual network. The value is reviewable change, repeatability, dependency ordering, policy enforcement, drift detection and recovery evidence.

Terraform is a declarative infrastructure engine. A configuration says a resource should exist with attributes and relationships. Terraform loads provider schemas, evaluates expressions, builds a dependency graph, refreshes prior state against remote APIs, calculates a plan and applies graph operations. It is not a general-purpose imperative script, though provisioners and external data can introduce imperative behavior.

A **provider** is a plugin that translates Terraform resource/data-source operations into a remote API. A **resource** is managed infrastructure. A **data source** reads external information but does not own it. A **module** is a directory of Terraform configuration used as a reusable component; the working directory is the **root module**, and referenced modules are child modules. A **resource address** such as `module.network.azurerm_subnet.private["api"]` identifies one managed instance.

Terraform needs **state** because configuration alone cannot reliably map a block named `azurerm_resource_group.platform` to a particular Azure object, remember provider metadata or efficiently calculate change. State is a mapping between resource addresses and remote object identities/attributes. It is not merely a cache that can be casually deleted. Losing state can make Terraform propose duplicate resources or destruction; exposing it can leak secrets.

The core workflow is `init → fmt/validate/test → plan → review/policy/approval → apply saved plan → verify`. `plan` compares configuration, previous state and refreshed remote objects; it is a proposal based on an observation in time. Remote APIs can change between plan and apply, so apply the reviewed saved plan under state lock and still inspect outcome.

Declarative does not mean risk-free or idempotent in the mathematical sense. Provider APIs may be eventually consistent, partial operations can succeed before errors, replacement may destroy/recreate, and a run can lose connectivity after cloud creation but before state persistence. Terraform recovers through refresh/state/provider logic, but operators need evidence and careful state procedures.

IaC history includes earlier configuration-management and provisioning systems, then cloud APIs and immutable-infrastructure practices. Terraform's provider ecosystem and graph model made multi-provider declarative provisioning popular. HashiCorp Terraform and OpenTofu now have separate licensing/governance; syntax/provider compatibility exists but version features and support must be selected explicitly. This lesson uses installed Terraform CLI and official current Terraform documentation.

## 2. CORE MECHANICS

### 2.1 Configuration and evaluation

Terraform language uses blocks and expressions. Input variables define a typed interface; locals name derived values; resources/data sources define graph vertices; outputs expose module results. Values can be known during planning or **unknown until apply** (for example a generated resource ID). Unknown is not null; expressions propagate it so Terraform can still plan structure where possible.

Types include string, number, bool, list/tuple, map/object and set. Declare precise object types and validation rather than `any`. `null` means omission/absence depending provider schema. Mark an object attribute optional with deliberate default. Variable validation fails early; resource pre/postconditions validate lifecycle-specific facts; top-level `check` blocks assert health without necessarily stopping all operations according to semantics/version.

The lab validates environment, owner, data classification and `CC-NNNN` cost-center format. A precondition requires at least three replicas for critical services. The production classification check demonstrates cross-variable policy, but organizational policy should also run outside a module so it cannot be removed in the same untrusted change.

### 2.2 Dependency graph

An expression reference creates an implicit edge. If subnet uses `azurerm_virtual_network.main.id`, VNet must precede subnet; destruction reverses dependency. Prefer these data-flow references over `depends_on`, which is for hidden behavioral dependencies the provider graph cannot infer. Overusing `depends_on` makes more values unknown and serializes plans.

Terraform can apply independent vertices in parallel up to its concurrency setting/API constraints. Parallel creation does not imply business independence: Azure rate limits, eventual propagation, subnet locks or shared policy may fail. Provider should model retry; reduce parallelism only with evidence, not as permanent cure for faulty graph/provider.

Cycles cannot be ordered. A security group that references itself may have a provider-specific separate rule resource pattern. Break design cycles by separating interfaces/attachments, not arbitrary sleeps. `time_sleep` masks eventual consistency and lengthens every run; prefer provider polling/readiness or explicit API boundary.

### 2.3 Init, providers and the lock file

`terraform init` initializes backend, installs modules/providers and writes `.terraform.lock.hcl`. Configuration version constraints define acceptable provider versions; lock file records the selected provider version/checksums so CI and developers choose the same by default. Commit the lock file.

HashiCorp docs state current lock file tracks provider selections, not remote module versions. Pin module version/source commit/digest explicitly. A Git branch source is mutable. For private registry/modules, use semantic version constraints and reviewed updates.

`terraform init -upgrade` intentionally revisits constraints; do it in a dedicated PR with provider changelog and plan across environments. Provider upgrades can change defaults, schemas and replacement behavior. Populate checksums for all CI platforms where needed (`terraform providers lock -platform=...`) so Mac developer and Linux CI don't create lock churn.

Provider binaries execute with runner privileges and credentials. Allow trusted namespaces/registries, verify signed checksums, isolate runners and use short-lived credentials. A malicious provider/module/provisioner is supply-chain code execution.

### 2.4 State contents and sensitivity

State stores resource attributes used for mapping/planning, including values marked sensitive. `sensitive=true` redacts CLI output; it does not encrypt/remove value from state or plan. Never put secrets in Terraform unless resource/API requires it; retrieve from secret manager at runtime and prefer generated/rotated systems whose value isn't returned to Terraform.

Use remote backend with encryption, versioning/backups, private network, least data-plane permissions, audit and locking. Keep production states separate by blast radius/lifecycle, not one giant state. State separation trades smaller plans/permissions/failures against cross-state dependencies and coordination.

Do not commit `.terraform/`, state, plan files or crash logs; all may contain credentials/sensitive values. HashiCorp docs note backend credentials passed in config/`-backend-config` may be written into `.terraform` and plan files. Prefer environment/workload identity.

### 2.5 Azure remote backend

The `azurerm` backend stores a state blob and supports Azure Blob native locking and consistency checks. Official docs recommend Microsoft Entra ID and OIDC/workload identity; SAS/access keys are not recommended for new workloads. `backend-azurerm.example.txt` contains non-secret coordinates and `use_azuread_auth=true`.

Bootstrap problem: Terraform state storage must exist before that configuration can use it. Provision with a separately governed bootstrap stack/subscription or controlled one-time process. Enable blob versioning/soft delete as supported policy, encryption, network restrictions and diagnostic logs. The CI principal needs precise blob data permissions; state administrators are highly privileged because state reveals/controls infrastructure.

Backend blocks cannot use variables. Supply environment-specific non-secret coordinates via reviewed files/environment. Never commit client secret. Changing backend requires `terraform init -migrate-state`/`-reconfigure` decision and backup; rehearse.

### 2.6 Locking and concurrency

State locking prevents two applies from independently reading the same prior state and overwriting mappings. A lock is not a cloud-wide mutex: another state, portal user or external tool can modify the same Azure resource. Design one owner per object.

If runner crashes, lock may persist until backend lease expires/manual action. `force-unlock LOCK_ID` is dangerous: first prove no apply still runs, identify workspace/backend/owner, preserve logs, and get approval. Unlocking a live apply permits concurrent corruption.

State has lineage and serial. HashiCorp docs say state push protects against mismatched lineage/higher remote serial unless `-force`; forcing can overwrite newer state. Manual `state push` is emergency surgery: pull/version backup, stop all runs, verify remote objects and peer review.

### 2.7 Plan semantics

Normal plan refreshes remote state, compares config/state/remote and proposes create/update/replace/destroy. `-refresh-only` updates state/outputs to remote reality without changing objects when applied; use to intentionally accept drift after review. `-refresh=false` speeds/isolates but can plan from stale state and is unsafe as routine production shortcut.

Save automation plan with `terraform plan -out=tfplan`, render `terraform show -json tfplan` for policy, approve exact artifact, then `terraform apply tfplan`. Plan contains sensitive data; secure and expire it. Do not apply by rerunning an unreviewed new plan after approval. Still, provider/API preconditions can cause apply failure if remote changed.

Exit code `terraform plan -detailed-exitcode`: 0 no changes, 1 error, 2 changes. CI must handle 2 as expected, not failure. Speculative PR plan should use read credentials and avoid data sources/provisioners that mutate.

Plan actions: `+` create, `~` update, `-/+` destroy then create, `+/-` create before destroy, `-` destroy. A single “forces replacement” field on database/storage can be catastrophic. Require policy/manual review of deletes/replacements and capacity/cost.

### 2.8 Apply, partial failure and recovery

Apply walks the graph and updates state after operations. If some resources succeed and later node fails, earlier infrastructure remains and state should record it. Fix cause and plan again; do not assume rollback. Cloud API may create object but response/state write fail; next refresh/import must reconcile.

If backend state write fails irrecoverably, Terraform may write local recovery state, per HashiCorp backend docs. Protect that file, halt runs and push only after confirming lineage/serial/current remote under incident procedure. Never run another apply that creates competing state.

Provider timeouts/retries should be configured where available. A timeout is ambiguous: resource may finish later. Query Azure activity/resource state and let refresh reconcile. Avoid manual deletion until ownership/outcome is understood.

### 2.9 Resource lifecycle

`create_before_destroy` can reduce downtime for replaceable resources but requires coexistence: unique names, quota, network/IP and downstream capacity. It propagates through dependencies and can surprise. `prevent_destroy` blocks planned destruction but can be removed by the same config change; external policy/locks/backup are stronger safeguards. `ignore_changes` tells Terraform to stop reconciling selected attributes after create; it can hide malicious/manual drift. Use only where another named controller owns field, with documentation/audit.

`replace_triggered_by` ties replacement to another managed value/resource. `precondition`/`postcondition` encode assumptions. Destruction provisioners are unreliable during remove/failure and should not own critical cleanup.

Resource `-target` is exceptional recovery, not partial deployment architecture. It can omit required graph changes and leave inconsistent outputs. Follow with full plan and document why. `-replace=address` is reviewed replacement; `taint` is older workflow and immediate state mutation.

### 2.10 Count versus for_each

`count` addresses by numeric index. Removing middle item shifts indices, potentially replacing/moving many resources. `for_each` addresses by stable key and is safer for named subnets/tenants/services:

```hcl
for_each = { api={cidr="10.0.1.0/24"}, data={cidr="10.0.2.0/24"} }
name = each.key
```

Keys must be known before apply and become part of state/address. Do not use sensitive values as keys because addresses appear in output/state. Renaming a key is an address move; add `moved` block.

For ordered identical ephemeral instances, count may be fine. For availability zones/resources with identity, map keys. Convert count→for_each with explicit moved blocks per instance to prevent recreation.

### 2.11 Modules

A module should encode a cohesive abstraction and policy, not wrap every resource one-for-one. Inputs typed/validated; outputs minimal and semantic; providers configured in root and passed, not hardcoded credentials. Avoid enormous “platform” module with hundreds of flags; composition and opinionated smaller modules are testable.

Version modules immutably and publish changelog/upgrade path. A breaking module change may generate infrastructure replacement even with semantic version bump; consumers must inspect plan. Avoid deep nesting that obscures resource addresses. Expose data/resources only when a real use case exists.

Test module at unit/expression level and integration in isolated subscription/resource group. Terraform `test` can execute plan/apply test files depending run blocks; apply tests cost and mutate, so isolate and destroy reliably. Static validation cannot prove cloud policy or service functionality.

### 2.12 Refactoring with moved/removed blocks

Renaming a resource block without mapping makes Terraform see old address removed/new address added, often destroy/create. A `moved` block declares old→new address so state association changes during plan. Keep moved blocks while supported callers may upgrade across the change; removing too soon breaks upgrade path.

For complex/manual moves, `terraform state mv` mutates state immediately; back up and peer-review exact addresses. Prefer configuration-driven moved blocks because plan records intent and every workspace applies it.

`removed` blocks (version-dependent) can declare Terraform should forget/destroy with lifecycle intent. `state rm` stops management without destroying remote object; dangerous orphan/drift risk. After any refactor, expect zero remote changes in plan when intent is address-only.

### 2.13 Import and adoption

Import binds an existing remote object to one resource address. CLI import historically requires configuration and changes state; it does not automatically create correct config. Modern `import` blocks make adoption declarative/reviewable and can support generated config workflows. Import each object once; duplicate bindings violate Terraform's one-address/one-object assumption.

Workflow: inventory and freeze manual change, write minimal exact config, back up state, import block, plan, fill all managed/default attributes until plan is no-op, then remove import block if desired. A plan proposing replacement after import is a stop signal, not cleanup permission.

Azure resource IDs are case/shape-sensitive by provider semantics. Import child resources separately as docs require. Provider may read defaults/tags/policies not represented; reconcile deliberately.

### 2.14 Drift

Drift is remote change outside expected Terraform apply or changed external default. Normal plan refresh detects it and proposes revert/config adoption. Decide authority:

- Accidental portal change → revert through apply.
- Emergency approved hotfix → encode same in config, then plan no-op.
- Another controller legitimately owns field → model ownership/`ignore_changes` narrowly.
- Resource moved across state → use state/refactor/import workflow.

Run scheduled read-only plans with alerts, but avoid auto-applying destructive drift correction without review. Azure Policy may mutate/deny; model policy-assigned tags/defaults and provider behavior. Drift in security groups/identity/private endpoints is high priority.

### 2.15 Workspaces and environment layout

CLI workspaces are multiple state instances for same configuration. They are useful for similar ephemeral environments but weak isolation for production because backend/credentials/code remain shared and accidental workspace selection is possible. Prefer separate root configurations/state keys/accounts/subscriptions for strong environment/tenant boundaries, with reusable modules.

Do not create one workspace per customer at tens of thousands scale without operational model. State size, plan latency, locks and blast radius guide partitioning. A state with entire organization creates slow plans/global permissions; a state per tiny resource creates dependency sprawl. Group by lifecycle, owner, privilege and failure domain.

Cross-state outputs create coupling. `terraform_remote_state` readers may gain access to entire state backend even if only outputs appear; prefer publishing minimal nonsecret facts to a config registry/cloud data source. Avoid cyclic state dependencies.

### 2.16 Azure resource design

Use separate subscriptions/resource groups by environment/blast/ownership as governance allows. Resource naming must handle Azure global uniqueness and replacement. Stable random suffix stored in state can prevent collisions but impacts import/recovery; deterministic names expose predictability/global namespace constraints.

Tag owner, environment, data classification, cost center and managed-by, enforced with merge policy. Protect critical state/storage/Key Vault databases with Azure resource locks and policy in addition to Terraform `prevent_destroy`; document break-glass removal. Private endpoints require DNS zones/links/routing and can create dependency cycles.

Use `azurerm` provider with pinned compatible version, `features {}`, subscription/tenant via environment/workload identity, and explicit provider aliases for controlled multi-subscription/region. Never allow one generic principal Owner over every subscription. CI plan can read; apply identity has scoped change permissions; state access separate and audited.

### 2.17 Secrets and identity

Prefer CI OIDC federation to Microsoft Entra ID: runner exchanges signed short-lived identity for Azure token. No long-lived client secret in repo/CI vars. Restrict issuer, subject (repo/branch/environment), audience and role scope. Protect production environment approval because a compromised workflow on allowed branch can request token.

Terraform variables marked sensitive only redact. `TF_VAR_*`, command arguments, plan/state/logs can leak. Use secret references/Key Vault resources without reading secret value where possible. If Terraform generates secret, state becomes secret store and needs equivalent controls/rotation; consumers should fetch by identity.

### 2.18 Testing and policy pipeline

Fast gates:

1. `terraform fmt -check`.
2. `terraform init -backend=false` with locked provider mirror/cache.
3. `terraform validate`.
4. lint/security/config policy.
5. unit/module `terraform test` where no cloud apply.
6. plan against isolated/test account.
7. JSON plan policy: deny public endpoints, wildcard identity, missing tags/encryption, unapproved regions/SKUs, deletes/replacements without approval and budget breach.
8. human review of semantic diff/cost/failure.
9. apply saved plan under lock + post-deploy verification.

Policy must inspect planned values including unknowns. A rule that treats unknown as safe has bypass. Static scanning source misses module/provider defaults; JSON plan sees resolved structure but secrets and some unknowns remain. Cloud-side Azure Policy is defense-in-depth, not replacement; a deny during apply causes partial failure if pipeline should have caught it.

### 2.19 Destructive-change safety

Plan deletion/replacement questions:

- Is object stateful? Backup and restore tested?
- Does create-before-destroy fit naming/quota/cost/dependencies?
- Is dependent data replicated/migrated?
- What is RPO/RTO and rollback/roll-forward?
- Is change caused only by address refactor (use moved)?
- What locks/policies/approvals required?

Never use `terraform destroy` against shared/prod workspace casually. Scope environment by backend identity, require protected pipeline approvals and perhaps manual break-glass token. `prevent_destroy` helps accidental plan but is not access control.

### 2.20 Debugging and recovery

Read error at graph vertex; inspect provider/API request ID, Azure activity log and state/address. Use `terraform state list/show` (redact), `terraform show -json` and `terraform graph`. Enable `TF_LOG` only briefly in secure environment; logs can contain sensitive data.

For state mismatch: stop applies, acquire/confirm lock, pull encrypted backup, inspect lineage/serial, compare remote object IDs, then prefer import/moved/state CLI. Never edit JSON directly. For stuck operation, determine cloud outcome before retry/delete. After emergency repair, full refresh plan must be reviewed to zero/expected changes and incident documented.

## 3. WORKED PROBLEMS

### Problem 1 — Address instability

**Statement.** `count` creates subnets `[api,data,ml]`; remove data. Plan wants index shifts.

**Solution.** Count addresses `[0],[1],[2]`; removing middle makes ml move from 2 to 1. Refactor to `for_each` keyed `api`,`data`,`ml` with moved blocks mapping old indices. Then removing `data` destroys only its key. Review no unintended replacements.

**Mistake caught.** Treating list order as stable resource identity.

### Problem 2 — State secret

**Statement.** Output password is `sensitive=true`; team commits state because CLI hides it.

**Solution.** Sensitive only redacts presentation. State/plan may contain plaintext. Remove from Git history under security process, rotate password, migrate encrypted locked remote backend, restrict/audit access, and redesign consumers to fetch secret by workload identity. Add ignore/scanning.

**Mistake caught.** Equating redaction with encryption.

### Problem 3 — Plan replacement

**Statement.** Database plan shows `-/+` due to name/location change.

**Solution.** Stop. Read provider force-new attribute, data/backups/RPO/RTO, naming coexistence and dependent endpoints. Prefer new resource, replication/migration, validation and staged cutover with `create_before_destroy` only if provider/name/quota permit. Protect deletion and approve separately.

**Mistake caught.** Approving because diff is one line.

### Problem 4 — Crashed apply and lock

**Statement.** CI died; state is locked and an Azure VNet appears.

**Solution.** Prove process/run ended and identify lock ID/backend. Check Azure activity/VNet and remote state. Let/force-unlock only under approval. If VNet absent from state, write matching config and import/reconcile rather than create duplicate/delete blindly. Full plan afterward.

**Mistake caught.** Immediate force-unlock and rerun.

### Problem 5 — Resource rename

**Statement.** Rename `azurerm_resource_group.core` to `.platform`; plan destroys/creates.

**Solution.** Add `moved { from=azurerm_resource_group.core to=azurerm_resource_group.platform }`. Plan should show address move/no remote mutation (assuming config unchanged). Keep block across supported upgrade path. Manual state mv only if configuration-driven move cannot express it.

**Mistake caught.** Assuming block label is cosmetic.

### Problem 6 — Import portal resource

**Statement.** Adopt production Key Vault created manually.

**Solution.** Freeze changes; write exact resource/provider config; secure state backup; declare import block to exact address/ID; plan. Fill policies, RBAC, purge protection, network, tags from observed intended state until no destructive diff. Never apply replacement. Transfer ownership and drift alert.

**Mistake caught.** Import then immediately apply generated defaults.

### Problem 7 — Backend credential leak

**Statement.** Pipeline passes storage SAS in `-backend-config`; saved plan/artifacts persist.

**Solution.** Revoke SAS, inspect/purge logs/artifacts securely, switch to OIDC/Entra `use_azuread_auth`, nonsecret backend coordinates, least Blob Data role, private access and audit. HashiCorp warns backend auth can be copied into `.terraform`/plans.

**Mistake caught.** Assuming backend arguments remain only in process memory.

### Problem 8 — Two states own one resource

**Statement.** Network and app states both import same subnet.

**Solution.** Both believe ownership and can overwrite/destroy. Choose one owner (network); remove mapping from app state with backup/lock and configuration removal, then app reads published subnet ID/data source with permissions. Plan both. Do not destroy remote subnet.

**Mistake caught.** Treating import as read-only reference.

### Problem 9 — Policy unknown

**Statement.** Plan policy allows public IP because value is `(known after apply)`.

**Solution.** Unknown is not compliant. Rule should deny, require proven source/module invariant, or defer with explicit gated postcondition/provider/cloud policy. Test unknown-path inputs. Source lint and plan policy plus Azure Policy reduce gaps.

**Mistake caught.** Treating unknown as false/safe.

## 4. REAL-WORLD / APPLIED CONTEXT

**Azure backend.** HashiCorp's current `azurerm` backend documentation says Azure Blob supports native state locking/consistency and recommends Entra authentication, particularly OIDC/workload identity; access keys/SAS are not recommended for new workloads. It warns credentials supplied directly can persist in `.terraform`/plan files. The included backend example follows this boundary without real credentials.

**Provider lock reproducibility.** Current Terraform documentation says `.terraform.lock.hcl` should be committed and records provider selections/checksums; remote module versions are not currently locked there. A production module source therefore needs immutable version, while provider upgrades update lock in review.

**Offline lab.** The included lab uses `terraform_data`, a built-in resource, so no provider download/cloud cost occurs. On this machine Terraform initialized, validated and saved a plan showing exactly two creates. Its variable/precondition/check logic demonstrates module/policy mechanics while keeping cloud credentials out of training.

## 5. COMPARISON TABLE

| Tool/action | Changes config | Changes state | Changes remote | Normal use | Risk |
|---|---:|---:|---:|---|---|
| `fmt`/`validate` | formatting only/no | no | no | fast CI | semantic cloud errors remain |
| speculative `plan` | no | refresh read/no persisted intent normally | no | review | snapshot can become stale |
| saved plan + apply | no | yes | yes | approved automation | plan contains secrets; partial failure |
| `refresh-only` apply | no | yes | no intended mutation | accept observed drift | legitimizes unwanted drift |
| import block | yes | yes on apply | no ownership creation | adopt object | wrong config can next mutate/destroy |
| moved block | yes | address association | no intended mutation | refactor | wrong mapping binds wrong object |
| `state rm` | no | removes binding | no | stop management | orphan unmanaged resource |
| `state push -force` | no | overwrites | no immediate | rare recovery | catastrophic state loss |

| Environment strategy | Isolation | Reuse | Best use | Trap |
|---|---|---|---|---|
| CLI workspaces | state names, shared root/backend | high | similar ephemeral | wrong workspace/weak prod boundary |
| directories per env | separate roots/state | modules reuse | production boundaries | config duplication |
| separate repos/stacks | strongest ownership pipeline | versioned modules | org/team/failure domains | dependency/version coordination |

## 6. COMMON MISTAKES & MISCONCEPTIONS

1. **State is disposable cache.** It maps addresses to real objects; deletion loses ownership knowledge.
2. **Sensitive means encrypted.** It redacts UI; state/plan retain value.
3. **Put state in Git.** No secure locking and secret/data-loss risk.
4. **Tag/provider constraint pins exact dependency.** Lock provider; pin module version/source immutably.
5. **`init -upgrade` in every CI run.** It creates unreviewed provider drift.
6. **Plan is timeless promise.** Remote can change; apply reviewed saved artifact under lock.
7. **Apply rolls back on failure.** Earlier graph vertices may remain successfully created.
8. **Force-unlock fixes stuck run.** If run alive, concurrent applies corrupt ownership.
9. **Direct state JSON edit.** Bypasses schema/lineage/serial safeguards.
10. **`-target` for normal deploys.** It omits graph changes and creates partial state.
11. **`ignore_changes` fixes drift.** It cedes ownership/hides security changes.
12. **`prevent_destroy` is security.** Same author can remove it; external policy/approval needed.
13. **Count safe for named resources.** Middle deletion shifts index identities.
14. **Rename block label only.** Address changes and plan may replace without moved block.
15. **Import creates correct config.** It binds state; you must reconcile every managed attribute.
16. **One object in two states.** Competing owners mutate/destroy unpredictably.
17. **Workspaces equal account isolation.** Shared backend/code/credentials make prod mistakes easier.
18. **Module is secure because internal.** It executes provider/module/provisioner supply-chain code.
19. **Unknown plan value is compliant.** Policy cannot prove it; fail/gate appropriately.
20. **Portal hotfix can stay undocumented.** Next apply may revert; encode and reconcile.

## 7. CHEAT SHEET — REVIEW ONLY, NOT A SUBSTITUTE FOR THE SECTIONS ABOVE

- Terraform: config + prior state + refreshed remote → dependency graph → plan → apply/state.
- State is sensitive ownership database; remote encrypted/versioned/locked/private/audited.
- Azure backend: Entra/OIDC preferred; no SAS/key/client secret in config/flags/artifacts.
- Commit `.terraform.lock.hcl`; constraints allow, lock selects provider; pin remote modules separately.
- Reference creates graph edge; `depends_on` only hidden dependency; avoid sleeps/provisioners.
- CI: fmt, init backend false, validate/test/lint, saved plan JSON policy, approve, apply exact plan, verify.
- Plan 0 no diff, 1 error, 2 changes with detailed exit; scrutinize delete/replace.
- Apply partial failure does not roll back; refresh/reconcile ambiguous API outcome.
- Stable identities: `for_each`; count for truly positional; rename with moved block.
- Import binds one object to one address; reach no-op before mutation.
- `ignore_changes`, target, state rm/mv/push and force-unlock are sharp tools with audit/backups.
- `sensitive` redacts, not encrypts; minimize secret values in Terraform.
- Separate states by lifecycle/owner/privilege/blast; avoid cross-state secret exposure/cycles.
- Terraform policy + Azure Policy + RBAC/resource locks + backups are layered controls.

## 8. PRACTICE SET FOR SELF-TEST

1. Explain the three-way comparison among configuration, state and remote API for an out-of-band tag change.
2. Convert `count` subnets at indices 0–2 to keyed `for_each` and list moved blocks.
3. Design Azure Blob state backend authentication/permissions/network/backup for production CI.
4. A saved plan is approved, then another pipeline applies first. Explain lock and saved-plan outcomes.
5. Recover when Azure created a resource but Terraform failed writing remote state.
6. Design a module interface for private AKS workload network without exposing provider credentials or enormous flags.
7. Decide state boundaries for network, AKS platform, application and regulated database; explain dependencies.
8. Write policy gates for a plan adding public IP, Owner role, unencrypted storage and resource deletion with unknown values.
9. Plan an import of 200 existing resource groups using declarative import and no destructive change.
10. Contrast Terraform `prevent_destroy`, Azure resource lock, backup and approval—what failure each handles.

## 9. CURATED RESOURCES

1. HashiCorp Terraform, [Language overview](https://developer.hashicorp.com/terraform/language). Authoritative blocks, expressions, modules, types and lifecycle language.
2. HashiCorp Terraform, [State](https://developer.hashicorp.com/terraform/language/state) and [Purpose](https://developer.hashicorp.com/terraform/language/state/purpose). Exact mapping, metadata, performance and synchronization rationale.
3. HashiCorp Terraform, [Backends: State Storage and Locking](https://developer.hashicorp.com/terraform/language/state/backends). Remote persistence, recovery state, lineage/serial and locking boundaries.
4. HashiCorp Terraform, [`azurerm` Backend](https://developer.hashicorp.com/terraform/language/backend/azurerm). Current Azure Blob locking, Entra/OIDC methods and credential warnings.
5. HashiCorp Terraform, [Dependency Lock File](https://developer.hashicorp.com/terraform/language/files/dependency-lock). Provider selection/checksum behavior and module-lock limitation.
6. HashiCorp Terraform, [`plan`](https://developer.hashicorp.com/terraform/cli/commands/plan) and [`apply`](https://developer.hashicorp.com/terraform/cli/commands/apply). Normal/refresh/destroy planning, saved plans and automation semantics.
7. HashiCorp Terraform, [Modules](https://developer.hashicorp.com/terraform/language/modules) and [Module syntax](https://developer.hashicorp.com/terraform/language/modules/syntax). Composition, sources, versions and provider passing.
8. HashiCorp Terraform, [Refactoring](https://developer.hashicorp.com/terraform/language/modules/develop/refactoring) and [Import](https://developer.hashicorp.com/terraform/language/import). Moved blocks, address preservation and declarative adoption.
9. HashiCorp Terraform, [Tests](https://developer.hashicorp.com/terraform/language/tests). Native test files/run blocks, mocks and plan/apply test boundaries.
10. Microsoft Learn, *Azure landing zones—Terraform accelerator* and *Authenticate Terraform to Azure*. Azure governance layout and workload-identity implementation; verify against organization/provider versions.

## 10. RELATED TOPICS BRIDGE

### Before

1. **Containers.** IaC provisions registries/runtime infrastructure and policy for image deployment.
2. **Kubernetes.** Terraform can provision clusters/node pools/identity/network, while Kubernetes objects have their own reconciliation owner.
3. **Data Migrations.** Infrastructure replacement/refactoring needs expand–migrate–contract and recovery evidence.
4. **Capacity-Driven Design.** Region/zone/node/database/storage quantities become reviewed variables and policies.

### After

1. **CI/CD Supply Chain.** Plans, provider/module trust, approvals, OIDC and policy execute in delivery pipeline.
2. **Cloud Identity and Networking.** Entra roles, private endpoints, VNet/DNS and workload federation become IaC resources.
3. **SRE/Observability.** Drift, apply health, cloud activity and capacity integrate with operational controls.
4. **Regulated Design.** State security, change evidence, separation of duties and resource deletion require governance.

---ANSWER KEY BELOW---

1. Refresh reads remote changed tag into current view/state; config retains desired old tag. Plan proposes update reverting remote to config. If hotfix approved, encode new tag in config first so refreshed plan is no-op/expected. If provider ignores/defaults field, inspect ownership semantics.
2. Define map `{api=...,data=...,ml=...}` and `for_each`. Moved blocks: `from=res.subnet[0] to=res.subnet["api"]`, similarly 1→data, 2→ml using actual address syntax. Plan must show moves/no replacements before later removing a key.
3. Dedicated locked-down state subscription/resource group/storage/container; encryption, blob versioning/soft delete, private endpoint/firewall/DNS, logs/alerts/backups/restore drill. CI OIDC federated Entra principal with minimum Blob Data role on container; separate state-admin break glass; no keys/SAS; native locking and serialized pipeline.
4. First apply acquires lock; second waits/fails per timeout. After first changes state/remote, the old saved plan may be stale and apply should not be trusted/accepted; regenerate/review from new state. A lock serializes applies but does not make prior approval valid after intervening change.
5. Stop runs and preserve local recovery state/logs. Inspect Azure object/activity and remote state lineage/serial. If object exists but binding absent, add exact config and import to intended address (or cautiously recover state under documented process), then full refresh plan. Never rerun create blindly or force-push over newer state.
6. Inputs: address spaces/subnet intents/private DNS/firewall/service endpoints, allowed egress, tags/region and typed feature choices; outputs semantic subnet IDs/private DNS references. Provider configured/aliased in root and passed; no credentials. Enforce validations/policy and compose modules rather than hundreds of booleans.
7. Network state: shared long-lived/high-privilege VNet/DNS. AKS platform: cluster/node pools/workload identity tied lifecycle. Application primarily Kubernetes/GitOps state, reading minimal published facts. Regulated DB separate restricted state/identity/approvals. Publish nonsecret IDs through Azure data/config rather than broad remote-state access; avoid cycles.
8. Deny public IP unless explicit approved exception; deny Owner/wildcards; require encryption/private access/tags/region; deny destroy/replace of protected classes without signed approval and recovery evidence. Unknown security value is deny/defer, not pass. Run source + JSON plan + Azure Policy and test bypasses.
9. Inventory/freeze and generate exact typed map keyed by stable names; declare resource `for_each`; create one import block per key/ID (generated code reviewed); batch plans in isolated state if blast dictates; reconcile defaults/tags until no mutation; apply imports under lock; verify each object owned once and enable drift pipeline.
10. `prevent_destroy` catches Terraform plan but removable in code. Azure resource lock blocks provider/API deletion until separately removed, including portal (scope/permissions matter). Backup enables data recovery but not availability and must be restored/tested. Approval enforces human/separation/change evidence but can err. Layer all for critical data.
