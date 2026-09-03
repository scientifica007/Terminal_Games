# Performance and GitHub Authentication Retrospective

This document records two incidents encountered while developing and testing Terminal_Games:

1. intermittent input stalls in 2048 after exceeding the persisted Best Score;
2. GitHub refusing `git fetch` as an unauthenticated download even though GitHub CLI was already authenticated.

The purpose is not only to preserve the fixes, but also to record the diagnostic path, the evidence that mattered, failed approaches, trade-offs, and reusable engineering rules.

---

## 1. 2048 stalls after exceeding Best Score

### Symptom

2048 normally responded immediately to input, but during some sessions it appeared to stop responding for a short time and then continue. The behavior was intermittent rather than a deterministic freeze.

The decisive observation from manual testing was that the stalls started only after the current run exceeded the previously persisted Best Score.

That timing narrowed the search substantially: ordinary movement and merge logic had already been running before the problem appeared, while Best Score persistence changed behavior exactly at the threshold where the pauses began.

### Why the board algorithm was unlikely to be the cause

2048 operates on a 4x4 board. A move processes only sixteen cells and performs a small number of list transformations and merges. The computational cost is effectively constant and far too small to explain human-visible pauses on normal hardware.

This made CPU complexity an unlikely primary suspect. The more relevant question was what external or blocking work occurred when the score crossed the record.

### Root cause

The shared progress system stored data in:

```text
~/.terminal_games/progress.json
```

Before the fix, 2048 performed persistence work in the gameplay path:

- the displayed Best Score could be read from the JSON store while rendering turns;
- whenever the current score exceeded the stored record, `update_best_score()` synchronously read and rewrote the progress file;
- the write used the safe atomic-write strategy: create a temporary file beside the destination and replace the destination with `os.replace()`.

The atomic write behavior was correct for data integrity, but it was being invoked at the wrong architectural layer. Filesystem I/O is blocking and has variable latency. A disk write that usually finishes quickly can occasionally pause because of filesystem activity, storage latency, scheduling, antivirus/indexing behavior, virtualized storage, or other operating-system effects.

The result was a classic hot-path I/O problem: a real-time user interaction path performed synchronous persistence work whose latency was not bounded by the game logic.

This also explains the user's observation precisely. Before beating the old record, no new Best Score needed to be written. After beating it, additional scoring moves could repeatedly produce new records and therefore repeated writes.

### The same latent problem in Snake

The review found the same architectural risk in Snake. Snake is more sensitive because its game loop advances according to time rather than waiting for an Enter-terminated command. Persisting a new Best Score directly when food is eaten can delay a tick and make movement feel uneven.

The fix therefore covered both 2048 and Snake rather than treating the visible 2048 symptom as an isolated special case.

---

## 2. Architectural fix: separate observation from persistence

The solution was to introduce a shared in-memory `BestScoreTracker` in `games/progress.py`.

Conceptually, the tracker separates three operations that had previously been coupled:

1. **Load once** — read the persisted Best Score when the round starts.
2. **Observe many times** — compare new scores in memory during gameplay.
3. **Flush occasionally** — write the highest observed record only at an explicit safe I/O point.

The tracker maintains both the last persisted value and the current in-memory best. During normal gameplay, `observe(score)` changes only RAM. It does not read or write the JSON file.

Persistence is deferred until a point where a short blocking operation is acceptable:

- explicit `SAVE`;
- normal quit;
- game over / end of round.

### Effect in 2048

During a scoring move, 2048 now performs essentially:

```python
score += gained
best.observe(score)
```

The value shown as Best Score is taken from the tracker already held in memory. There is no progress-file read or write in the merge path.

When the player explicitly saves or exits, the tracker is flushed. If no new record exists, the flush is a no-op.

### Effect in Snake

When Snake eats food, its score and in-memory Best Score are updated without filesystem access. The disk write is postponed to save, quit, interruption handling, or the end of the run.

This keeps the real-time tick path deterministic with respect to persistence: eating food no longer introduces disk latency into movement timing.

---

## 3. Why explicit Save remains synchronous

The objective was not to eliminate synchronous persistence everywhere. The objective was to remove it from latency-sensitive gameplay paths.

An explicit Save command is different. The player has requested durable state and can reasonably expect the command not to report success until the data has been written. A short I/O pause at that moment is semantically acceptable.

This distinction is important:

> Blocking I/O is not inherently wrong. Blocking I/O in a latency-sensitive hot path is the problem.

The current design therefore deliberately keeps explicit Save synchronous.

---

## 4. Durability trade-off

Buffering Best Score in memory introduces a deliberate trade-off.

If the process is killed abruptly, the terminal is forcibly closed, or the machine loses power after a new record is achieved but before Save, normal quit, or game over, the newest record may not have reached disk.

That is preferable to repeated synchronous writes on every scoring event for these terminal games, because responsiveness is part of the gameplay contract.

If future requirements demand stronger crash durability, the next design should not restore per-score writes. Better options include:

- a debounced write, for example at most once every several seconds;
- an asynchronous persistence worker;
- a transaction/batch API that writes state and Best Score together at safe boundaries.

Any such change should preserve the rule that the game tick itself must not wait on storage.

---

## 5. Verification of the 2048 fix

The fix was covered at two levels.

### Automated tests

Regression tests verify that:

- `BestScoreTracker.observe()` does not call persistence;
- a dirty tracker flushes the highest observed score once;
- a clean tracker does not write unnecessarily;
- a loaded game's score can seed an in-memory record higher than the already persisted value;
- a 2048 round buffers a newly achieved record and flushes it on quit.

The GitHub Actions test workflow passed on the exact PR head before merge.

### Manual test

The manual reproduction was intentionally based on the original failure condition:

1. remove the old Best Score;
2. play and establish a new Best Score;
3. save it;
4. start playing again;
5. exceed the persisted record;
6. continue making moves after exceeding it;
7. confirm that the previous pauses no longer occur;
8. save/quit;
9. restart the game and confirm that the new record was persisted.

The test passed. The performance symptom disappeared, and the record remained present after restarting.

The resulting fix was merged through PR #8 as:

```text
ef8578a perf: remove Best Score disk I/O from gameplay loops
```

---

## 6. Reusable performance rules from the incident

For future terminal games in this repository:

- Do not perform filesystem writes in animation loops, real-time ticks, key-handling hot paths, or frequently repeated scoring paths.
- Load persistent metadata once per session/round when practical, then cache it in memory.
- Separate state mutation from persistence. A score changing does not automatically mean the disk must be updated immediately.
- Define explicit safe I/O points: Save, quit, game over, menu transitions, or other non-time-critical boundaries.
- When a slowdown correlates with a state threshold such as "only after beating the record", investigate the side effects activated by that threshold before optimizing the core algorithm.
- Test performance fixes using the exact triggering condition, not merely by starting the game and observing that it launches.
- For real-time games, treat variable-latency external operations as part of timing design, not merely as storage implementation details.

---

# 7. GitHub authentication incident

## Symptom

While attempting to fetch the branch containing the Best Score fix, Git reported:

```text
fatal: remote error: GitHub is temporarily limiting some unauthenticated downloads to protect the stability of the platform. Please retry later or authenticate.
```

Because `git fetch origin` failed, the new remote branch was not learned locally. Subsequent attempts such as:

```bash
git switch --track origin/fix/best-score-io-stalls
```

failed with:

```text
fatal: invalid reference: origin/fix/best-score-io-stalls
```

The second error was only a consequence of the first. The local repository could not reference a remote branch it had not successfully fetched.

---

## 8. Authentication state was more subtle than "logged in or not"

GitHub CLI authentication itself was valid:

```text
Logged in to github.com account scientifica007
Git operations protocol: https
Token scopes: gist, read:org, repo, workflow
```

The repository remote was also normal HTTPS:

```text
https://github.com/scientifica007/Terminal_Games.git
```

Git configuration showed multiple credential-helper entries, including the GitHub CLI credential helper.

Running `gh auth login` again therefore did not solve the problem: the account was already authenticated.

Likewise, SSH was not an immediate fallback because:

```bash
ssh -T git@github.com
```

reached GitHub but ended with:

```text
Permission denied (publickey).
```

That means GitHub's SSH host was reachable, but no accepted SSH key was configured for the account on that machine.

---

## 9. Important diagnostic distinction: `ls-remote` succeeded while `fetch` failed

An explicit GitHub CLI credential helper allowed this command to succeed:

```bash
git -c credential.helper= \
    -c credential.helper='!/usr/bin/gh auth git-credential' \
    ls-remote origin HEAD
```

It returned the correct current `HEAD` SHA.

However, the analogous `fetch` command still received the unauthenticated-download limitation.

This observation matters because `ls-remote` and `fetch` do not perform identical work. `ls-remote` primarily obtains reference advertisements, whereas `fetch` proceeds into object negotiation and pack transfer. Success of the former proves that credentials can be obtained and that the repository is reachable, but it does not guarantee that the entire smart-HTTP fetch path is being authenticated in the same way or at the same stage.

We should not claim knowledge of GitHub's internal rate-limit implementation from this experiment alone. The evidence supports a narrower conclusion:

> The normal credential-helper flow was insufficient for this fetch under the observed GitHub limitation, while sending an Authorization header proactively made the same fetch succeed.

---

## 10. Solution that worked: preemptive Authorization header

The successful workaround built an HTTP Basic Authorization value from the token already managed by `gh`, placed it in a temporary Git configuration file, used that configuration for one fetch, and deleted it immediately afterward.

```bash
cd ~/Terminal_Games

auth="$(printf 'x-access-token:%s' "$(gh auth token)" | base64 -w0)"
tmp="$(mktemp)"
chmod 600 "$tmp"

git config --file "$tmp" \
  http.https://github.com/.extraheader \
  "AUTHORIZATION: basic $auth"

GIT_CONFIG_GLOBAL="$tmp" git fetch origin

status=$?
rm -f "$tmp"
unset auth
echo "fetch status: $status"
```

This succeeded and downloaded the branch and updated `origin/main`.

The repository could then be synchronized normally without a merge commit:

```bash
git switch main
git merge --ff-only origin/main
```

The final local state became:

```text
## main...origin/main
ef8578a (HEAD -> main, origin/main, origin/HEAD) perf: remove Best Score disk I/O from gameplay loops
```

---

## 11. Why this workaround is safer than storing the header permanently

The Authorization header contains a reversible Base64 encoding of the token credential. Base64 is encoding, not encryption.

Therefore the header should not be committed, echoed, pasted into documentation with a real value, or stored permanently in repository/global Git configuration.

The workaround limits exposure by:

- obtaining the token from `gh` rather than printing it manually;
- writing the header only to a `mktemp` file;
- restricting that file with `chmod 600`;
- using the temporary file for a single Git invocation;
- deleting the file immediately;
- unsetting the shell variable afterward.

The shell history records the command text, but not the runtime token value because the token is obtained through command substitution.

If the command is interrupted before cleanup, the temporary file should be located and removed. For a reusable script, a shell `trap` would be an improvement so cleanup occurs on exit or interruption.

---

## 12. A more robust reusable form

If this workaround needs to be used again, a function with guaranteed cleanup is preferable:

```bash
github_authenticated_fetch() {
    local auth tmp status

    auth="$(printf 'x-access-token:%s' "$(gh auth token)" | base64 -w0)" || return
    tmp="$(mktemp)" || return
    chmod 600 "$tmp"
    trap 'rm -f "$tmp"' RETURN

    git config --file "$tmp" \
        http.https://github.com/.extraheader \
        "AUTHORIZATION: basic $auth" || return

    GIT_CONFIG_GLOBAL="$tmp" git fetch origin
    status=$?
    unset auth
    return "$status"
}
```

This is still a fallback, not the preferred permanent authentication architecture.

---

## 13. Preferred long-term Git authentication options

### Option A: make normal HTTPS credential handling reliable

`gh auth setup-git` should normally configure Git to obtain GitHub credentials through GitHub CLI. If ordinary `git fetch` later works consistently again, no special workaround is needed.

When diagnosing HTTPS credential problems, inspect configuration origins rather than only effective values:

```bash
git config --show-origin --get-all credential.helper
git config --show-origin --get-all credential.https://github.com.helper
```

Multiple global, local, blank-reset, and host-specific helper entries can interact. A successful `gh auth status` proves GitHub CLI has credentials; it does not by itself prove that every Git HTTP request is using them as intended.

### Option B: configure SSH properly

SSH avoids HTTPS credential-helper behavior entirely, but it must be configured first. The failed test during this incident showed that no accepted key was available.

A normal SSH setup would require:

1. generate or select a local SSH key;
2. add the public key to the GitHub account;
3. verify with `ssh -T git@github.com`;
4. change the remote to:

```text
git@github.com:scientifica007/Terminal_Games.git
```

Only after successful SSH authentication should the repository remote be switched.

---

## 14. Safe repository recovery procedure used during the incident

Because files from PR #8 had temporarily been copied into a local test branch while `git fetch` was unavailable, synchronization was done conservatively.

Before updating `main`, the local modifications were stashed:

```bash
git stash push -m "manual PR8 test files"
```

After authenticated fetch succeeded:

```bash
git switch main
git merge --ff-only origin/main
```

Once `main` contained the official merged commit and the working tree was clean, the temporary duplicate test state was removed rather than reapplied:

```bash
git stash drop stash@{0}
git branch -D test/best-score-io-stalls
```

This avoided accidentally applying the same code twice or creating conflicts from a test copy of changes already present in `main`.

---

## 15. Reusable Git/GitHub rules from the incident

- Treat the first error in a failed Git sequence as the primary failure. An `invalid reference` after a failed fetch is usually downstream state, not a second independent problem.
- `gh auth status` and Git HTTPS authentication are related but not identical. Verify the Git path directly.
- Use `git ls-remote origin HEAD` as a low-cost connectivity/ref-advertisement test, but do not assume it proves full fetch behavior.
- If credential-helper authentication appears inconsistent, inspect helper configuration with `--show-origin`.
- Do not expose tokens in terminal output, documentation, committed files, or permanent `http.extraheader` configuration.
- A temporary preemptive Authorization header can be a controlled fallback when GitHub is treating the fetch path as unauthenticated despite valid CLI credentials.
- Prefer a temporary config file with mode `600` and guaranteed cleanup.
- Use `git merge --ff-only origin/main` when synchronizing a clean local `main` after fetch; it prevents an accidental merge commit.
- Stash local experimental copies before synchronizing, and do not `stash pop` them if the official merged commit already contains the same changes.
- SSH is a strong long-term alternative, but only after the key is registered and `ssh -T git@github.com` succeeds.

---

# 16. Combined engineering lesson

Although the two incidents were unrelated at the product level, they shared the same diagnostic principle: distinguish the visible symptom from the boundary operation that actually changes behavior.

For 2048, the visible symptom was an input pause, but the relevant boundary was crossing the persisted Best Score and triggering synchronous filesystem I/O.

For GitHub, the visible symptom was a generic unauthenticated-download message, but the relevant boundary was the difference between credentials existing in GitHub CLI and credentials being presented early enough/effectively enough for the actual Git fetch transfer.

In both cases, the useful debugging method was:

1. identify the exact condition under which behavior changes;
2. isolate the external side effect activated at that condition;
3. test the smallest hypothesis that distinguishes competing explanations;
4. fix the architectural boundary rather than masking the symptom;
5. reproduce the original failure condition after the fix;
6. leave the repository in a clean, documented state.
