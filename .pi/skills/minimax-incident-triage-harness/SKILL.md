---
name: minimax-incident-triage-harness
description: Production-style incident triage workflow for logs, metrics, code, and safe mitigations. Use when debugging alerts, regressions, outages, or suspicious runtime behavior.
license: MIT
metadata:
  version: "1.0.0"
  category: debugging
  sources:
    - Incident response and SRE triage practice
    - Evidence-first debugging workflows
    - Production mitigation and verification patterns
---

# Incident Triage Harness

Investigate production-style failures with an evidence-first loop: confirm symptoms, narrow the blast radius, correlate signals, inspect code, and prove the smallest safe mitigation. This skill drives structured incident response from detection through postmortem, with concrete commands, decision trees, and escalation rules at every phase.

## When to Use

Trigger this skill when the situation matches any of these patterns:

- **Production outage**: service down, 5xx spike, user-facing errors affecting a route or endpoint
- **Performance degradation**: latency exceeding SLO thresholds, throughput drop, resource saturation
- **Data corruption**: wrong results, stale reads, missing records, integrity violations
- **Security breach**: unauthorized access, credential leak, suspicious traffic patterns, unusual API key usage
- **Deployment regression**: failure window aligns with a recent deploy, rollback, or config push
- **Infrastructure failure**: disk full, memory exhaustion, network partition, dependency outage
- **Alert triage**: PagerDuty/Opsgenie/Grafana alert fired and you need to investigate

**Do NOT use this skill** for: feature requests, planned maintenance, performance tuning of a healthy system, or greenfield debugging of code that has never run in production.

**For deeper prompts, evidence templates, and mitigation checklists**, also read `reference.md` in this skill directory. It contains per-incident-type playbooks with concrete commands, diagnostic cheat sheets, monitoring thresholds, and runbook templates.

---

## The Triage Mindset

Before opening a single log file, lock in these principles:

1. **Symptom first, cause second.** Prove what is broken before you theorize why.
2. **Blast radius before root cause.** Contain the damage. A live incident is not the time for deep root cause analysis.
3. **Evidence over intuition.** Every hypothesis must survive contact with logs, metrics, or code.
4. **Smallest safe mitigation.** Disable a path, not a service. Roll back a change, not a sprint.
5. **Explicit uncertainty.** If you don't know, say you don't know — and say what would prove it.

---

## Triage Phases

The full incident lifecycle runs through seven phases. Move forward deliberately; do not skip phases during active incidents.

### Phase 0: Detect

Goal: confirm there is a real incident, not noise.

**Steps:**

1. **Verify the signal source**
   ```
   Is the alert from a synthetic check, real-user monitoring (RUM), or manual report?
   Synthetic alert + no RUM impact = likely a monitoring false positive.
   RUM spike + no synthetic alert = monitoring gap — treat as real.
   ```

2. **Check multiple independent signals**
   ```
   - Grafana/Datadog dashboards for correlated metric anomalies
   - Error tracking (Sentry, Rollbar) for exception rate changes
   - Log volume/pattern change (ELK, Loki, CloudWatch)
   - Business metrics (order volume, signup rate, payment success)
   - Social media / status page user reports
   ```

3. **Eliminate false positives**
   ```
   - Scheduled maintenance window? -> suppress alert
   - Known noisy alert that fires periodically? -> note pattern, escalate monitoring debt
   - Test environment bleeding into production dashboards? -> fix dashboard filter
   - Bot/crawler traffic surge? -> check User-Agent distribution
   ```

**Decision: Is this a real incident?**
```
YES -> Declare incident, start timer, move to Phase 1
NO  -> Document false positive, improve alert rule, exit
UNCERTAIN -> Treat as real. Bias toward action.
```

---

### Phase 1: Triage & Blast Radius

Goal: understand what is broken, who is affected, and how badly. This phase should take <5 minutes.

**Step 1: Define the symptom precisely**

```
Template:
  What: [exact user-visible failure]
  Where: [route, endpoint, job, region, AZ]
  When: [first observed timestamp, duration]
  Who: [affected user segment, % of traffic]
  How bad: [error rate %, latency p99, data loss, revenue impact]
```

Example:
```
  What: POST /api/checkout returns 500
  Where: us-east-1, checkout-service
  When: 14:03 UTC, ongoing (12 minutes)
  Who: 73% of checkout attempts
  How bad: ~$4,200/min revenue loss, p99 latency >30s vs normal 1.2s
```

**Step 2: Map the blast radius**

```
- What routes/endpoints are affected?
- What services are affected (trace upstream/downstream dependencies)?
- What regions/AZs/data centers?
- What user segments (all users, paid tier, specific geography)?
- What business functions are impaired?
```

**Step 3: Identify the recent change surface**

Deploys, config changes, and infrastructure events in the 24h before the incident window:

```
Commands:
  git log --oneline --since="24 hours ago" -- deployment/production/
  kubectl get events --sort-by='.lastTimestamp' -n production | tail -30
  aws cloudtrail lookup-events --lookup-attributes AttributeKey=EventName,AttributeValue=UpdateService --start-time $(date -d '24 hours ago' -Iseconds)
```

Checklist:
- [ ] Application deploy / rollback
- [ ] Infrastructure change (Terraform apply, CloudFormation stack update)
- [ ] Configuration change (feature flag, env var, Secrets Manager rotation)
- [ ] Database migration
- [ ] Dependency version bump
- [ ] Certificate rotation
- [ ] DNS change
- [ ] Scaling event (auto-scaling up/down, new nodes)
- [ ] Traffic shift (canary promotion, blue/green swap, load balancer change)

**Decision tree for Phase 1:**

```
Incident overlaps with recent deploy?
  ├─ YES -> Roll back first, investigate after service is restored
  └─ NO  -> Continue to Phase 2

Blast radius is expanding?
  ├─ YES -> Escalate immediately (see Escalation Rules below). Consider traffic drain or circuit-breaker.
  └─ NO  -> Proceed to Phase 2

Incident is revenue-critical (payment, checkout, login)?
  ├─ YES -> Declare SEV1. Wake on-call commander. Parallelize: one person mitigates, one diagnoses.
  └─ NO  -> Proceed to Phase 2
```

---

### Phase 2: Diagnose

Goal: form the smallest plausible hypothesis and gather evidence to test it.

**Step 1: Gather evidence in priority order**

```
1. ERROR LOGS (fastest signal)
   - Application error logs around the incident start time
   - Stack traces — look for the root exception, not the wrapper
   - Error rate by endpoint (Sentry/Datadog APM breakdown)

   Commands:
     grep "2026-05-05T14:0[0-9]" /var/log/app/error.log | cut -d' ' -f5- | sort | uniq -c | sort -rn | head -20
     kubectl logs -l app=checkout-service --since=15m --tail=500 | grep -E "ERROR|FATAL|panic"

2. METRICS (second signal — confirms or refines)
   - Latency percentiles (p50, p95, p99)
   - Error rate (4xx, 5xx breakdown)
   - Throughput (requests/sec)
   - Resource utilization (CPU, memory, disk, network)
   - Dependency health (DB connections, cache hit rate, queue depth)

3. TRACES (third signal — pinpoints the bottleneck)
   - Find a representative failed trace in Jaeger/Zipkin/Honeycomb
   - Identify which span is the bottleneck or error origin
   - Compare with a successful trace from before the incident

4. RECENT CODE CHANGE (fourth signal — explains why)
   - Diff the deploy that overlaps with the incident window
   - Focus on: error handling changes, DB query changes, network call additions
```

**Step 2: Form hypotheses**

Use this template for each hypothesis:

```
Hypothesis #N:
  If [root cause] is happening,
  then we would expect to see [specific evidence].
  We would NOT expect to see [counter-evidence].

  Strongest next check: [exact command or dashboard query]
  Time to check: [estimated minutes]
```

Example:
```
Hypothesis #1:
  If the DB connection pool is exhausted,
  then we would expect to see "connection timeout" errors and pg_stat_activity showing maxed connections.
  We would NOT expect to see fast queries completing normally.

  Strongest next check: SHOW PROCESSLIST or SELECT count(*) FROM pg_stat_activity;
  Time to check: 1 minute
```

**Step 3: Test and eliminate**

```
1. Test the fastest-to-verify hypothesis first
2. If confirmed -> move to Phase 3 (Mitigate)
3. If disproved -> eliminate it explicitly, form next hypothesis
4. If multiple hypotheses remain after 10 minutes -> escalate, bring in SME
```

**Diagnostic command patterns by symptom:**

```bash
# High latency
curl -w "@curl-format.txt" -o /dev/null -s https://api.example.com/health  # measure endpoint timing
strace -c -p $(pgrep -f "node|python|java")  # syscall time distribution
perf top -p $(pgrep -f "binary")  # CPU profile in real time

# High error rate
tail -10000 /var/log/app/access.log | awk '{print $9}' | sort | uniq -c | sort -rn  # HTTP status distribution
grep -oP '"error":"[^"]*"' /var/log/app/app.log | sort | uniq -c | sort -rn | head -10  # error message frequency

# Memory issues
ps aux --sort=-%mem | head -20  # top memory consumers
grep -E "^(VmRSS|VmSize|Threads)" /proc/$(pgrep -f "binary")/status  # process memory details

# Connection issues
ss -tulpn | grep LISTEN  # what's listening
ss -tn state established | wc -l  # count established connections
netstat -s | grep -i "overflow\|pruned\|collapsed"  # TCP buffer issues
```

---

### Phase 3: Mitigate

Goal: reduce or eliminate user impact. **This is NOT the fix. This is the tactical action that stops the bleeding.**

**Mitigation hierarchy (prefer highest that suffices):**

```
Level 1: TOGGLE (fastest, safest)
  - Disable feature flag for failing feature
  - Switch traffic to a healthy replica/region
  - Enable circuit breaker on failing dependency
  Rollback time: <1 minute. Blast radius: minimal.

Level 2: ROLLBACK
  - Revert the most recent deploy
  - Roll back database migration (if safe and no data loss)
  - Restore previous configuration
  Rollback time: 2-10 minutes. Blast radius: changes reverted for all traffic.

Level 3: SCALE
  - Scale up instances to handle overload
  - Increase connection pool / thread pool
  - Increase disk space or swap
  Rollback time: 1-5 minutes. Blast radius: buys time, does not fix root cause.

Level 4: DRAIN / SHED
  - Drain traffic from failing region to healthy region
  - Drop non-critical requests at the load balancer
  - Throttle low-priority traffic (rate limiting at edge)
  Rollback time: 1-5 minutes. Blast radius: some features degraded for some users.

Level 5: PARTIAL OUTAGE ACCEPTANCE
  - Accept that a non-critical feature is down
  - Return degraded-but-correct responses (graceful degradation)
  - Communicate to users via status page
  Rollback time: indefinite. Blast radius: controlled, communicated.
```

**Before executing mitigation, ask:**

```
- Will this stop the bleeding without making anything else worse?
- Can we undo this in <5 minutes if it's wrong?
- Does anyone on the call object? (Silence = consent after explicit ask)
```

**Mitigation verification:**

After applying mitigation, verify within 2 minutes:
```
- Error rate dropping? Check dashboard.
- Latency returning to baseline? Check p50/p99.
- User reports stopping? Check support tickets / social.
- Any new unexpected failures? Check dashboards for second-order effects.
```

If mitigation did NOT reduce impact within 5 minutes, **undo it** and try next level up.

---

### Phase 4: Root Cause Analysis

Goal: identify the actual root cause. This is where the real fix lives. **Only proceed here after the incident is mitigated or if no mitigation is possible.**

**The Five Whys (SRE method):**

```
1. Why did the checkout endpoint return 500?
   -> The DB query timed out after 30 seconds.

2. Why did the DB query time out?
   -> The query did a full table scan on the orders table.

3. Why did it do a full table scan?
   -> The query filter used `status` column, but the index on `status` was dropped in last migration.

4. Why was the index dropped?
   -> The migration intended to replace it with a composite index but had a bug that only dropped it.

5. Why didn't CI catch this?
   -> Migrations are tested in CI, but the performance impact only manifests at production data volume.
```

**Root cause categories and evidence:**

| Category | Evidence | Common fix |
|----------|----------|------------|
| Code bug | Stack trace points to new/changed code, repro in staging | Code fix + deploy |
| Configuration | Config diff shows changed value, revert fixes it | Config rollback |
| Capacity | Resource graphs show plateau/saturation, scaling fixes it | Scale up + capacity planning |
| Dependency | Upstream/downstream error correlated, their status page shows incident | Circuit breaker + fallback |
| Data | Query returns wrong/unexpected data, migration artifacts | Data fix + migration repair |
| Process | No deploy but behavior changed, e.g. cron job ran, token expired | Process fix + monitoring |

---

### Phase 5: Fix

Goal: apply the permanent fix and prove it resolves the root cause.

**Fix sequence:**

```
1. Write the fix (code, config, data migration, infrastructure change)
2. Test in staging with production-like load
3. If fix is low-risk -> deploy through normal pipeline
4. If fix is high-risk or urgent -> deploy with heightened monitoring and rollback plan
5. Verify fix against the original symptom
6. Undo any temporary mitigations (re-enable feature, restore traffic, remove rate limit)
```

**Fix verification checklist:**

```
- [ ] Deploy complete without errors
- [ ] Original symptom no longer reproducible
- [ ] Error rate returned to pre-incident baseline
- [ ] Latency returned to pre-incident baseline
- [ ] Canary/metrics stable for >15 minutes post-deploy
- [ ] Mitigation safely removed (feature flag re-enabled, traffic drained back)
- [ ] No regressions introduced (check unrelated dashboards)
- [ ] On-call notified that fix is live
```

---

### Phase 6: Verify

Goal: confirm the system is fully healthy and the incident is resolved.

**Verification gates:**

```
Gate 1: SYMPTOM GONE (5 min window)
  - Primary error metric at 0 or pre-incident baseline
  - Original failing endpoint returns 200/expected response
  - Synthetic check passes

Gate 2: NO SECONDARY EFFECTS (15 min window)
  - All services healthy (check all dashboards, not just the affected one)
  - No queue backlogs (SQS/Kafka lag, Sidekiq/Resque queue depth)
  - No cascading failures in downstream services

Gate 3: CAPACITY STABLE (30 min window)
  - Memory/CPU/disk stable, not trending toward saturation
  - DB connection pool at normal levels
  - Cache hit rate normal

Gate 4: USER EXPERIENCE NORMAL (1 hour window)
  - Real-user monitoring (RUM) metrics at baseline
  - Support ticket volume normalized
  - Business metrics (orders, logins, payments) at expected levels
```

**Declare incident resolved only when all gates pass.**

If any gate fails, return to Phase 1 with the new symptom.

---

### Phase 7: Postmortem

Goal: learn from the incident and prevent recurrence. **This is mandatory for SEV1 and SEV2 incidents.**

**Postmortem timeline:**
- SEV1: Draft within 24 hours, final within 72 hours
- SEV2: Draft within 48 hours, final within 5 business days
- SEV3: Blameless async doc within 1 week

**Required sections (see reference.md for full template):**

```
1. Summary (1 paragraph — what happened, impact, duration)
2. Timeline (UTC, minute-by-minute key events)
3. Root Cause (what caused it, not just what triggered it)
4. Impact (users affected, revenue lost, data loss, SLA breach)
5. Detection (how was it found — alert, user report, engineer noticed)
6. Response (what was done, when, by whom)
7. Resolution (permanent fix applied)
8. Action Items (specific, owner, due date)
   - Prevent recurrence: [action] -> @owner by YYYY-MM-DD
   - Improve detection: [action] -> @owner by YYYY-MM-DD
   - Improve response: [action] -> @owner by YYYY-MM-DD
9. Lessons Learned (what went well, what went poorly, what surprised us)
10. Timeline to Detection (how long from first failure to first alert)
11. Timeline to Mitigation (how long from alert to impact reduced)
12. Timeline to Resolution (how long from alert to permanent fix)
```

**Postmortem anti-patterns:**
- Blaming individuals instead of systems
- Accepting "human error" as root cause (ask: why did the system allow the human error?)
- Skipping action items with no owner or due date
- Writing a postmortem that no one reads (share in team meeting, discuss action items)

---

## Escalation Rules

Escalate immediately when any of these triggers fire. **Err on the side of over-escalation during an active incident.**

### Escalation Triggers

| Trigger | Action |
|---------|--------|
| **Incident exceeds 15 minutes without mitigation** | Escalate to on-call commander / engineering manager |
| **Blast radius is expanding** (more endpoints, regions, or user segments affected) | Escalate to incident commander, wake additional on-call engineers |
| **Data loss or corruption confirmed** | Escalate to CTO / VP Engineering, wake DBA on-call |
| **Security breach confirmed** | Escalate to security on-call, follow security incident response plan |
| **Revenue impact exceeds $X/hour** (define per organization) | Escalate to VP Engineering / business stakeholders |
| **SLA breach imminent** (>X minutes of 5xx in measurement window) | Escalate to customer-facing teams (support, TAM, CSM) |
| **Single on-call engineer overwhelmed** (>3 hypotheses being chased, >5 people asking for updates) | Escalate to incident commander to coordinate |
| **Two independent systems failing simultaneously** (unlikely to be a single root cause) | Escalate to infrastructure/platform team, consider multi-cause scenario |

### Escalation Path

```
On-call Engineer (first responder)
  -> On-call Commander (coordinates response, communicates status)
    -> Engineering Manager (resource allocation, stakeholder communication)
      -> Director / VP Engineering (major customer impact, press inquiry risk)
        -> CTO (existential threat to the business)
```

### Declaring Incident Severity

```
SEV1: Complete service outage, data loss, security breach, revenue-critical path down
  - Page on-call commander immediately
  - Status page updated within 5 minutes
  - Executive update every 30 minutes

SEV2: Partial outage, significant degradation, non-critical path down
  - Page on-call team
  - Status page updated within 15 minutes
  - Stakeholder update every 2 hours

SEV3: Minor degradation, single-user impact, non-production issue
  - Ticket created, addressed during business hours
  - No status page update unless user-visible
```

---

## Multi-Agent Incident Response

For complex incidents, decompose the investigation across multiple agents using the `Task` delegation pattern.

### Agent Team Roles

```
Role: TRIAGE LEAD (you)
  - Coordinates the overall incident response
  - Maintains the timeline
  - Communicates status
  - Decides when to escalate
  - Does NOT dive deep into any single hypothesis

Role: LOG ANALYST (delegate)
  - Searches and analyzes error logs
  - Identifies error patterns and frequencies
  - Correlates errors with user-visible symptoms

Role: METRICS ANALYST (delegate)
  - Analyzes dashboards and time-series data
  - Identifies metric anomalies and correlations
  - Produces latency/error/throughput breakdowns

Role: CODE SLEUTH (delegate)
  - Inspects recent code changes
  - Traces code paths from entry point to failure
  - Identifies logical errors, race conditions, missing edge cases

Role: INFRA INVESTIGATOR (delegate)
  - Checks infrastructure health (nodes, network, storage)
  - Verifies configuration and secrets
  - Diagnoses resource exhaustion or capacity issues
```

### Delegation Pattern

```
// Launch parallel investigations when hypotheses are independent

Task(
  subagent_type="generalPurpose",
  description="Log analysis for incident",
  prompt="Analyze error logs for checkout-service in us-east-1 between 14:00-14:15 UTC.
    Search for ERROR/FATAL/panic patterns. Report top 5 error messages with counts and example stack traces.
    Return: error distribution, most frequent stack trace, any correlated warnings."
)

Task(
  subagent_type="generalPurpose",
  description="Code diff analysis for incident",
  prompt="Git diff the most recent deploy to checkout-service. Focus on:
    1. Changes to error handling paths
    2. Changes to database queries
    3. Changes to external API calls
    Return: files changed, risk assessment for each change, most suspicious diff."
)
```

### Agent Handoff Rules

```
1. TRIGGER: When you have >3 plausible hypotheses
   ACTION: Delegate 1-2 hypotheses per agent

2. TRIGGER: When you've spent >10 minutes on one hypothesis with no confirmation
   ACTION: Delegate the investigation to a focused agent, move to next hypothesis

3. TRIGGER: When infrastructure AND code AND data all look suspicious
   ACTION: Deploy all three specialist agents in parallel

4. TRIGGER: When mitigation is applied but symptom persists
   ACTION: Delegate verification agent to check all dashboards for second-order effects
```

---

## Common Pitfalls

### Pitfall 1: Treating Symptoms, Not Causes

```
ANTI-PATTERN:
  "CPU is at 100%. Let's add more CPU."
  Symptom: high CPU
  Root cause ideas: infinite loop, GC thrashing, regex catastrophic backtracking,
                    sudden traffic spike, cron job overlap

CORRECT:
  1. Identify WHY CPU is high (profile with `perf top` or `py-spy`)
  2. Fix the cause (fix the loop, tune GC, limit regex input)
  3. Add CPU as mitigation only if immediate relief is needed
```

### Pitfall 2: Confirmation Bias

```
ANTI-PATTERN:
  "I think it's the deploy. Look — this log line mentions the new code."
  (Ignores that the same error occurred 3 days ago, before the deploy)

CORRECT:
  1. Explicitly state each hypothesis
  2. Define evidence that would PROVE it and evidence that would DISPROVE it
  3. Actively search for disconfirming evidence
  4. Eliminate hypotheses explicitly: "Hypothesis #2 disproved because..."
```

### Pitfall 3: Premature Optimization

```
ANTI-PATTERN:
  "The fix is to refactor the entire payment module to be async."
  (During a SEV1, proposing a 3-week refactor)

CORRECT:
  1. Mitigate first: "Revert the deploy, service is back."
  2. Root cause: "The new synchronous call to fraud-check adds 8s to the critical path."
  3. Fix: "Make fraud-check call async with a timeout" or "Revert and redesign in a follow-up PR."
```

### Pitfall 4: Editing Code Before Confirming the Symptom

```
ANTI-PATTERN:
  "The logs say 'connection refused'. Let me update the connection string and redeploy."
  (The actual issue: the DB server is down. Code change is irrelevant.)

CORRECT:
  1. Reproduce the symptom
  2. Check infrastructure health
  3. THEN inspect code
```

### Pitfall 5: Declaring Victory After Mitigation

```
ANTI-PATTERN:
  "We rolled back. Incident resolved. Close the ticket."
  (No root cause, no action items, same incident will recur on next deploy.)

CORRECT:
  1. Mitigate -> incident is "stable", not "resolved"
  2. Find root cause -> incident is "understood"
  3. Apply permanent fix -> incident is "resolved"
  4. Complete postmortem -> incident is "closed"
```

### Pitfall 6: Hiding Uncertainty

```
ANTI-PATTERN:
  "We fixed it." (Reality: we applied 3 changes at once and don't know which one worked.)

CORRECT:
  "We applied 3 mitigations simultaneously. The symptom resolved. We cannot confirm 
   which mitigation was effective. Action item: reproduce in staging to isolate the 
   effective fix before the next deploy."
```

---

## Communication During Incidents

### Status Update Template

Send updates on a regular cadence (every 30 minutes for SEV1, every 2 hours for SEV2):

```
Incident: [short title]
Severity: [SEV1 / SEV2 / SEV3]
Status: [investigating / mitigating / monitoring / resolved]
Duration: [X minutes]

Current situation:
  - [bullet: what we know]
  - [bullet: what we're doing]
  - [bullet: customer impact]

Next update: [time or "when status changes significantly"]

Incident commander: [name]
Incident channel: [#slack-channel]
```

### Status Page Guidance

```
Investigating: "We are investigating elevated error rates on the checkout endpoint. 
  Customers may experience errors when attempting to complete purchases."
  
Identified: "The issue has been identified as a missing database index introduced 
  in the latest deployment. We are rolling back the deployment."

Monitoring: "The deployment has been rolled back. Error rates have returned to normal. 
  We are monitoring closely."

Resolved: "The incident is resolved. A full postmortem will be published within 72 hours."
```

---

## Quick Reference

```
DETECT     -> Verify real incident. Check multiple independent signals.
TRIAGE     -> Define symptom precisely. Map blast radius. Check recent changes. (<5 min)
DIAGNOSE   -> Form hypotheses. Gather evidence. Test and eliminate. (ongoing)
MITIGATE   -> Stop the bleeding. Toggle > Rollback > Scale > Drain > Accept. (<5 min to apply)
ROOT CAUSE -> Five Whys. Identify systemic cause, not just trigger.
FIX        -> Permanent fix. Test. Deploy. Verify. Undo mitigations.
VERIFY     -> Symptom gone. No secondary effects. Capacity stable. User experience normal.
POSTMORTEM -> Write within 24-72h. Action items with owners and dates. Share and learn.

ESCALATE when: >15 min no mitigation, expanding blast radius, data loss, security breach.
PITFALLS: symptoms≠causes, confirmation bias, premature optimization, code-before-evidence.
```

---

## Additional Resources

- For per-incident-type diagnostic playbooks with concrete commands, see [reference.md](reference.md)
- The reference file includes: memory leak, race condition, DB connection pool exhaustion, API latency spike, disk full, CPU spike, and network partition playbooks, plus command cheat sheets, monitoring thresholds, and runbook/postmortem templates.