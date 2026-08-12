# Git and Collaborative Version Control from Scratch

Parent subject: `05-cloud-platform`
Study time: 3–4 hours
Target: senior backend / AI platform / MLOps interviews

## 1. FOUNDATIONS

### The problem version control solves

Software changes continuously. Engineers need to know what changed, why, by whom, which version runs in production, how parallel work combines, and how to recover when a change is wrong. Copying folders such as `app-final-v7-really-final` cannot provide reliable identity, ancestry, atomic change sets, review, or collaboration.

A **version control system** records versions and relationships among them. Early systems such as SCCS and RCS tracked individual files; CVS and Subversion centralized project history; distributed systems such as Git give every clone a complete repository history and allow local commits and branching.

Linus Torvalds created Git in 2005 for Linux kernel development. Git prioritizes distributed work, speed, content integrity, branching, and merging. It models history as an immutable directed acyclic graph (DAG) of objects addressed by cryptographic hashes. Learning that model makes commands predictable.

### Repository, working tree, index, and object database

A **repository** contains Git metadata and objects, normally in `.git`. The **working tree** is the checked-out file state you edit. The **index** or staging area is the proposed snapshot for the next commit. A **commit** records a complete project snapshot plus metadata and parent commit references.

Three comparisons explain common status output:

1. HEAD commit versus index: what is staged.
2. Index versus working tree: what is modified but unstaged.
3. Working tree versus untracked files: files Git has not been asked to include.

`git add` does not merely “start tracking a file”; it copies the selected current content into the index. If you edit again after adding, staged and unstaged versions can coexist. `git commit` records the index, not every working-tree change.

### Git objects and identity

Core objects are:

- **blob:** file contents, not filename;
- **tree:** directory-like mapping of names/modes to blobs or subtrees;
- **commit:** root tree, parent commit(s), author, committer, timestamp, message;
- **annotated tag:** named signed/described reference to another object.

An object ID hashes object type, size, and content. Git historically uses SHA-1 repositories and supports SHA-256-format repositories, with transition compatibility considerations. Hashes provide content identity and corruption detection; ordinary commit hashes are not digital signatures or proof of author identity. Signed commits/tags add cryptographic attestation tied to trusted key verification.

A commit is a snapshot, but storage is efficient: unchanged content reuses the same objects, and packfiles delta-compress objects. Thinking “snapshot DAG” is more accurate than “list of diffs”; diffs are computed between snapshots.

### References, HEAD, branches, and tags

A **reference** is a movable name pointing to an object ID. A branch such as `main` points to its latest commit. `HEAD` usually symbolically points to the current branch. Making a commit creates a commit whose parent is current HEAD and advances the branch.

A **detached HEAD** points directly to a commit instead of a branch. Commits made there are valid but can become hard to find after switching unless you create a branch/tag. A **tag** marks an object, commonly a release. Lightweight tags are refs; annotated tags are objects with metadata and optional signatures. Release automation should prefer protected, annotated/signed tags or immutable provenance according to policy.

### The commit graph

If A is followed by B and C, the graph is `A <- B <- C`. A feature branch from B creates D and E while main creates C:

```text
      D---E  feature
     /
A---B---C    main
```

A merge can create M with parents C and E. History records both lines. A rebase instead copies the logical changes D/E onto C, producing new commits D′/E′ with new IDs. Rebasing rewrites ancestry; merging preserves it. Neither is morally superior—the team chooses based on shared-history safety and desired review/release trace.

### Remotes and distributed collaboration

A **remote** is a named repository URL, often `origin`. `git clone` copies objects and creates remote-tracking references such as `origin/main`. `git fetch` downloads objects and updates remote-tracking refs without altering your branch/working tree. `git pull` combines fetch with a configured integration action, usually merge or rebase. `git push` asks the remote to update refs after sending missing objects.

Your local `main`, `origin/main`, and the server's `main` are distinct refs that can temporarily differ. This distinction explains “behind/ahead” states and why fetch is safe inspection.

### Merges and conflicts

A merge finds a common ancestor and combines changes from two tips. If one branch is an ancestor of the other, Git can **fast-forward** the ref without a merge commit. A three-way merge compares both tips with the merge base. A **conflict** occurs when Git cannot choose a correct combined result, such as competing changes to overlapping lines or delete/modify conflict.

Conflict markers show ours and theirs in a particular command context, but resolving means constructing the correct domain result, not selecting one side mechanically. Compile/test after resolution. The index records resolution stages until files are added.

### Rebase, cherry-pick, revert, reset, and restore

**Rebase** replays commits onto a new base, creating new IDs. Do not rebase history other people consume unless coordinated; their ancestry diverges.

**Cherry-pick** applies the change introduced by selected commit(s) as new commit(s) on current history. It duplicates logical change and can complicate later merges, but is useful for controlled backports.

**Revert** creates a new commit that inverses an earlier commit. It preserves shared history and is the normal safe rollback after push. Reverting a merge needs choosing the mainline parent and has future merge implications.

**Reset** moves a branch/HEAD and optionally index/working tree. `--soft` keeps index/working content; default `--mixed` resets index; `--hard` overwrites tracked working content. Hard reset is destructive to uncommitted tracked changes and must not be casual.

**Restore** copies content from index/commit into working tree and can unstage with `--staged`. Always inspect `status` and exact paths before overwriting.

### Collaboration, review, and releases

A pull/merge request is hosting-platform workflow, not a core Git object. It associates a branch difference with discussion, approvals, checks, ownership, and merge policy. A strong change is small, coherent, tested, and documented. Commit messages explain intent and constraints, not restate filenames.

Protected branches can require reviews, status checks, signed commits, linear history, and restricted force pushes. CI should build the reviewed commit/merge result and deployment should record immutable commit and artifact digest. Rebuilding the same branch name later may produce different bytes if dependencies/build environment float.

### Security and secrets

Git history is durable and replicated. Deleting a secret from the latest file does not remove it from old commits, clones, caches, CI logs, forks, or artifacts. Treat exposure as credential compromise: rotate/revoke first, audit use, then perform coordinated history rewriting only when necessary. Secret scanners reduce risk but are not perfect.

`.gitignore` prevents untracked matching paths from being added by ordinary commands; it does not untrack existing files or provide secrecy. Use environment-specific secret managers and commit templates/examples without real values.

## 2. CORE MECHANICS

### 2.1 Configure identity and create a repository

```bash
git config --global user.name "Nirantar Kulkarni"
git config --global user.email "verified-address@example.com"
mkdir claims-service && cd claims-service
git init
```

Identity metadata is not authentication. Repository-scoped config can override global. Inspect with `git config --show-origin --list`. Use a verified organizational address/signing policy when required.

Create README, inspect, stage, commit:

```bash
git status
git add README.md
git diff --cached
git commit -m "Document local development entry point"
```

Review staged diff before commit to avoid accidental secrets, debug files, or unrelated changes.

### 2.2 Read status and diffs

`git status --short` uses two columns: index and working tree. `M ` means staged modification; ` M` unstaged; `MM` both; `??` untracked. `git diff` shows working tree versus index. `git diff --cached` shows index versus HEAD. `git diff HEAD` shows total tracked difference.

Partial staging with `git add -p` lets one file's independent hunks enter different commits. After staging, rerun tests against actual working tree and inspect staged content; build systems generally see working tree, which may include unstaged edits absent from commit.

### 2.3 Branch and merge

```bash
git switch -c feature/idempotency
# edit, test
git add src test
git commit -m "Enforce request fingerprint for idempotent creation"
git switch main
git merge --no-ff feature/idempotency
```

`--no-ff` creates a merge commit even when fast-forward is possible, preserving branch grouping; teams may instead prefer squash or rebase merge. Squash merges produce one new commit and do not record feature commits as ancestors.

### 2.4 Resolve a conflict

After `git merge feature`, inspect `git status` and `git diff`. Edit markers into intended combined content, run focused and full relevant tests, `git add` resolved paths, then `git commit`/`git merge --continue`. To abandon before completion, `git merge --abort` when supported/state permits.

Do not use broad “ours” for generated lockfiles/config without understanding. Regenerate artifacts from the chosen source inputs when appropriate.

### 2.5 Rebase a private branch

```bash
git fetch origin
git switch feature/idempotency
git rebase origin/main
```

For each conflict: resolve, stage, `git rebase --continue`; use `--abort` to return. Commits are copied with new parents/IDs. If the old branch was pushed and rewriting is authorized, `git push --force-with-lease` checks that the remote ref still matches expected knowledge, unlike blind `--force`. It can still overwrite others if assumptions/workflow are wrong; protected branches should prevent it.

### 2.6 Fetch and integrate deliberately

```bash
git fetch --prune origin
git log --oneline --graph --decorate --all -20
git diff main..origin/main
```

Then choose merge/rebase/fast-forward. `git pull --ff-only` is a useful default when automatic merge commits are unwanted; it refuses divergence. `--prune` removes stale remote-tracking refs, not local branches or remote objects immediately.

### 2.7 Undo safely

Unstaged mistaken edit: inspect then `git restore -- path` (overwrites it). Unstage while keeping edit: `git restore --staged path`. Wrong local last commit not shared: `git commit --amend` or carefully reset. Wrong pushed commit: `git revert <id>` and review/test the inverse.

Recover “lost” local commit:

```bash
git reflog
git show <old-id>
git branch recovery/<description> <old-id>
```

The **reflog** records local ref movements for a retention period. It is not pushed/shared and unreachable objects are eventually garbage-collected. Recover promptly.

### 2.8 Ignore generated/local files

Example `.gitignore`:

```gitignore
.idea/
build/
target/
.env
*.log
```

Negation and directory patterns have rules; verify with `git check-ignore -v path`. If `.env` is already tracked, adding ignore does nothing: remove it from index in a reviewed change, keep local file, and rotate any committed secret.

Do commit dependency lockfiles when the ecosystem/project policy uses them for reproducibility. Do not ignore every generated file blindly; generated API clients or migration checksums may be intentional source artifacts.

### 2.9 Tags and release identity

```bash
git tag -s v1.4.0 -m "claims-service 1.4.0" <commit>
git push origin v1.4.0
git verify-tag v1.4.0
```

Tag signing requires configured key/trust. A tag points to source identity; also record artifact digest, SBOM, builder/provenance, tests, and deployment. Never move a published release tag silently—create a new version.

### 2.10 Repository hygiene and large files

Git is optimized for source, not frequently changing large binaries/datasets/models. Git LFS stores pointer files in Git and objects in separate storage, but availability, retention, credentials, quotas, and reproducibility still need management. ML datasets/models belong in versioned artifact/object stores with checksums and lineage, while Git records manifests/code.

Use `git fsck` for integrity checks and `git gc`/maintenance according to normal tooling, not as a secret-removal strategy. Avoid committing build outputs, caches, credentials, and personal IDE state unless policy explicitly requires them.

## 3. WORKED PROBLEMS

### Problem 1 — Staged versus unstaged (easy)

You edit A, `git add A`, then edit A again. What will commit contain?

**Solution.** The version staged at add time. Status shows A both staged and unstaged (`MM`). Review `git diff --cached` and `git diff` separately.

**Trap:** assuming commit reads latest working file automatically.

### Problem 2 — Branch meaning (easy)

Is a Git branch a copied directory?

**Solution.** No. It is a movable reference to a commit. Switching updates index/working tree to a snapshot while objects are shared.

**Trap:** estimating branch storage as a full project copy.

### Problem 3 — Fetch versus pull (easy)

You want to inspect remote changes without modifying working branch.

**Solution.** `git fetch`, then inspect `origin/main` and diffs/log. Pull also integrates according to configuration.

**Trap:** using pull as a harmless download-only command.

### Problem 4 — Pushed defect (medium)

Commit X is on shared main and caused a production bug. Reset or revert?

**Solution.** Revert X (or deploy a proven previous artifact as immediate mitigation, then record correction). Revert adds history and does not rewrite shared ancestry. Test the inverse, especially when later commits depend on X.

**Trap:** force-pushing main backward.

### Problem 5 — Rebase IDs (medium)

Why do commit IDs change after rebase when file changes appear identical?

**Solution.** Commit hash includes parent and metadata/tree. Rebase changes parent and creates new commit objects.

**Trap:** assuming hash identifies only patch content.

### Problem 6 — Conflict resolution (medium)

Both branches add different enum cases to the same line. Pick ours or theirs?

**Solution.** Likely combine both, then validate enum semantics, switch exhaustiveness, serialization compatibility, and tests. Conflict is a request for domain judgment.

**Trap:** mechanically accepting one side and losing valid change.

### Problem 7 — Secret committed (hard)

An Azure credential appears in a commit pushed publicly for ten minutes.

**Solution.** Revoke/rotate immediately, inspect audit use, remove from code/current branch, notify security, scrub CI/log/artifacts as governed, then coordinate history rewrite if valuable. Assume clones/caches exist; history rewrite does not make old secret safe.

**Trap:** only force-pushing a deletion.

### Problem 8 — Force-with-lease (hard)

Why is it safer than `--force`, and is it risk-free?

**Solution.** It refuses update if remote ref differs from expected observed value, protecting unseen updates. It is not risk-free: stale tracking/explicit expectations and team misunderstandings can still overwrite history; authorization and branch protection matter.

**Trap:** treating it as universally safe on shared branches.

### Problem 9 — Release reproducibility (hard)

Is commit hash enough to reproduce a container byte-for-byte?

**Solution.** No. Base images, dependencies, build tools, timestamps, network inputs, platform, and secrets can vary. Pin dependencies/base digest, use controlled hermetic/reproducible build, record provenance/SBOM and artifact digest, and verify.

**Trap:** equating source identity with artifact identity.

## 4. REAL-WORLD / APPLIED CONTEXT

### Linux kernel workflow

Git was created for a highly distributed kernel workflow. Contributors exchange commits/patch series, maintainers merge signed subsystem histories, and tags identify releases. Trust is social plus cryptographic and review-based; hash identity alone does not assert code safety.

### Trunk-based development

Trunk-based teams integrate small changes frequently into a protected mainline, often hiding incomplete functionality behind feature flags. Short-lived branches reduce merge divergence and support continuous delivery, but require strong tests, review, backward-compatible database/API evolution, and flag cleanup.

### GitOps

GitOps workflows store desired declarative platform state in Git and controllers reconcile environments. Git gives reviewed history and identity, but secrets, runtime state, emergency changes, drift, promotion, and controller credentials still require explicit design. A commit merge is not proof a rollout succeeded.

## 5. COMPARISON TABLE

| Operation | History effect | Best use | Risk |
|---|---|---|---|
| Merge | Adds merge commit or fast-forwards; preserves ancestry | Shared divergent branches | Noisy graph if indiscriminate |
| Rebase | Copies commits to new parent/IDs | Clean up private branch | Rewrites consumed history |
| Squash merge | One new aggregate commit | PR as one logical change | Loses commit ancestry/granular revert |
| Cherry-pick | Copies selected change | Backport/hotfix | Duplicate logical commits |
| Revert | New inverse commit | Undo shared history | Conflicts/dependencies; merge reverts nuanced |
| Reset soft | Moves ref, retains staged/working | Repair private local history | Dangerous if shared ref moved |
| Reset hard | Moves ref and overwrites tracked state | Explicit disposable local cleanup | Loses uncommitted tracked work |
| Fetch | Updates remote-tracking refs | Inspect safely | Does not integrate local branch |
| Pull | Fetch + integrate | Deliberate configured workflow | Surprise merges/rebases |

## 6. COMMON MISTAKES & MISCONCEPTIONS

1. **Git stores only diffs.** Logical model is content-addressed snapshots/graph.
2. **Add means include future edits.** It stages current content.
3. **Commit includes all files.** It records index only.
4. **Branch is a folder copy.** It is a ref.
5. **Hash proves author identity.** Signature/trust is separate.
6. **Pull only downloads.** It fetches and integrates.
7. **Rebase moves commits unchanged.** It creates new objects/IDs.
8. **Conflict means choose ours/theirs.** Correct result may combine or redesign.
9. **Reset and revert are interchangeable.** Reset moves history; revert adds inverse history.
10. **`.gitignore` removes tracked secrets.** It affects untracked inclusion only.
11. **Deleting a secret from main removes exposure.** History/clones/logs persist; rotate.
12. **Commit hash reproduces an artifact.** Inputs/environment must also be pinned/provenanced.

## 7. CHEAT SHEET — REVIEW ONLY

Review only; not a substitute for the lesson.

- Working tree = edits; index = next snapshot; HEAD = current commit/ref.
- `diff`: working vs index; `diff --cached`: index vs HEAD.
- Commit = tree + parent(s) + metadata; branch = movable ref.
- Fetch downloads/updates remote refs; pull also integrates.
- Merge preserves ancestry; rebase rewrites copied ancestry.
- Revert shared mistake; reset only with explicit local/history intent.
- Reflog can recover recent local ref movements.
- `force-with-lease` is safer, not harmless.
- `.gitignore` is not secret protection and does not untrack.
- Release identity needs source commit + immutable artifact digest + provenance.
- Inspect status/diff and test before every commit/merge/revert.

## 8. PRACTICE SET FOR SELF-TEST

1. Explain `MM`, ` M`, `M `, and `??` in short status.
2. Name the four core Git object types.
3. Draw a branch diverging after B and merging after two commits on each side.
4. Explain why a fast-forward has no merge commit.
5. Choose fetch, pull, or clone to inspect new upstream commits in an existing repository.
6. Recover a commit lost after an accidental local reset.
7. Choose revert or reset for a defect already used by teammates.
8. Explain the safety check in force-with-lease.
9. State response to a committed database password.
10. List four non-source inputs needed for reproducible container output.

## 9. CURATED RESOURCES

- Scott Chacon and Ben Straub, *Pro Git*, 2nd ed., Chapters 1–3, 6–7, and 10 — complete free reference from basics through internals, remotes, workflows, signing, and object model.
- Git official reference documentation: `gitglossary`, `gitrevisions`, `gitrepository-layout`, `git-merge`, `git-rebase`, `git-reset`, `git-revert`, and `git-reflog` — authoritative semantics and edge cases.
- Git project, “Git User's Manual,” sections on object database, history, merging, recovery, and sharing — coherent primary workflow/internals explanation.
- Atlassian, “A successful Git branching model” contrasted with trunk-based development literature — useful historical branch model; evaluate against modern continuous delivery rather than copying blindly.
- Paul Hammant, “Trunk Based Development” — concrete short-lived branch/mainline practices and scaled variants.
- SLSA specification, “Provenance” — explains why source commit alone is insufficient for trusted artifact identity.
- GitHub documentation, “About protected branches,” “About pull request reviews,” and “Managing commit signature verification” — hosting-specific enforcement beyond core Git.

## 10. RELATED TOPICS BRIDGE

### Before

1. **Linux and Shell:** provides files, processes, commands, quoting, permissions, and exit status.
2. **Programming/Testing Foundations:** enables coherent changes and verification.

### After

1. **Cloud Computing Foundations:** provides the target environments and shared responsibility.
2. **Containers:** builds immutable artifacts from versioned source.
3. **Terraform:** versions declarative infrastructure and state migrations.
4. **CI/CD Supply Chain:** turns commits into reviewed, attested, deployed artifacts.
5. **Data Migrations:** coordinates compatible code/schema history and rollback-forward plans.

---ANSWER KEY BELOW---

1. Both staged+unstaged modification; unstaged only; staged only; untracked.
2. Blob, tree, commit, annotated tag.
3. Any correct DAG with common B, two branch paths, and merge commit with two parents.
4. Current tip is an ancestor of incoming tip, so moving the branch ref represents integration without combining divergent histories.
5. Fetch.
6. Inspect `git reflog`, verify old ID with `show`, create a recovery branch at it.
7. Revert, preserving shared ancestry.
8. Remote ref must match expected value, rejecting unseen ref movement.
9. Rotate/revoke immediately, audit, remove current use, coordinate cleanup/history rewrite as needed; assume copied.
10. Base image digest, dependency lock/artifacts, compiler/build tool version, platform/architecture, timestamps/environment/network inputs (any four).
