# Cloud Identity and Networking

**Parent:** 05 — Cloud Platform  
**Target:** senior backend / AI-platform / MLOps engineering on Azure  
**Study time:** 3–4 hours plus the executable policy lab

## 1. FOUNDATIONS

Cloud security asks two independent questions: **who may perform which operation on which resource**, and **which network flow may reach which endpoint**. Identity authorization answers the first; networking constrains the second. Neither replaces the other. A private database reachable only from an application subnet is still unsafe if every workload identity can read it. A perfectly scoped identity can still be abused if its public endpoint accepts traffic from anywhere and credentials are stolen.

Early enterprise systems trusted a network perimeter: inside was trusted, outside was hostile. Cloud, remote work, APIs and compromised workloads made location an unreliable identity. Zero Trust reframed the model as “verify explicitly, use least privilege, assume breach.” This does not mean “remove networks.” It means identity, device/workload context, network segmentation, encryption and telemetry form independent layers whose failures should not collapse the whole defense.

An **identity** is a security principal that can be authenticated. Human identities represent people; **workload identities** represent software. In Microsoft Entra ID, an application registration describes an application, while a **service principal** is its tenant-local identity. An Azure **managed identity** is a service principal whose credential lifecycle Azure manages. A system-assigned managed identity shares the lifecycle of one Azure resource; a user-assigned identity is a separate reusable resource.

**Authentication** establishes which principal is acting. **Authorization** decides whether that principal may perform an action. Azure Role-Based Access Control (RBAC) evaluates **role assignments**: principal + role definition + scope. A **role definition** lists allowed management-plane `actions` and data-plane `dataActions`, along with exclusions. **Scope** is hierarchical: management group → subscription → resource group → resource. An assignment normally applies to descendants. Least privilege therefore means both the smallest action set and smallest scope.

The **management plane** configures Azure resources through Azure Resource Manager—for example, changing a storage account firewall. The **data plane** accesses the service's contents—for example, reading a blob or Key Vault secret. Being Contributor on a resource does not automatically mean reading its data; conversely, a data role should not grant resource configuration. This separation is crucial in healthcare and fintech: platform operators may manage availability without reading patient records or transactions.

A **virtual network (VNet)** is a private IP routing boundary. A **subnet** partitions its address space. A route decides the next hop. A **network security group (NSG)** applies ordered stateful layer-3/4 allow/deny rules to subnet or network interfaces. **Ingress** enters a boundary; **egress** leaves it. **North–south** traffic crosses a workload perimeter; **east–west** traffic moves between internal components. A firewall can add centralized filtering, application/FQDN policy and inspection.

**CIDR** notation describes an IP prefix. IPv4 has 32 bits; `/24` fixes 24, leaving 8 host bits and 256 total addresses. Azure reserves addresses in each subnet, so total arithmetic is not identical to usable platform addresses. Address plans must not overlap with peered VNets or on-premises networks. A `/16` such as `10.42.0.0/16` contains 65,536 addresses and 256 distinct `/24` blocks, but allocating the entire range without growth/region planning creates future routing pain.

DNS maps names to addresses and is part of the security/data path. A **private endpoint** creates a network interface with a private address in the VNet for a specific PaaS resource. Correct private DNS makes the normal service name resolve to that private address from intended networks. A **service endpoint** instead extends subnet identity to a supported PaaS service while DNS continues to resolve its public address; Microsoft currently recommends Private Link/private endpoints for secure private access where appropriate. Private endpoint creation alone does not disable a service's public access or make hybrid DNS work.

Without these concepts, teams put subscription-wide Owner credentials in pipelines, use shared secrets that never rotate, flatten all services into one routable network, allow `0.0.0.0/0`, and declare a service “private” while clients resolve public DNS. The resulting blast radius is organizational rather than workload-sized.

## 2. CORE MECHANICS

### 2.1 Identity lifecycle and credential choice

Use a human identity for interactive work with multifactor authentication and privileged elevation. Use a managed identity for an Azure-hosted workload. Use workload identity federation/OIDC for an external CI job or Kubernetes service account so it exchanges a signed, short-lived assertion rather than storing a client secret. A service principal secret is a fallback for systems that cannot federate; it needs secret-manager storage, owner, expiry, rotation and detection.

System-assigned managed identity fits one resource: deleting an App Service removes the identity. User-assigned identity fits stable identity across replacements or multiple replicas/resources, but reuse expands blast radius and makes attribution/coordinated change harder. Never reuse one production identity across unrelated services merely to reduce role assignments.

### 2.2 Azure RBAC evaluation

Start with the requested operation and exact target. Gather role assignments inherited from target and ancestors, expand group membership, match `actions`/`dataActions`, subtract exclusions and account for deny assignments/conditions. Azure denies if no applicable allow exists; an explicit platform-managed deny can override allow. Microsoft documents that deny assignments are created/managed by Azure (including deployment-stack scenarios), rather than arbitrary everyday role design.

Suppose `api-prod-mi` has a custom secrets-reader role only at `/.../vaults/kv-prod`. It may read `kv-prod/secrets/db`, but not write that secret, read `kv-prod-backup`, or assign roles. The lab's `scope_contains` adds a slash boundary; a naïve string prefix would incorrectly treat `/groups/prod` as ancestor of `/groups/production`.

Avoid Owner and Contributor for applications. Contributor can modify resources broadly and may create paths to code execution, while Owner can also manage access. Prefer built-in data roles when their semantics fit; otherwise create a narrow custom role using stable operation names, document excluded operations and test both allowed and forbidden cases. Role changes can take time to propagate, so bounded retry may be legitimate after assignment—but “wait longer” must not conceal wrong tenant, principal, scope or data-plane role.

### 2.3 Privileged access and separation of duties

Standing privilege accumulates. Use Entra Privileged Identity Management for eligible, time-bounded human access with MFA, justification and approval where risk warrants. Keep break-glass accounts isolated, monitored and tested. Separate identity administration, infrastructure deployment, application release and audit. A production deployer should not grant itself a stronger role; a developer approving their own privileged production change defeats the control.

### 2.4 OIDC federation mechanics

A CI platform signs a short-lived ID token with claims such as issuer, audience, repository, ref/environment and workflow. Entra validates the issuer signature and matches a configured federated credential. It then issues an Azure access token for the service principal/managed identity. Security depends on claim specificity: bind production to the exact repository and protected environment, not an organization wildcard; validate intended audience; protect the workflow and reviewers; grant only a scoped deployment role.

An ID token is not the Azure access token and should not be logged. OIDC removes stored cloud credentials from the repository, but malicious code executing in the privileged deploy job can still request and use the token during its lifetime. Preserve the trust split established in CI/CD.

### 2.5 Address planning and subnetting

Plan globally before locally. Reserve non-overlapping blocks by environment and region, then allocate subnets by trust/function with growth. `10.42.0.0/16` might reserve `10.42.0.0/20` for shared regional services, `10.42.16.0/20` for production, and `10.42.32.0/20` for nonproduction. Within production, `/24` subnets can separate ingress, applications, data and private endpoints. Do not size only for today's pods: Kubernetes nodes/pods, private endpoints, upgrades and blue/green capacity consume addresses.

CIDR containment is bit-based, not textual. `10.42.1.0/24` contains `10.42.1.18`, not `10.42.10.18`. Python's `ipaddress` module in the lab performs exact membership. Overlapping address space prevents simple peering/routing and makes mergers/hybrid connectivity costly; NAT can work around overlap but adds operational complexity and obscures original identities.

### 2.6 Routes, NAT and asymmetry

Azure creates system routes. User-defined routes can send `0.0.0.0/0` to Azure Firewall or a network virtual appliance for controlled egress. A route permits reachability; an NSG/firewall permits or denies traffic. NAT translates addresses but is not authorization. An outbound NAT Gateway provides stable source addresses and port scale; inbound exposure needs a separate load balancer/application gateway/front door design.

Stateful devices expect return traffic through compatible paths. Asymmetric routing—request through firewall, response directly—can cause drops and confusing intermittent failures. Inspect effective routes on both sides, next hops and source translation. Longest-prefix match generally wins among routes; more specific `/24` beats `/16`, subject to Azure route-source priority rules.

### 2.7 NSGs and deny-by-default flow design

Describe each required flow as source, destination, protocol, port and business purpose. Assign explicit priority; lower NSG priority numbers are evaluated first. Keep rules specific and name them by intent. The lab permits application subnet `10.42.2.0/24` to data subnet `10.42.4.0/24` only on TCP 5432, while ingress subnet `10.42.1.0/24` can reach one private endpoint `10.42.3.4` only on TCP 443. Everything else is denied by its policy model.

Azure NSGs are stateful: an allowed outbound connection permits corresponding return traffic without a mirrored inbound rule. This does not authorize a new reverse-direction connection. Default NSG rules exist and service tags abstract platform address sets, so inspect effective rules rather than assuming the file's custom rules are the whole decision.

### 2.8 Hub-spoke and segmentation

A hub can centralize firewall, VPN/ExpressRoute, DNS resolver and shared operational services; spokes isolate workloads/subscriptions. VNet peering is not transitive: spoke A does not automatically reach spoke B through a peered hub. Configure routing/firewall deliberately. Centralization improves governance but creates throughput, cost and failure dependencies; zone redundancy, capacity and route testing matter.

Segment by trust and flow, not organizational fashion. Internet ingress terminates at an edge/WAF/load balancer, only the required port reaches application tier, only application identity/network reaches data, and egress is allowlisted/observed. Network boundaries contain lateral movement; workload identity and application authorization still protect each request.

### 2.9 Private endpoints and DNS

For Azure Storage with Private Link, create the private endpoint, approve/validate its connection to the intended resource, create/link the correct private DNS zone such as `privatelink.blob.core.windows.net`, and ensure clients using the normal storage FQDN resolve through the CNAME chain to the endpoint's private IP. Disable or restrict public network access after proving all callers have private resolution/routes.

Hybrid clients need conditional forwarding through Azure DNS Private Resolver or an appropriate DNS architecture. Linking a private zone to one VNet does not automatically serve every peered/on-prem network. Beware one private DNS zone containing records for services reached from networks where endpoints are absent; resolution can black-hole traffic.

Service endpoints do not put a private IP on the service. Microsoft documents that DNS stays public and enabling the endpoint changes service traffic source identity; existing public-IP firewall rules and open connections can be disrupted. Choose based on service support, exfiltration needs, topology, DNS complexity and cost—not the word “private.”

### 2.10 Ingress, TLS and egress

Public APIs usually need a deliberate edge: DDoS protection where warranted, WAF for HTTP threats, TLS policy/certificate lifecycle, rate limits and an application gateway/load balancer to healthy private backends. Layer 7 gateways understand HTTP routing and headers; layer 4 load balancers do not. End-to-end TLS may re-encrypt to the backend; document where plaintext can exist and how certificates rotate.

Egress is often ignored. A compromised service with unrestricted outbound access can exfiltrate data or download tools. Route egress through a controlled firewall/NAT, allow required destinations, use private endpoints for PaaS, and log DNS/flow/firewall decisions. FQDN allowlisting depends on DNS and changing provider endpoints; test update/package-repository failure modes.

### 2.11 Observability and troubleshooting sequence

For identity failures, capture correlation ID, principal object ID, tenant, token audience/issuer/expiry, requested operation and exact scope—without logging the token. Check data-plane versus management-plane role, inherited assignments, deny/condition and propagation. `401` usually means authentication/token failure; `403` means authenticated but unauthorized, though services vary.

For network failures, proceed layer by layer: name resolution → source/destination IP → route/next hop → NSG effective rules → firewall/WAF/load balancer → TLS/SNI/certificate → application listener/health → identity authorization. Test from the actual client subnet/identity. “Ping fails” proves little because ICMP may be unsupported while TCP 443 works.

### 2.12 Security, privacy, availability and cost boundaries

Flow logs, DNS logs and identity audit records can contain user/resource names, IPs and access patterns. Restrict access, minimize and set retention based on incident/regulatory need. Private endpoints, firewalls, gateways, resolvers, NAT and cross-zone/region traffic have hourly and data-processing costs; price the exact region/SKU before architecture approval. Removing public access can improve security and simultaneously break vendor callbacks, build agents or disaster recovery. Inventory callers and rehearse failover.

## 3. WORKED PROBLEMS

### Problem 1 — Calculate subnet capacity

**Statement.** A platform reserves `10.42.16.0/20`. How many `/24` subnets fit, and how many total IPv4 addresses does each contain?

**Solution.** Moving from `/20` to `/24` borrows four subnet bits, producing `2^4 = 16` subnets. Each `/24` leaves eight host bits, producing `2^8 = 256` total addresses. Do not report all 256 as usable Azure NIC addresses because Azure reserves addresses per subnet. Allocate growth rather than filling every block.

**Mistake caught:** confusing total mathematical addresses with usable platform capacity.

### Problem 2 — Find excessive RBAC scope

**Statement.** A claims API needs to read secrets from one Key Vault but has Contributor at subscription scope. Redesign.

**Solution.** Give its managed identity a suitable Key Vault secrets data-plane reader role at the vault (or narrower supported) scope. Remove Contributor. It does not need management-plane resource mutation. Validate read succeeds, secret write/delete fails, another vault fails and access is logged.

**Mistake caught:** using a broad management role for data access.

### Problem 3 — Diagnose a 403

**Statement.** An App Service managed identity can list a storage account in ARM but gets 403 reading a blob.

**Solution.** ARM list proves management-plane authorization, not blob data-plane permission. Confirm the token audience is Storage, principal object ID is correct, and grant the required Storage Blob Data role at the smallest container/account scope. Check storage firewall/private path separately. Retest after expected propagation with correlation logs.

**Mistake caught:** treating control-plane and data-plane access as identical.

### Problem 4 — Secure production federation

**Statement.** GitHub OIDC trusts any branch in `acme/payments` and the principal is Owner on the subscription.

**Solution.** Bind the federated subject to the protected production environment/reusable workflow, validate audience, grant only deployment actions on the production resource group or resource, and keep role-assignment write out. Require environment approval, pin workflow actions and allow OIDC only in the deploy job.

**Mistake caught:** assuming short-lived credentials are automatically least privilege.

### Problem 5 — Private endpoint that resolves publicly

**Statement.** Storage has a private endpoint `10.42.3.4`, but an on-prem host resolves the account to a public address and fails after public access is disabled.

**Solution.** Connectivity exists but DNS does not guide the client to it. Configure conditional forwarding for the relevant private-link zone through Azure DNS Private Resolver (or approved DNS chain), ensure zone/record/link correctness, then verify `nslookup` from on-prem returns `10.42.3.4`, route reaches it and TCP 443 succeeds.

**Mistake caught:** believing endpoint creation automatically configures every DNS domain.

### Problem 6 — Evaluate an NSG flow

**Statement.** App `10.42.2.9` may reach PostgreSQL `10.42.4.25:5432`; ingress `10.42.1.9` must not. Write and test the invariant.

**Solution.** Allow source `10.42.2.0/24`, destination `10.42.4.0/24`, TCP 5432 at a priority before broad deny. Do not allow VirtualNetwork-to-VirtualNetwork broadly if it defeats intent. The lab proves app is true and ingress false using exact CIDR membership.

**Mistake caught:** opening the database to the entire VNet for convenience.

### Problem 7 — Diagnose asymmetric routing

**Statement.** Requests from on-prem enter through a hub firewall, reach a spoke VM, but replies time out intermittently after a route change.

**Solution.** Inspect effective routes on VM subnet and on-prem path. If the spoke's more specific route returns directly through VPN/ExpressRoute instead of the stateful firewall, the firewall never sees the return. Align user-defined routes/propagation so both directions traverse compatible stateful hops; verify source NAT assumptions and connection logs.

**Mistake caught:** inspecting only forward reachability.

### Problem 8 — Service endpoint change outage

**Statement.** Enabling a Storage service endpoint breaks existing connections and IP firewall rules.

**Solution.** Microsoft documents that source addressing changes to private VNet addresses for service traffic and existing open TCP connections close during the switch. Pre-add subnet virtual-network rules, remove dependence on old public egress IP rules only after validation, schedule/retry safely, and monitor reconnection.

**Mistake caught:** treating a network-control change as metadata-only.

### Problem 9 — Design regulated three-tier access

**Statement.** Design identity/network boundaries for a public healthcare API, worker and database.

**Solution.** Edge WAF/gateway accepts TLS 443; app subnet accepts only gateway-to-app port; worker uses queue-triggered private access; data subnet/private endpoint accepts only app/worker required ports. Each workload gets distinct managed identity with only its data roles. Secrets use Key Vault private endpoint and scoped read. Controlled egress, private DNS, audit/flow logs with privacy retention, availability zones and tested break-glass/DR complete the design.

**Mistake caught:** using a shared identity and “private VNet” as the full threat model.

## 4. REAL-WORLD / APPLIED CONTEXT

### 4.1 Azure RBAC at resource scope

Microsoft's Azure RBAC documentation explicitly recommends assigning a managed identity at the storage-account scope rather than resource-group/subscription when only that account is needed. In a payments platform, separate identities might be `payment-api-mi` with queue send and tokenization access, `settlement-worker-mi` with queue receive and one database procedure, and `reconciliation-mi` with read-only report storage. Compromise of the public API then cannot inherit the settlement worker's privileges. Audit with immutable principal object IDs rather than mutable display names.

### 4.2 Private Link for regulated PaaS

An Azure Storage private endpoint places a private NIC in a chosen subnet. A realistic resolution chain is `records.blob.core.windows.net` → private-link alias → `10.42.3.4` for linked networks. The private endpoint must target the correct subresource (`blob` differs from `dfs`, `file`, etc.), its connection state must be approved, and public network access must be evaluated separately. Hybrid clients need resolver/forwarding. This pattern reduces public exposure but introduces IP consumption, DNS dependencies and per-endpoint/data-processing cost.

### 4.3 Executable dual-plane policy

The included standard-library Python lab models a small subset of real policy: two custom roles and two allowed network flows. Six tests prove positive and negative cases. On the recorded macOS/Python run, all six completed in under the unittest timer's 0.001-second resolution; that is only a deterministic correctness check, not an Azure latency benchmark. Real Azure authorization includes group inheritance, conditions, deny assignments, wildcard operations and service-specific logic, while NSGs include priorities/defaults/service tags. The lab exists to make the two-plane invariant executable, not replace cloud policy evaluation.

Run it from `lab/`:

```bash
python3 -m unittest -v test_policy.py
python3 -m py_compile policy.py test_policy.py
```

## 5. COMPARISON TABLE

| Workload identity | Credential lifecycle | Blast radius | Best use |
|---|---|---|---|
| System-assigned managed identity | Azure-managed; deleted with resource | one resource by design | App Service/VM/function tied to resource |
| User-assigned managed identity | Azure-managed separate resource | all attached workloads/roles | stable identity across replacement or deliberate sharing |
| OIDC federated service principal | short-lived token exchange; no stored cloud secret | claim rule plus assigned scope | external CI/CD or federated workload |
| Client secret | manually stored/rotated until expiry | principal roles for secret lifetime | legacy fallback only |
| Certificate credential | private key lifecycle, usually stronger than secret | principal roles for key lifetime | legacy non-federated automation with protected key |

| PaaS network control | Address seen by client | DNS behavior | Isolation/trade-off |
|---|---|---|---|
| Public endpoint + firewall | public | public record | simplest; public exposure constrained by firewall/identity |
| Service endpoint | service DNS remains public | public service IP | subnet identity/backbone route; service support and rules required |
| Private endpoint | private NIC IP in VNet | private-link DNS must be designed | private reachability per resource; cost/IP/DNS complexity |

| Traffic component | Decision layer | Stateful? | Does not prove |
|---|---|---|---|
| Route table | next hop/reachability | no connection authorization | identity or application permission |
| NSG | source/destination/protocol/port | yes | user/workload identity |
| Azure Firewall | centralized network/application policy | yes | business-level authorization |
| WAF | HTTP attack/rule inspection | connection-aware | backend data permission |
| Azure RBAC | principal/action/scope | authorization state | network reachability |

## 6. COMMON MISTAKES & MISCONCEPTIONS

1. **“Inside the VNet is trusted.”** A compromised workload can move laterally. Segment flows and require workload identity/application authorization.
2. **“Private endpoint disables public access.”** It adds a private path; explicitly configure the service's public access/firewall.
3. **“Private endpoint fixes DNS everywhere.”** Only correctly linked/forwarded clients resolve privately. Test each client network.
4. **“Service endpoint gives the service a private IP.”** Service DNS remains public; subnet identity/routing changes.
5. **“Contributor can read all service data.”** Management and data plane roles differ. Grant the appropriate data role.
6. **Subscription-scope application roles.** A compromised app reaches unrelated resources. Assign at the smallest resource scope.
7. **Owner for deployment convenience.** It permits access administration. Define a deployment role without role-assignment write.
8. **One managed identity for every service.** Roles union and attribution degrade. Separate unrelated trust domains.
9. **User-assigned is always better.** Reuse can enlarge blast radius; choose based on lifecycle and trust.
10. **OIDC equals secure.** A wildcard subject or broad Azure role remains dangerous. Constrain claims and role/scope.
11. **Logging access tokens.** Tokens are credentials. Log correlation/claims metadata, never the raw token.
12. **Text-prefix scope check.** `/prod` must not match `/production`. Parse hierarchy or enforce delimiter boundary.
13. **CIDR by visual prefix.** `10.42.1.0/24` excludes `10.42.10.1`. Use bit-aware tooling.
14. **Counting all addresses as usable.** Cloud platforms reserve subnet addresses. Use provider capacity rules.
15. **Overlapping VNets.** Peering/hybrid routing becomes ambiguous. Allocate centrally with future acquisitions/regions.
16. **NSG `VirtualNetwork` broadly allowed.** It may defeat tier isolation. Inspect defaults and effective rules.
17. **Mirroring stateful return rules.** Return traffic for an allowed connection is already tracked; reverse new connections are distinct.
18. **NAT as firewall.** Translation does not express principal or application authorization.
19. **Ignoring egress.** A breach exfiltrates freely. Route, restrict and observe outbound flows.
20. **Only checking forward routes.** Stateful devices fail under asymmetric return. Inspect both paths.
21. **Ping as universal test.** ICMP support/policy differs. Test the actual DNS/TCP/TLS/application flow.
22. **Deleting a failing identity assignment immediately.** Capture principal, scope, action and correlation evidence first; propagation or wrong object ID may be the cause.
23. **Disabling public access without caller inventory.** CI, vendor callbacks or DR can fail. Migrate and verify every caller.
24. **Unlimited diagnostic retention.** Flow/identity logs can be sensitive and costly. Apply access and retention policy.

## 7. CHEAT SHEET — REVIEW ONLY, NOT A SUBSTITUTE FOR THE SECTIONS ABOVE

Identity decision: `principal + requested action/dataAction + exact target scope + inherited assignments − exclusions − deny/condition`.

Network decision: `DNS → source/destination → route/next hop → NSG → firewall/LB/WAF → TLS → listener → identity/application authorization`.

- Humans: MFA + just-in-time privilege. Azure workloads: managed identity. External CI: narrow OIDC federation.
- Prefer resource scope; separate management-plane and data-plane roles.
- `/20` contains 16 `/24`s; `/24` contains 256 total IPv4 addresses before Azure reservations.
- Route controls path; NSG/firewall controls flow; RBAC controls operation.
- Private endpoint = private NIC + connection + DNS + routes + service public-access decision.
- Service endpoint keeps public DNS/service address and identifies allowed subnet to supported service.
- NSG rules are priority ordered and stateful; inspect defaults/effective rules.
- Hub-spoke peering is not transitive.
- Deny by default, allow documented flow, observe identity and network decisions.

## 8. PRACTICE SET FOR SELF-TEST

1. A `/18` regional block is divided into `/23` workload blocks. How many blocks and total addresses per block result?
2. Design identities/roles/scopes for API read, worker write and auditor read across one Key Vault and two Storage containers.
3. Diagnose why subscription Contributor can create a Key Vault but cannot read a secret.
4. Write positive and negative authorization tests for a production deployment custom role.
5. Design GitHub-to-Azure OIDC federation that only a protected production environment may use.
6. Plan non-overlapping hub/spoke CIDRs for two regions, production/nonproduction and future 2× growth from `10.64.0.0/10`.
7. Trace `10.42.2.8` to private PostgreSQL `10.42.4.25:5432` through DNS, routes, NSGs, TLS and identity.
8. Compare service endpoint and private endpoint for Azure Storage used from Azure plus on-premises.
9. A private endpoint works from hub but not a peered spoke. Give a prioritized diagnostic plan.
10. Threat-model a healthcare API with public ingress, third-party callbacks and restricted database; include availability/cost/privacy trade-offs.

## 9. CURATED RESOURCES

1. Microsoft Learn, [Understand Azure role assignments](https://learn.microsoft.com/en-us/azure/role-based-access-control/role-assignments). Exact principal/role/scope model and smallest-scope guidance.
2. Microsoft Learn, [Understand scope for Azure RBAC](https://learn.microsoft.com/en-us/azure/role-based-access-control/scope-overview). Management-group-to-resource inheritance and scope syntax.
3. Microsoft Learn, *Azure custom roles* and *Azure resource provider operations*. Exact `actions`, `dataActions`, exclusions and operation discovery for testable roles.
4. Microsoft Learn, *What are managed identities for Azure resources?* Lifecycle and system-assigned versus user-assigned behavior.
5. Microsoft Learn, *Workload identity federation* and *Use GitHub Actions to connect to Azure*. Current token-exchange/federated credential implementation.
6. Microsoft Learn, [Azure virtual network service endpoints](https://learn.microsoft.com/en-us/azure/virtual-network/virtual-network-service-endpoints-overview). Exact source-IP, DNS, connection-disruption and support boundaries.
7. Microsoft Learn, *What is a private endpoint?* Private NIC/subresource/approval semantics and limitations.
8. Microsoft Learn, *Azure Private Endpoint DNS configuration*. Canonical private-link zone names, zone links and DNS scenarios.
9. Microsoft Learn, *Network security groups*. Priority, default rules, service tags, stateful behavior and effective rules.
10. Microsoft Azure Well-Architected Framework, [Segmentation strategy](https://learn.microsoft.com/en-us/azure/well-architected/security/segmentation) and *Networking and connectivity*. Zero Trust, east–west/north–south and defense-in-depth design.
11. NIST SP 800-207, *Zero Trust Architecture*, Scott Rose et al. Canonical policy decision/enforcement and no-implicit-trust architecture.
12. RFC 4632, *Classless Inter-domain Routing (CIDR)*, Fuller and Li. Prefix/address aggregation foundations beyond Azure tooling.

## 10. RELATED TOPICS BRIDGE

### Before

1. **Containers:** workload identity and exposed ports attach security to an immutable runtime unit.
2. **Kubernetes:** service accounts, NetworkPolicy, Services/Ingress and cluster egress map onto cloud identity/network controls.
3. **Terraform:** roles, VNets, endpoints, DNS and routes need reviewable declarative ownership.
4. **CI/CD Supply Chain:** OIDC claims and scoped deployment roles replace stored production credentials.

### After

1. **SLIs, SLOs and Error Budgets:** gateways, DNS, identity and private endpoints become availability dependencies to measure.
2. **Metrics, Logs and Traces:** identity audit, flow, DNS and firewall telemetry enable diagnosis.
3. **Incident Response:** credential revocation and network containment are core response actions.
4. **Capacity and Disaster Recovery:** IP space, NAT ports, firewall throughput, DNS and regional failover need explicit capacity.
5. **Regulated System Design:** data-plane separation, private access, audit and retention support healthcare/fintech controls.

---ANSWER KEY BELOW---

1. `/18` to `/23` borrows five bits, so `2^5 = 32` blocks. `/23` leaves nine host bits, so 512 total addresses per block before Azure reservations.
2. Use three managed identities. API gets only blob/container read and vault secret read at exact resources. Worker gets only destination container write (plus minimum read if protocol needs it) and its own secret. Auditor group/identity gets read on the two containers, not secret values unless explicitly required. No management mutation; test cross-container, write/delete and role-assignment denial.
3. Contributor is a management-plane role and can configure the vault, but secret retrieval is a data-plane operation. Verify vault permission model, token audience and principal, then grant the minimum Key Vault data role at vault/appropriate scope; also satisfy firewall/private endpoint path.
4. Positive tests: read/update intended application resource and slot at production resource scope. Negative: role assignment write, resource-group delete, Key Vault secret read, unrelated resource group, network-policy change and deployment from wrong federated subject. Treat unexpected allowed action as failure.
5. Entra federated credential trusts GitHub's issuer and intended Azure audience with subject tied to exact organization/repository and `production` environment (or exact reusable workflow claims). GitHub environment has branch protection/reviewers. Only deploy job gets `id-token: write`; Azure principal has custom deploy role at target resource/resource group, no access administration.
6. One valid plan: reserve `/12` per region inside `/10`, then `/14` for prod and `/14` for nonprod within each, leaving the remainder for growth/shared/DR; subdivide spokes systematically. The key proof is no overlap across connected/hybrid ranges and documented reserve of at least current allocation for 2× growth; validate with an IPAM tool rather than hand text matching.
7. Resolve database name to intended private `10.42.4.25`; verify source subnet route and return route; allow `10.42.2.0/24 → 10.42.4.0/24 TCP 5432` and no broader source; inspect firewall; validate TLS hostname/CA and server listener; then authenticate distinct workload identity/database user and authorize only required schema/operations. Log correlation without secrets.
8. Service endpoint is simpler for supported Azure-origin subnet access, keeps public DNS/service address and secures service firewall to subnet; hybrid identity/topology and exfiltration controls are less direct. Private endpoint gives the resource/subresource a private VNet address usable through routed hybrid connectivity but requires private DNS forwarding, IPs, endpoint approval and added cost. For regulated Azure+on-prem, private endpoint is usually favored when service/support/DR DNS are validated; quantify exact SKU/traffic cost.
9. Check spoke DNS result first; a zone linked only to hub may not resolve as expected through custom DNS. Then VNet peering flags, UDR both directions, NSG effective rules on client/endpoint subnet, firewall transit and endpoint connection state. Test TCP 443 and TLS SNI using the service FQDN, not raw-IP ping. Confirm public access state only after private path works.
10. Internet → DDoS/WAF/gateway TLS 443 → private app subnet; validate callbacks with mTLS/signatures and narrow routes/IP only when stable; app managed identity and exact DB data role; DB/private endpoints with private DNS and public access off; controlled egress; separate admin path/JIT access; zone-redundant edge/app/data and rehearsed regional DNS/failover. Log WAF/identity/flow decisions with PHI-minimizing retention. Quantify WAF/firewall/endpoint/NAT/log/cross-region cost and identify callbacks/private DNS/firewall as availability dependencies.
