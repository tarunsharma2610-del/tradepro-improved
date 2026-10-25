## Canonical checkpoint reconciliation — 25 October 2026 (latest exact-head CI verified)

- **Repository:** `tarunsharma2610-del/tradepro-improved` only. **Branch:** `phase3/durable-per-fill-charge-allocation`. **PR #6:** open, draft, unmerged.
- **Latest verified branch head before this documentation sync:** `e9440e2f31f9d4d108b9160608e653efffd2d9fc`. Exact-head Backend CI [run #40210391188](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40210391188) completed successfully on this exact SHA (25 October 2026).
- **Latest verified code/test checkpoint:** `50802e96e06756b57a9f930e0c54c680777922d4`; Backend CI [run #40209741299](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40209741299) passed on that exact SHA.
- **Verified gates:** backend pytest; broker-write safety boundary; SQLite and PostgreSQL 16 migration upgrade/downgrade/re-upgrade; synthetic PostgreSQL/document-volume restore drill. The synthetic restore does not prove actual Oracle Cloud recovery.
- **Concurrency acceptance gap closed:** PostgreSQL coverage races two promotion calls for the same reviewed component alongside verification; both promotions must return the complete allocation set and final reconciled rows must share one durable reference.
- **Next single implementation step:** integrate canonical snapshot allocation/reconciliation end-to-end with live-fill accounting (Phase 3 Gates 1C/5). Current live-fill accounting still validates raw source-component rows through the legacy six-row ledger. Add focused integration coverage for combined/split transaction/IPFT, exact replay, complete totals, and fail-closed rejection of extra/unmapped components. Do not silently drop or double-count charges; do not introduce generic quantity/notional allocation.
- **Remaining gates:** evidence-backed effective-dated tariff selection (Gate 2); approved per-fill rule wiring (Gate 3); invoice/source-backed GST/component acceptance (Gate 4); final adversarial/migration/restore review (Gate 6); final exact-head documentation/sign-off (Gate 7).
- **Upstox controls:** no unused SDK runtime dependency; Agent Skill is static-review-only and must not be executed or supplied live credentials. Brokerage calculator output is estimate-only; aggregate charge endpoints are not per-fill actual evidence. GST/IPFT/tariff candidates remain DRAFT until authentic applicable evidence and independent review support approval.
- **Safety invariants:** original `tarunsharma2610-del/Tradepro` remains out of scope and must stay untouched; PAPER mode mandatory; live broker order writes, automatic live-fill promotion, and automatic scheduling remain disabled. Do not merge PR #6 without explicit user approval.
- **Checkpoint protocol:** this 25-file documentation sync must pass CI on its own resulting commit before the next implementation change. Parent-commit CI does not verify a newer SHA.

---

# Phase 3 — Coordinated PostgreSQL and Contract-Note Restore Drill

Status: **procedure prepared; drill not yet executed**. Do not mark recovery acceptance complete until an operator records an actual isolated restore and audit result.

## Scope and safety

This runbook applies only to the `tradepro-improved` Compose stack. It does not touch the original `Tradepro` repository, production data, or broker settings. Run only against a disposable isolated environment with no live broker credentials and no externally exposed ports. Never test by overwriting a production volume.

Compose declares separate named volumes, `postgres_data` and `broker_charge_documents`. The backend and worker both mount the document volume at `/var/lib/tradepro/contract-notes`. These two data sets must be backed up/restored as one recovery point because database evidence rows refer to files by opaque storage key, size, and SHA-256.

## Preconditions

- Use a disposable clone/host or isolated Compose project name, with outbound broker access disabled and no real broker credentials.
- Confirm the exact Compose project and volume names with `docker compose ls` and `docker volume ls`. Do not guess volume names; Compose prefixes them with the project name unless explicitly named.
- Ensure adequate protected disk space. Treat both backup artifacts as sensitive contract-note data; encrypt at rest and restrict access.
- Record UTC start time, Git commit, Compose project name, image IDs, volume names, and operator.

**Secret-handling note:** Do not save the fully resolved output of `docker compose config` in the backup directory: interpolation can expose the database password in a file that may later be copied or retained. Record the checked-in Compose file hash instead, and store the protected `.env` separately only if required by the recovery policy; never commit it to GitHub.

- Stop API and worker writes before the paired backup; keep the database available for the dump. For a consistent recovery point, stop `backend` and `worker` before capturing both datasets, and do not restart them until both captures finish.

## A. Capture paired backup artifacts

Run from the isolated project directory. Choose a protected backup directory outside the volumes; substitute a unique timestamped directory.

1. Create the directory and record metadata:
   ```sh
umask 077
mkdir -p ./phase3-backup
date -u +%Y-%m-%dT%H:%M:%SZ > ./phase3-backup/captured-at-utc.txt
git rev-parse HEAD > ./phase3-backup/git-commit.txt
docker compose ps > ./phase3-backup/compose-ps.txt
sha256sum ./docker-compose.yml > ./phase3-backup/compose-file-SHA256SUM.txt
```

2. Stop writers and verify they are stopped:
   ```sh
docker compose stop backend worker
docker compose ps
```

3. Dump PostgreSQL in custom format (run `pg_dump` in the database container; do not include passwords in command-line arguments or logs):
   ```sh
docker compose exec -T postgres sh -lc 'PGPASSWORD="$POSTGRES_PASSWORD" pg_dump -h 127.0.0.1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' > ./phase3-backup/postgres.dump
test -s ./phase3-backup/postgres.dump
```

4. Archive the contract-note volume through the backend's read-only mount path. The backend is stopped, so the archive is not racing uploads:
   ```sh
docker compose run --rm -T --no-deps --entrypoint sh backend -lc 'tar -C /var/lib/tradepro/contract-notes -czf - .' > ./phase3-backup/contract-notes.tgz
test -s ./phase3-backup/contract-notes.tgz
```

5. Generate checksums and protect the artifacts:
   ```sh
sha256sum ./phase3-backup/postgres.dump ./phase3-backup/contract-notes.tgz > ./phase3-backup/SHA256SUMS
chmod -R go-rwx ./phase3-backup
```

Restart the source stack only after both backup artifacts have been captured:
```sh
docker compose start backend worker
```

## B. Restore into an isolated target

1. Create a **separate** Compose project/host with the same reviewed application revision and schema compatibility. Confirm target volume names differ from the source. Keep API/worker stopped and ports unexposed.
2. Verify artifacts before reading them:
   ```sh
cd ./phase3-backup
sha256sum -c SHA256SUMS
```
3. Restore the document archive into the target's `broker_charge_documents` volume. Ensure it is empty first; never extract into a volume containing data that must be preserved. One supported method is to start a one-off backend container in the target project and extract the archive into its mounted document root:
   ```sh
docker compose run --rm -T --no-deps --entrypoint sh backend -lc 'tar -C /var/lib/tradepro/contract-notes -xzf -' < ../phase3-backup/contract-notes.tgz
```
4. Restore PostgreSQL into the target database. Start only the target database service; create an empty target database/schema, then use `pg_restore` with the target's database credentials. Review extension/owner requirements for this environment before using `--no-owner` or `--clean`; do not blindly drop objects in a non-disposable database.
   ```sh
docker compose exec -T postgres sh -lc 'PGPASSWORD="$POSTGRES_PASSWORD" pg_restore -h 127.0.0.1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" --no-owner --exit-on-error' < ../phase3-backup/postgres.dump
```
5. Start the target backend only after both restores finish. Do not start the worker until integrity checks pass.

## C. Verify restored evidence-to-file consistency

- Run the application's read-only `audit_contract_note_storage` service against the restored target database and `BROKER_CHARGE_DOCUMENT_ROOT=/var/lib/tradepro/contract-notes`, using an approved administrative command or test harness. Do not invent an API endpoint for this internal service.
- Acceptance requires empty `missing_files`, `integrity_mismatches`, `invalid_storage_keys`, and `unreferenced_files` findings, unless each exception is individually explained and formally accepted.
- For a representative sample and then every referenced evidence row, verify file byte size and SHA-256 against the restored database metadata. Verify source-component fingerprints still equal their parent evidence fingerprints.
- Verify counts of evidence rows, source components, allocation rows, and reconciled references against the source capture metadata. Exercise a read-only retrieval of representative notes; do not promote allocations or place broker orders during the drill.
- Record restore duration, database/object counts, audit output, hashes, errors, corrective actions, and reviewer sign-off in the drill report. Preserve logs without exposing note contents or credentials.

## D. Pass/fail and cleanup

Pass only when both artifacts restore successfully to the isolated target, schema/data checks pass, the storage audit has no unexplained findings, and a second reviewer signs off. Any missing/mismatched/unreferenced file, database restore error, or inability to reproduce evidence metadata is a failure: keep the worker stopped, preserve artifacts/logs, investigate, and repeat with a new isolated target.

After review, securely dispose of the isolated target according to the data-retention policy. Do not delete the only backup artifacts until their retention and restore requirements are satisfied.

## Required evidence record

Record: operator and independent reviewer; UTC timestamps; source/target Compose project names; commit and image IDs; database and document-volume identifiers; artifact SHA-256 values; restore commands/results; row/object counts; full audit findings; pass/fail decision; remediation and sign-off.

**Current checkpoint:** this is a reviewed procedure template, not evidence that any backup or restore has been performed.


## 2026-10-24 — Resolver acceptance and CI checkpoint

- Backend workflow `40108183667` succeeded on prior head `8214430f562f6f425cfc1b9b6a6b3b547832b68a`. New resolver tests add exact broker/endpoint/schema/field/scope matching and non-finite-number rejection; newer commits still require CI.
- Mapping identity fixtures use immutable dataclass replacement. Intended-use semantics remain explicit; missing/null/invalid values remain unusable and retain provenance; numeric zero remains distinct.
- Accounting acceptance includes replay/conflict, ledger reconciliation, lock order, rollback, reviewer authority and PostgreSQL verification/promotion race coverage. Re-check exact test and workflow status before claiming complete. CI does not establish production tariff correctness or broker-origin authenticity.
- Safety gates unchanged: PR #6 draft/unmerged; live broker order submission and automatic quantity/notional allocation disabled; production Upstox mappings/tariffs unapproved. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains untouched.


## 2026-10-24 — Resolver field-identity guard added; CI pending

- Resolver now verifies that the payload field matches the terminal field in the approved mapping path. Implementation `77aa77aec37dc535c3e427ca3f88c2ccb5e75ed8`; regression test `5c5482c7f7fa623707698f64b6a061351e5e5b87`. CI is pending for these and subsequent documentation commits.
- The field-identity guard is a code correctness safeguard, not approval of production Upstox field semantics or tariffs. Existing live-fill tests cover lock order, replay idempotency and rollback; genuine concurrent verification-versus-promotion coverage still needs confirmation.
- PR #6 remains draft/unmerged. Live order submission and automatic quantity/notional allocation remain disabled. Work only in `tradepro-improved`; original `Tradepro` remains untouched.


## 2026-10-24 — Latest resolver CI and PostgreSQL concurrency suite verified

- Backend workflow [#40109041654](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40109041654) passed on head `ed346e823cbfae8448fae0134c4ff864bfcc60ac`: **872 passed, 1 warning**; broker-write boundary guard passed.
- Dedicated PostgreSQL concurrency tests cover competing fill sets, source verification vs allocation promotion, and live-fill promotion vs ledger verification. The successful test summary has no skipped tests, confirming the collected suite ran in CI's synthetic database environment.
- This is not approval of production Upstox tariff/field mappings. PR #6 remains draft/unmerged; live broker order submission and automatic quantity/notional allocation remain disabled; original `Tradepro` remains out of scope.
