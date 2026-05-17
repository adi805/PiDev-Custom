# Incident Triage Harness Reference

This file supports `SKILL.md` with deeper examples, checklists, diagnostic commands, playbooks, runbook templates, and prompt patterns.

## Typical Failure Shapes

### 1. Deployment Regression

Signals:

- incident starts right after deploy
- one route or job fails consistently
- stack traces point into recently changed code

Good next checks:

- inspect deploy diff (`git diff HEAD~1..HEAD --stat`)
- compare failing and previous behavior
- verify whether config or env assumptions changed
- check deploy timestamp alignment with error spike (`grep TIMESTAMP logs/app.log | cut -d' ' -f1 | sort | uniq -c`)

### 2. Missing Migration Or Schema Drift

Signals:

- queries fail after deploy
- one table or index is suddenly slow or missing
- app code expects fields or indexes not present in the DB

Good next checks:

- verify migration history (`alembic history`, `rails db:migrate:status`, `prisma migrate status`)
- inspect schema or index presence (`\d+ table_name` in psql, `SHOW CREATE TABLE`, `DESCRIBE`)
- confirm whether app code and DB version diverged

### 3. Integration Breakage

Signals:

- upstream or downstream API errors
- auth tokens fail unexpectedly
- only one external dependency path is broken

Good next checks:

- inspect recent dependency or config changes
- compare successful vs failing requests (`diff <(curl -s -w "\n%{http_code}" success-url) <(curl -s -w "\n%{http_code}" failing-url)`)
- verify credentials, base URLs, or rate-limit behavior

### 4. Memory Leak / OOM Kill

Signals:

- process restarts without deploy
- increasing memory RSS over time (`ps aux --sort=-%mem | head`)
- OOM killer entries in dmesg or system logs
- gradual latency increase before crash

Good next checks:

- memory timeline: `while true; do ps -o rss,comm -p $PID | tail -1; sleep 60; done | tee mem.log`
- OOM detection: `dmesg -T | grep -i "out of memory\|oom-killer" | tail -20`
- heap profile: attach profiler or capture `jmap -histo $PID` (Java), `tracemalloc` snapshot (Python)
- GC behavior: check GC pause times and frequency

### 5. Database Connection Pool Exhaustion

Signals:

- "too many connections" or "connection pool exhausted" errors
- requests queueing up with no CPU/IO spike
- application hangs during traffic peaks
- idle connections accumulating

Good next checks:

- pool stats: `SELECT count(*) FROM pg_stat_activity WHERE state = 'idle';` (PostgreSQL) or pool metrics endpoint
- connection age: `SELECT pid, age(now(), query_start) FROM pg_stat_activity WHERE state != 'idle';`
- pool config vs actual: compare `pool_size` config with observed connections
- leak detection: count open connections over time, check for missing `close()`/`release()`

### 6. Race Condition / Deadlock

Signals:

- intermittent failures that reproduce under concurrency
- database deadlock errors (`ERROR: deadlock detected`)
- mutex/lock timeout warnings
- operation succeeds alone, fails in parallel

Good next checks:

- deadlock logs: `SELECT * FROM pg_stat_activity WHERE wait_event_type = 'Lock';`
- lock graph: trace lock acquisition order in logs
- stress test: `ab -n 1000 -c 50 http://endpoint` or `wrk -t4 -c100 -d30s`
- code audit: review shared mutable state access patterns

### 7. Disk Full

Signals:

- write errors across multiple services
- "No space left on device" in logs
- deployments or builds failing with ENOSPC
- log files stop growing

Good next checks:

- disk usage: `df -h` and `du -sh /* 2>/dev/null | sort -rh | head -20`
- large files: `find / -xdev -type f -size +500M -exec ls -lh {} \; 2>/dev/null`
- inode exhaustion: `df -i` — inode full even with free disk space
- log rotation: check if logrotate is running, check for runaway log files

### 8. DNS Failure

Signals:

- "Name or service not known" / "Temporary failure in name resolution"
- intermittent connectivity to specific hosts
- service discovery failures (Consul, etcd, Kubernetes DNS)

Good next checks:

- resolve test: `dig +short example.com`, `nslookup service.internal`, `host api.external.com`
- DNS config: `cat /etc/resolv.conf`, check `search` domains
- cache poisoning check: compare resolver output across different nameservers
- Kubernetes: `kubectl logs -n kube-system -l k8s-app=kube-dns` or CoreDNS logs

### 9. TLS / Certificate Expiry

Signals:

- sudden SSL/TLS handshake failures
- "certificate has expired" / "certificate verify failed" errors
- browsers or clients rejecting connections
- only affects external-facing endpoints

Good next checks:

- cert expiry: `echo | openssl s_client -servername example.com -connect example.com:443 2>/dev/null | openssl x509 -noout -dates`
- chain validation: `openssl s_client -showcerts -connect example.com:443 </dev/null 2>/dev/null | openssl verify -verbose`
- auto-renewal: check certbot/cert-manager cron or controller status
- Kubernetes: `kubectl get certificates -A`, `kubectl describe certificate`

### 10. CPU Throttle / Noisy Neighbor

Signals:

- latency spikes without request count increase
- CPU steal time (`%st` in top) above 5%
- unexplained periodic slowdowns at regular intervals
- container/vm throttled metrics

Good next checks:

- steal time: `top -bn1 | head -5` or `vmstat 1 5` — watch `st` column
- cgroup throttle: `cat /sys/fs/cgroup/cpu/cpu.stat` or `docker stats --no-stream`
- scheduled tasks: check cron, systemd timers, background jobs during incident window
- cloud metrics: check hypervisor/VM CPU credits (AWS T-series) or vCPU entitlement

---

## Diagnostic Cheat Sheets

### Web Application — Quick First Checks

```bash
# Error rate per endpoint in last 5 minutes
grep "$(date -d '5 min ago' '+%Y-%m-%dT%H:%M')" /var/log/app/access.log \
  | awk '{print $9, $7}' | sort | uniq -c | sort -rn | head -20

# Response time distribution (Apache/Nginx combined format)
awk '{print $NF}' /var/log/nginx/access.log | sort -n \
  | awk '{a[NR]=$1} END{print "p50:", a[int(NR*0.5)], "p95:", a[int(NR*0.95)], "p99:", a[int(NR*0.99)]}'

# Top memory consumers
ps aux --sort=-%mem | head -20

# Open file descriptors per process
lsof | awk '{print $1}' | sort | uniq -c | sort -rn | head -20

# TCP connection states
ss -s

# Top 10 IPs by connection count
ss -tn | awk '{print $5}' | cut -d: -f1 | sort | uniq -c | sort -rn | head -10
```

### Database — Quick First Checks

```bash
# PostgreSQL: active queries and their duration
psql -c "SELECT pid, age(now(), query_start), state, left(query, 120)
         FROM pg_stat_activity WHERE state != 'idle' ORDER BY query_start;"

# PostgreSQL: table bloat estimate
psql -c "SELECT schemaname, relname, n_dead_tup, n_live_tup, last_autovacuum
         FROM pg_stat_user_tables ORDER BY n_dead_tup DESC LIMIT 10;"

# PostgreSQL: index usage
psql -c "SELECT schemaname, relname, indexrelname, idx_scan, idx_tup_read, idx_tup_fetch
         FROM pg_stat_user_indexes ORDER BY idx_scan DESC LIMIT 20;"

# MySQL: running queries and locks
mysql -e "SELECT * FROM information_schema.processlist WHERE command != 'Sleep'\G"
mysql -e "SELECT * FROM information_schema.innodb_lock_waits\G"

# MongoDB: current operations
mongosh --eval "db.currentOp({active: true, '$ownOps': false})"
```

### Container / Orchestration — Quick First Checks

```bash
# Kubernetes: failing pods
kubectl get pods -A --field-selector=status.phase!=Running,status.phase!=Succeeded

# Kubernetes: events in last 15 minutes
kubectl get events -A --sort-by='.lastTimestamp' \
  | grep "$(date -u -d '15 min ago' '+%Y-%m-%dT%H')" || true

# Docker: container resource usage
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"

# Docker: exited containers (potential restarts)
docker ps -a --filter "status=exited" --format "table {{.Names}}\t{{.Status}}\t{{.Image}}"

# Systemd: failed services
systemctl --failed

# Systemd: service logs since incident start
journalctl -u service-name --since "15 minutes ago" --no-pager | tail -50
```

### Network — Quick First Checks

```bash
# Connectivity to upstream
for host in api1.example.com api2.example.com db.internal; do
  echo -n "$host: "; nc -zv -w2 $host 443 2>&1 | grep -o 'succeeded!\|Connection refused\|timed out'
done

# DNS resolution timing
dig +stats example.com

# Packet loss and latency
ping -c 10 -i 0.2 gateway.internal

# Interface errors
ip -s link show | grep -A1 '^[0-9]' | grep -v '^--$'

# Current bandwidth per process
iftop -t -s 5 -L 10 2>/dev/null || nethogs -t -d 5
```

---

## Monitoring Thresholds — When to Escalate

### Latency

| Metric | Warning | Critical | Action |
|--------|---------|----------|--------|
| p50 latency | > 2× baseline | > 5× baseline | Scale, check cache |
| p95 latency | > 3× baseline | > 10× baseline | Investigate DB, GC |
| p99 latency | > 5× baseline | > 20× baseline | Full incident response |
| Time-to-first-byte | > 200ms | > 1s | Check upstream deps |

### Error Rate

| Metric | Warning | Critical | Action |
|--------|---------|----------|--------|
| 5xx rate | > 0.1% | > 1% | Rollback, circuit break |
| 4xx rate (auth) | > 5% | > 20% | Check auth provider |
| Timeout rate | > 0.5% | > 5% | Scale, optimize queries |
| Drop rate | > 0.01% | > 0.1% | Load shed, scale |

### Saturation

| Metric | Warning | Critical | Action |
|--------|---------|----------|--------|
| CPU utilization | > 70% | > 90% | Scale, profile hot paths |
| Memory utilization | > 80% | > 95% | Restart leaky process, scale |
| Disk utilization | > 80% | > 95% | Cleanup, expand volume |
| Connection pool | > 70% | > 90% | Increase pool, scale instances |
| Queue depth | > baseline + 50% | > baseline + 200% | Process faster, add consumers |
| Garbage collection | > 100ms pause | > 500ms pause | Tune GC, check heap |

---

## Prompt Pattern

Use this shape when asking a subagent or structuring your own reasoning:

```text
Incident:
[short symptom summary]

Known evidence:
- [log or metric]
- [deployment clue]
- [user-visible impact]

Return:
1. top 2-3 hypotheses
2. the strongest next check for each
3. the smallest safe mitigation if impact is ongoing
4. what would prove the root cause
```

## Decision Tree — Escalation Flow

```
Incident detected
  │
  ├─ Is blast radius unknown? ── YES ──> Determine scope first (check all endpoints/services)
  │                                      
  ├─ Is revenue/user-facing? ── YES ──> Page on-call now, don't wait for triage
  │
  ├─ Are you the SME (Subject Matter Expert)?
  │   ├─ YES ──> Proceed to Diagnostic Phase
  │   └─ NO  ──> Gather symptoms, escalate to SME within 15 min
  │
  ├─ Is impact worsening?
  │   ├─ YES and accelerating ──> Immediate mitigation (rollback/circuit-breaker)
  │   ├─ YES but stable     ──> Proceed with triage while monitoring
  │   └─ NO (stable)        ──> Full triage, no rush — but don't let it go cold
  │
  └─ After 30 min with no root cause identified
      ├─ Escalate breadth: involve infra/DB/network specialists
      └─ If still unsolved at 60 min: initiate war room / bridge call
```

## Safe Mitigation Checklist

Before recommending mitigation:

- does it reduce harm without widening scope?
- can it be rolled back quickly?
- does it avoid destructive data changes?
- can you verify it with the current runtime?
- have you documented the mitigation so the next on-call understands what was done?
- have you set a reminder to revisit the temporary fix?

### Mitigation Patterns — Tiered

**Tier 1 — Immediate (do now, ask later):**
- Roll back the most recent deploy
- Toggle a feature flag OFF
- Increase instance count / scale horizontally
- Redirect traffic away from failing region/AZ
- Enable read-only mode to stop data corruption

**Tier 2 — Short-term (approval needed, low risk):**
- Restart affected service
- Clear a specific cache key
- Increase connection pool size
- Add a temporary rate limit
- Drop non-critical traffic (health checks, crawlers)

**Tier 3 — Delayed (requires planning, higher risk):**
- Add an index to a table
- Alter a query timeout
- Change load balancer config
- Manual data fix / migration

## Reporting Template

```text
Symptom:
Blast radius:
Current best hypothesis:
Evidence:
Mitigation:
Verification:
Remaining unknowns:
Next steps:
```

### Postmortem Template

```text
Incident Title: [short title]
Date: [YYYY-MM-DD HH:MM UTC]
Duration: [minutes from detection to mitigation]
Severity: [SEV1 / SEV2 / SEV3]

## Summary
[One paragraph — what happened and how it was fixed]

## Timeline (UTC)
- HH:MM — Detection: [how detected — monitoring, user report, etc.]
- HH:MM — Triage start: [who responded]
- HH:MM — Hypothesis formed: [initial diagnosis]
- HH:MM — Root cause confirmed: [what proved it]
- HH:MM — Mitigation applied: [what was done]
- HH:MM — Service restored: [verification method]

## Root Cause
[Detailed explanation of what caused the incident — include config diff, code change, external trigger]

## Impact
- Users affected: [count or percentage]
- Revenue impact: [estimated or N/A]
- Data loss: [description or none]
- Services degraded: [list]

## What Went Well
- [something that worked during response]

## What Went Wrong
- [something that delayed or complicated response]

## Action Items
- [ ] [actionable item with owner and due date]
- [ ] [preventive measure — monitoring, alert, process change]
- [ ] [follow-up investigation]

## Mitigation vs Fix
- Mitigation applied: [what stopped the bleeding]
- Permanent fix: [what prevents recurrence — planned or completed]
```

## Evidence Collection Playbook

When entering an unfamiliar incident, collect these in order:

1. **Time window**: When exactly did symptoms start? (pinpoint from logs/metrics)
2. **Affected scope**: Which endpoints, services, users, regions? (blast radius)
3. **Recent changes**: Deploys, config changes, dependency updates, infrastructure changes? (check deploy logs, terraform apply logs, git history)
4. **Error signatures**: What do the errors look like? (collect 10-20 representative stack traces or error messages)
5. **Resource state**: CPU, memory, disk, connections, thread count at time of incident (capture snapshots)
6. **Upstream/downstream health**: Are dependencies healthy? (health check all integrations)
7. **Traffic pattern**: Any change in request volume, pattern, or source? (compare to same time yesterday)

## Anti-Patterns

- editing code before confirming the symptom
- broad refactors during an active incident
- treating one suspicious log line as proof
- claiming a fix when only a mitigation was verified
- hiding uncertainty when the root cause is still incomplete
- restarting a service without preserving logs, heap dumps, or thread dumps first
- making multiple changes at once — you can't isolate which one worked
- assuming "it fixed itself" — it didn't, it will happen again
- escalating without a summary of what you've already checked
- forgetting to set a follow-up reminder for the permanent fix

## Runbook — Incident Commander Checklist

**First 5 minutes:**
- [ ] Acknowledge the alert / page
- [ ] Determine blast radius: which services, endpoints, users?
- [ ] If user-facing: post to status page
- [ ] If accelerating: start rollback or circuit-breaker in parallel with triage

**First 15 minutes:**
- [ ] Collect evidence: logs, metrics, recent changes
- [ ] Form initial hypothesis
- [ ] Run first diagnostic check against hypothesis
- [ ] If hypothesis wrong: form new hypothesis from new evidence
- [ ] Assign roles if multiple responders: IC (incident commander), Comms, Investigator

**First 30 minutes:**
- [ ] Mitigation in place or clear ETA
- [ ] Status update sent to stakeholders
- [ ] If no root cause: escalate breadth (involve other teams)
- [ ] If progress stalled: call for war room

**First 60 minutes:**
- [ ] Root cause confirmed or solid theory with evidence
- [ ] Permanent fix scoped
- [ ] Postmortem draft started (capture while fresh)

**Resolution:**
- [ ] Verify service restored (not just "no errors" — check latency, throughput, correctness)
- [ ] Communicate resolution to stakeholders
- [ ] Create postmortem within 24 hours
- [ ] File follow-up tickets for all action items
- [ ] Schedule postmortem review meeting

## Tool-Specific Diagnostic Shortcuts

### Prometheus / Grafana

```promql
# Error rate per endpoint (last 5 min)
rate(http_requests_total{status=~"5.."}[5m])

# Latency percentiles
histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))

# Memory pressure
rate(node_memory_MemAvailable_bytes[5m])

# CPU throttle
rate(container_cpu_cfs_throttled_seconds_total[5m])

# Disk IO saturation
rate(node_disk_io_time_seconds_total[5m])
```

### Elasticsearch / Kibana

```
# Search for errors in last 15 min
{
  "query": {
    "bool": {
      "must": [
        {"range": {"@timestamp": {"gte": "now-15m"}}},
        {"match": {"level": "ERROR"}}
      ]
    }
  },
  "aggs": {
    "errors_over_time": {"date_histogram": {"field": "@timestamp", "interval": "1m"}},
    "top_error_messages": {"terms": {"field": "message.keyword", "size": 10}}
  }
}
```

### AWS CloudWatch

```bash
# Lambda error count (last 15 min)
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda --metric-name Errors \
  --dimensions Name=FunctionName,Value=my-function \
  --start-time "$(date -u -d '15 min ago' +%Y-%m-%dT%H:%M:%SZ)" \
  --end-time "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --period 60 --statistics Sum

# RDS CPU utilization
aws cloudwatch get-metric-statistics \
  --namespace AWS/RDS --metric-name CPUUtilization \
  --dimensions Name=DBInstanceIdentifier,Value=my-db \
  --start-time "$(date -u -d '30 min ago' +%Y-%m-%dT%H:%M:%SZ)" \
  --end-time "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --period 300 --statistics Average
```
