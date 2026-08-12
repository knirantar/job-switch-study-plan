# Linux, Shell, Files, and Processes from Scratch

Parent subject: `05-cloud-platform`
Study time: 3–4 hours
Target: senior backend / AI platform / MLOps interviews

## 1. FOUNDATIONS

### Why Linux is the platform foundation

Most cloud servers, containers, Kubernetes nodes, CI runners, and ML training/inference environments use Linux. Even when a managed service hides the operating system, Linux concepts explain process isolation, files, permissions, sockets, signals, resource limits, logs, and failure diagnosis.

An **operating system** mediates applications and hardware. Its **kernel** manages CPU scheduling, virtual memory, filesystems, devices, networking, and protection. User-space programs request kernel services through system calls. A Linux distribution combines the Linux kernel with libraries, package management, startup/service management, shells, and applications.

Unix developed around composable tools, hierarchical files, processes, users, and text streams. Linux reimplemented Unix-like semantics as free software. The design principle “do one thing and compose” appears in pipelines, but production engineering also requires structured formats, bounded output, error handling, and secure quoting.

### Terminal, shell, command, and process

A **terminal** is the interface carrying input/output. A **shell** such as `bash` or `zsh` parses command language, expands variables/globs, sets up redirection/pipelines, and launches programs. A **command** may be a shell builtin, executable file, function, or alias. A **process** is a running program instance with a process ID (PID), parent PID, credentials, memory, open file descriptors, environment, and scheduling state.

The shell is not merely a place to type program names. Characters such as spaces, quotes, `$`, `*`, `?`, `|`, `>`, `<`, `;`, `&`, and parentheses have syntax. Unquoted data can become multiple arguments, wildcard matches, or executable substitutions. Never concatenate untrusted input into shell code.

### Filesystem hierarchy and paths

Linux presents a single rooted hierarchy `/`. An **absolute path** begins at root; a **relative path** begins at the current working directory. `.` means current directory and `..` parent. Names beginning with `.` are hidden by convention, not security.

Common directories:

- `/etc`: host configuration;
- `/var`: changing state such as logs/cache/spool;
- `/tmp`: temporary files with special shared-directory rules;
- `/usr`: installed user-space programs/libraries/data;
- `/home`: ordinary user homes;
- `/proc`: virtual process/kernel information;
- `/dev`: device nodes;
- `/run`: volatile runtime state;
- `/opt`: optional application software.

A **mount** attaches a filesystem at a directory. A path can cross local disk, network filesystem, pseudo-filesystem, or container mount without application syntax changing. Disk capacity and inode exhaustion are distinct: millions of tiny files can exhaust inodes while bytes remain.

### Files, directories, links, and file descriptors

Unix treats many resources as byte streams accessed by **file descriptors**. Each process normally starts with descriptor 0 standard input, 1 standard output, and 2 standard error. A regular file stores bytes; a directory maps names to inode-like objects; a symbolic link stores another path; a hard link is another directory entry for the same inode within constraints.

Deleting a pathname unlinks a directory entry. If a process still has the file open, its storage remains until the final reference closes. This explains “disk full but log file was deleted”: the logging process still holds the deleted inode. Restart/reopen the writer after validating impact; do not blindly kill it.

### Users, groups, and permissions

Processes run with user and group identities. Basic mode bits grant read (`r`), write (`w`), and execute (`x`) to owner, group, and others. Numeric modes use 4,2,1: `750` means owner rwx (7), group r-x (5), others none (0).

Directory permissions differ: read lists names, write creates/removes entries, execute traverses/accesses named entries. Writing a file depends on file permission; deleting it usually depends on parent directory permission. The sticky bit on shared `/tmp` restricts users from removing others' entries.

`root`/UID 0 has broad privilege. Use least privilege and `sudo` for audited, scoped elevation. Setuid, capabilities, ACLs, SELinux/AppArmor, namespaces, and container security add layers; mode bits alone are not the entire policy.

### Environment and exit status

An **environment variable** is a string inherited by child processes. `PATH` lists directories searched for executables. Environment variables are convenient configuration but visible to processes/tooling depending on platform; secrets require controlled injection and redaction.

Programs return an **exit status**: zero conventionally success, nonzero failure. Shell conditions use this status, not printed words. Pipelines by default may report only the last command's status in some shells; `set -o pipefail` makes earlier failures visible. Scripts should fail intentionally and avoid continuing after critical setup errors.

### Processes, signals, and services

Processes form a parent-child tree. A foreground process is associated with the terminal job; background processes continue without occupying foreground input. **Signals** asynchronously notify processes. `SIGTERM` requests graceful termination and can be handled; `SIGKILL` cannot be caught and immediately terminates; `SIGINT` commonly comes from Ctrl-C; `SIGHUP` often requests reload by convention.

A graceful service on SIGTERM stops accepting work, marks itself unready, drains bounded in-flight requests, flushes required state, and exits before an orchestrator grace period. SIGKILL prevents cleanup, so it is a last resort after diagnosing.

Modern Linux distributions commonly use systemd. A **unit** describes a service and dependencies; systemd starts, supervises, restarts according to policy, captures status, and integrates logs via journald. Containers often run one main foreground process supervised by the orchestrator instead.

### CPU, memory, storage, and load

CPU time can be user or system/kernel. **Load average** roughly counts runnable tasks plus tasks in uninterruptible sleep; it is not a CPU percentage. A load of 8 may be fine on 16 CPUs and severe on 2, and storage waits can raise load.

Virtual memory gives each process an address space. **RSS** is resident physical memory; virtual size includes mapped/reserved regions. The kernel uses unused RAM for page cache, so “free” being low is not automatically bad. Memory pressure can cause reclaim, swapping, latency, or the OOM killer.

Storage diagnosis distinguishes capacity, inodes, I/O latency, throughput, queue depth, and open-deleted files. Network diagnosis distinguishes DNS, route, port, TLS, and application. Resource metrics must be interpreted with workload and time.

## 2. CORE MECHANICS

### 2.1 Navigate and inspect safely

```bash
pwd
ls -la
find ./logs -maxdepth 1 -type f -name '*.log' -print
stat ./logs/service.log
du -sh ./logs
df -h .
df -i .
```

`du` sums reachable file usage; `df` reports filesystem allocation. Differences can come from open-deleted files, sparse files, snapshots, reserved blocks, or mount boundaries. Quote paths: `rm "$target"` avoids splitting spaces, but destructive operations still require resolved target validation.

### 2.2 Streams and redirection

```bash
command >output.txt       # replace stdout file
command >>output.txt      # append stdout
command 2>error.txt       # stderr only
producer | consumer      # producer stdout to consumer stdin
```

Redirection is set up by the shell before the program runs. `>` truncates immediately. Avoid redirecting into an important file without backup/atomic strategy. `2>&1` duplicates stderr to wherever stdout currently points; order matters.

Use pipelines for bounded transformations:

```bash
cut -d, -f3 requests.csv | sort | uniq -c | sort -nr | head
```

CSV with quoted commas needs a real CSV parser; text tools are not schema-aware. Do not parse JSON with fragile grep patterns—use `jq` when available.

### 2.3 Quoting and variables

Single quotes preserve literal characters. Double quotes allow parameter expansion but prevent word splitting/globbing of the result. Unquoted `$file` containing spaces becomes multiple arguments.

```bash
log_file='./run logs/app.log'
wc -l "$log_file"
```

Use `--` before untrusted filenames that may start with `-`: `rm -- "$file"` after validating exact scope. Never use `eval` for data. For multiple values use arrays in shells that support them rather than space-delimited strings.

### 2.4 Permissions and umask

`chmod 640 secret.conf` gives owner read/write, group read, others none. `chown app:app secret.conf` changes owner/group when authorized. `umask` removes permissions from creation defaults; a umask of `027` applied to a requested file mode 666 normally yields 640, and directory 777 yields 750.

Private keys commonly require 600; executable scripts often 750/755 depending sharing. Do not recursively `chmod 777` to solve a permission error. Determine the executing identity, required operation, path traversal, ownership, mount flags, ACL/MAC policy, and least privilege.

### 2.5 Processes and signals

```bash
ps -ef
ps -o pid,ppid,user,stat,%cpu,%mem,etime,cmd -p 1234
kill -TERM 1234
```

`kill` sends a signal; it does not necessarily kill. Wait and verify graceful exit before considering KILL. PID reuse means stale PID files are dangerous; service managers/pidfds improve identity. `pgrep` pattern matches can target unintended processes—resolve exact targets.

Process states include running/runnable, sleeping, stopped, zombie, and uninterruptible sleep. A zombie has exited but its parent has not collected status; it consumes a process-table entry, not ordinary running CPU/memory. Fix/restart the parent behavior rather than signaling the zombie.

### 2.6 Inspect resources

Common tools:

- `top`/`htop`: live CPU/memory/processes;
- `free -h`: memory categories;
- `vmstat 1`: run queue, memory, paging, CPU;
- `iostat -xz 1`: device utilization/latency if installed;
- `pidstat 1`: per-process CPU/I/O/context switches;
- `ss -lntp`: listening TCP sockets (permissions affect process info);
- `lsof -p PID`: open files/sockets;
- `lsof +L1`: open files with link count below one, often deleted;
- `dmesg`/journal: kernel events, access-controlled.

A single snapshot can mislead. Compare a time series with healthy baseline and request telemetry.

### 2.7 Logs and journald

```bash
systemctl status claims.service
journalctl -u claims.service --since '30 min ago'
journalctl -u claims.service -p warning..alert
```

Log timestamps, safe correlation IDs, severity, component, outcome, and durations. Avoid tokens, passwords, PAN/CVV, or sensitive patient contents. Rotation must coordinate rename/reopen or copy/truncate semantics. Applications should usually emit to stdout/stderr in containers and let the platform collect/rotate.

### 2.8 Packages and binaries

Package managers install signed repository artifacts and track dependencies: apt/dpkg on Debian/Ubuntu, dnf/rpm on Fedora/RHEL families. Update package indexes, pin/review versions according to reproducibility policy, verify repository trust, and understand that installing packages changes system state.

Use `command -v java`, `type java`, and `readlink` to discover executable resolution. `ldd` shows dynamic libraries but should not be run carelessly on untrusted binaries on all platforms; use safer inspection tools/policy. `file` identifies binary/script format.

### 2.9 Write a defensive small script

```bash
#!/usr/bin/env bash
set -Eeuo pipefail

if (( $# != 1 )); then
  echo "usage: $0 DIRECTORY" >&2
  exit 64
fi

target=$1
if [[ ! -d $target ]]; then
  echo "not a directory: $target" >&2
  exit 66
fi

find "$target" -maxdepth 1 -type f -name '*.log' -print0 |
  while IFS= read -r -d '' file; do
    printf '%s\t%s\n' "$(wc -c <"$file")" "$file"
  done
```

`-u` catches unset variables; `pipefail` catches pipeline failures; `-e` is useful but has nuanced exceptions and is not a substitute for explicit error handling. Null-delimited filenames handle spaces/newlines. The script reads only and validates input.

### 2.10 Diagnose a failing service

Order evidence:

1. What exact user-visible failure and start time?
2. Is the service process running/restarting, and what exit status?
3. What do bounded logs show around correlation/time?
4. Is it listening on expected address/port?
5. Can local protocol health succeed?
6. CPU, memory pressure/OOM, disk bytes/inodes/I/O, open files?
7. DNS/network/TLS/dependency health?
8. Recent deployment/config/package/secret changes?
9. Reproduce minimally, mitigate safely, preserve evidence, then fix/regress.

Do not begin by rebooting; that destroys volatile evidence and may temporarily hide the cause.

## 3. WORKED PROBLEMS

### Problem 1 — Permission mode (easy)

Interpret `-rwxr-x---`.

**Solution.** Regular file; owner read/write/execute (7), group read/execute (5), others none (0): mode 750.

**Trap:** treating the leading file-type character as a permission bit.

### Problem 2 — Exit status (easy)

What convention means success?

**Solution.** Zero. Nonzero indicates failure category chosen by program. Printed “OK” does not control shell success.

**Trap:** checking stdout text rather than status.

### Problem 3 — Disk discrepancy (easy)

`df` says full; `du` finds much less. Give a likely cause.

**Solution.** A process holds a deleted large file open, or snapshots/reserved blocks/mount visibility differ. Inspect `lsof +L1` and mount/snapshot context.

**Trap:** deleting more files without identifying retained storage.

### Problem 4 — Quoting (medium)

Why is `for f in $(find . -name '*.log')` unsafe?

**Solution.** Command-substitution output is split on whitespace and globbed; filenames with spaces/newlines break. Use `find ... -print0` with a null-delimited read loop or `-exec`.

**Trap:** assuming filenames cannot contain whitespace/newlines.

### Problem 5 — Load average (medium)

Load is 8 on a 16-vCPU host. Is CPU saturated?

**Solution.** Not enough information. Load includes runnable and some uninterruptible tasks; inspect CPU utilization, run queue, I/O wait, per-process state, and trend. Eight runnable tasks may fit 16 CPUs.

**Trap:** interpreting load as percentage.

### Problem 6 — Graceful shutdown (medium)

Kubernetes sends SIGTERM with 30-second grace. What should app do?

**Solution.** Become unready/stop new admission, drain bounded in-flight work, close resources/flush required telemetry within less than 30 seconds, and exit. Requests need deadlines and idempotent retry because forced kill remains possible.

**Trap:** sleeping 30 seconds while still receiving traffic.

### Problem 7 — Memory display (hard)

Linux shows little “free” memory but large cache and no swap pressure. Is it leaking?

**Solution.** Not from that evidence. Linux uses RAM for reclaimable page cache. Examine available memory, RSS trends, cgroup limit/events, reclaim, swap/page faults, OOM logs, and workload.

**Trap:** treating cached memory as permanently unavailable.

### Problem 8 — Zombie process (hard)

Why does `kill -9` not remove a zombie?

**Solution.** It has already exited. Its parent must `wait` to reap status; fix/signal/restart parent or let init adopt/reap it. Zombie does not execute.

**Trap:** escalating signals to a non-running process.

### Problem 9 — Secret exposure (hard)

A token was passed as a command-line argument and appears in process history/logs. Respond.

**Solution.** Revoke/rotate it, restrict and purge according to retention/evidence policy, audit use, stop logging command args, inject through a protected secret mechanism/file descriptor/workload identity, and minimize privilege/lifetime.

**Trap:** only editing the shell history.

## 4. REAL-WORLD / APPLIED CONTEXT

### Containers use Linux primitives

Containers are processes isolated by namespaces, constrained/accounted by cgroups, and given filesystem layers/mounts and capabilities. PID 1 has special signal/reaping responsibilities. Understanding files/processes explains why containers should run a foreground process, handle SIGTERM, avoid root, and write logs to standard streams.

### systemd services

systemd units declare the executable, user, environment, dependencies, restart behavior, resource controls, and hardening. Restart loops can amplify dependency load; `Restart=always` is not resilience without backoff/readiness and a fix for deterministic failure.

### JVM on Linux

The JVM reserves virtual regions and uses heap, metaspace, code cache, thread stacks, native buffers, and mapped files. Container cgroup limits differ from host totals. A Java OOM, kernel/cgroup OOM kill, and filesystem-full failure have different evidence and remediation.

## 5. COMPARISON TABLE

| Concept/tool | Shows | Use | Misinterpretation |
|---|---|---|---|
| `df` | Filesystem allocated/free blocks | Capacity at mount | Exact per-directory use |
| `du` | Reachable file sizes | Directory attribution | Open-deleted/snapshot storage |
| `df -i` | Inode availability | Tiny-file exhaustion | Byte capacity |
| `free` | Memory categories | Pressure context | “free=low means bad” |
| load average | Runnable + uninterruptible task demand | Demand trend vs CPUs | CPU percentage |
| RSS | Resident process pages | Physical footprint trend | Complete unique memory ownership |
| SIGTERM | Catchable graceful request | Normal shutdown | Guaranteed immediate exit |
| SIGKILL | Uncatchable termination | Last resort | Cleanup/graceful flush |
| symlink | Path reference | Flexible version/config links | Same object as hard link |
| hard link | Same inode entry | File identity/linking | Works across filesystems/directories generally |

## 6. COMMON MISTAKES & MISCONCEPTIONS

1. **Shell and terminal are the same.** Terminal transports I/O; shell interprets command language.
2. **Everything is literally a file.** Many resources use file descriptors/interfaces, but semantics differ.
3. **Deleting a file always frees space.** Open references retain storage.
4. **777 fixes permissions.** It creates exposure and ignores identity/path/MAC causes.
5. **Low free RAM means OOM.** Reclaimable cache and available memory matter.
6. **Load equals CPU use.** I/O-blocked tasks can contribute.
7. **SIGKILL is normal shutdown.** It prevents cleanup.
8. **Environment variables are secret storage.** Exposure depends on platform/tooling; use a secret control plane.
9. **Unquoted variables are safe when “normally simple.”** Production paths/input eventually contain special characters.
10. **`set -e` makes scripts correct.** It has contextual behavior and cannot replace validation/explicit checks.
11. **A zombie consumes normal runtime CPU.** It is an unreaped exit record.
12. **Reboot is diagnosis.** It destroys evidence and can hide recurring causes.

## 7. CHEAT SHEET — REVIEW ONLY

Review only; not a substitute for the lesson.

- Kernel manages resources; shell parses/launches; process is running program.
- Absolute path starts `/`; quote every data-derived path.
- fd 0 stdin, 1 stdout, 2 stderr.
- Mode digits: r=4,w=2,x=1; directory x means traverse.
- Exit 0 success; use `pipefail` where pipeline failure matters.
- SIGTERM graceful request; SIGKILL last resort.
- `df` filesystem, `du` reachable paths, `df -i` inodes.
- Low free RAM alone is not pressure; inspect available/reclaim/OOM.
- Load average is task demand, not percent CPU.
- `ss`, `lsof`, `ps`, `journalctl`, `vmstat`, `iostat` answer different layers.
- Validate exact targets before mutation; never concatenate untrusted shell.

## 8. PRACTICE SET FOR SELF-TEST

1. Decode mode 640 and 755.
2. Explain read/write/execute on a directory.
3. Redirect stdout to `out.log` and stderr to `err.log` without overwriting existing contents.
4. Why can a service bind `127.0.0.1:8080` but be unreachable remotely?
5. Name three causes of `df` full that `du` may not attribute directly.
6. Give the graceful sequence after SIGTERM.
7. Distinguish a sleeping process from zombie.
8. Explain why `PATH=.:...` can be dangerous.
9. Diagnose “too many open files” at process and system scope.
10. Write a safe conceptual loop over arbitrary filenames.

## 9. CURATED RESOURCES

- Brian Ward, *How Linux Works*, 3rd ed., Chapters 1–8 — kernel/user space, devices, disks, boot, services, networking, and shell basics.
- Michael Kerrisk, *The Linux Programming Interface*, Chapters 2–6, 20–27, 52–61 — authoritative system calls, files, processes, signals, virtual memory, terminals, sockets, and namespaces.
- GNU Bash Reference Manual, sections “Shell Operation,” “Quoting,” “Redirections,” “Pipelines,” and “Shell Parameters” — exact parsing and execution behavior.
- Filesystem Hierarchy Standard 3.0 — canonical purpose of `/etc`, `/var`, `/usr`, `/run`, and other hierarchy locations.
- `man 7 signal`, `man 2 open`, `man 2 unlink`, `man 7 credentials`, `man 5 proc` — primary Linux interface documentation.
- Brendan Gregg, *Systems Performance*, 2nd ed., Chapters 2, 5–10 — scientific methodology and CPU, memory, filesystem, disk, and network analysis.
- systemd official manuals: `systemd.service`, `systemd.exec`, `systemctl`, and `journalctl` — service lifecycle, hardening, status, and logs.

## 10. RELATED TOPICS BRIDGE

### Before

1. **Programming Logic and Debugging:** supplies contracts, hypotheses, boundaries, and regression thinking.
2. **Computer Networking:** supplies sockets, addresses, ports, DNS, and layered diagnostics.

### After

1. **Git and Collaborative Version Control:** uses files, shell, processes, permissions, and exit status.
2. **Cloud Computing Foundations:** runs Linux systems under virtualized/shared responsibility.
3. **Containers:** packages and isolates Linux processes/filesystems/resources.
4. **Kubernetes:** schedules and supervises containers, signals, storage, and networking.
5. **SRE:** turns OS/service evidence into monitoring, incidents, and capacity work.

---ANSWER KEY BELOW---

1. 640: owner rw, group r, others none; 755: owner rwx, group/others r-x.
2. Read lists entries, write changes entries, execute traverses/accesses named children; combinations have nuanced effects.
3. `command >>out.log 2>>err.log`.
4. Loopback listens only on local host namespace; bind appropriate interface and apply firewall/auth/TLS policy.
5. Open-deleted files, snapshots, reserved blocks, hidden data beneath a mount, filesystem metadata (any three).
6. Stop admission/mark unready, drain bounded in-flight, flush/close required state, exit before grace; forced termination remains possible.
7. Sleeping waits and can resume; zombie has exited and awaits parent reap.
8. Current directory executable can shadow a trusted command, especially after changing to untrusted directories.
9. Inspect per-process limit and fd count/types, leaks, system file table, workload/concurrency; raise limits only with capacity and leak analysis.
10. Use `find ... -print0` and `while IFS= read -r -d '' file; do ... "$file"; done`, or `find -exec`.
