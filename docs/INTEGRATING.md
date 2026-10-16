# Integrating Sealed

Sealed is live on Testnet Bradbury at `0x956f35F171D0094dEdD26a46C3641CB362B942f4`.

## 1. Open a contest (sponsor)

```bash
genlayer write 0x956f35F171D0094dEdD26a46C3641CB362B942f4 open_contest --args \
  "Validator in plain English" "<brief, up to 1,200 characters>" 900 600 3600
```

The three numbers are the commit, reveal and judging windows in seconds (60 s
to 30 days each). Returns a contest id such as `k1`. The brief and windows can
never change. Refused: `TITLE_SHAPE`, `BRIEF_SHAPE`, `COMMIT_WINDOW`,
`REVEAL_WINDOW`, `JUDGE_WINDOW`.

## 2. Commit (entrant)

Compute the commitment locally. The view below does it for you; a view call is
not a transaction, so nothing is published:

```bash
genlayer call <sealed> commitment_of --args k1 <your address> <salt> "<your exact text>"
```

or in Python:

```python
hashlib.sha256("\x1f".join([contest_id, address.lower(), salt, text]).encode()).hexdigest()
```

Then publish only the hash:

```bash
genlayer write <sealed> commit --args k1 <64 hex chars>
```

Keep the salt and the exact text. Losing either means you can never reveal.
Salt: 16 to 64 characters from `a-z A-Z 0-9 - _`. Refused: `COMMIT_CLOSED`,
`SPONSOR_CANNOT_ENTER`, `ALREADY_COMMITTED`, `CONTEST_FULL`, `COMMITMENT_SHAPE`.

## 3. Reveal (the same entrant)

```bash
genlayer write <sealed> reveal --args k1 <salt> "<your exact text>"
```

Only during the reveal window. Refused: `REVEAL_NOT_OPEN`, `REVEAL_CLOSED`,
`NOT_COMMITTED`, `ALREADY_REVEALED`, `SALT_SHAPE`, `ENTRY_SHAPE`,
`COMMIT_MISMATCH`.

## 4. Judge (anyone)

```bash
genlayer write <sealed> judge --args k1 <entrant address>
```

Returns `PASS` or `FAIL`, stored permanently. Refused: `REVEAL_RUNNING`,
`JUDGING_CLOSED`, `NOT_REVEALED`, `ALREADY_JUDGED`. A model error
(`[LLM_ERROR] ...`) or a validator disagreement stores nothing; call it again.

## 5. Read results

```bash
genlayer call <sealed> results --args k1
```

```json
{"final": true, "pass": ["0x..."], "fail": ["0x..."], "unjudged": [], "unrevealed": ["0x..."]}
```

`final` is true once judging closes, or as soon as every revealed entry has a
verdict. `verdict_of(contest, address)` returns one entrant's state:
`COMMITTED`, `REVEALED`, `PASS`, `FAIL`, or empty if it never entered.

## Consuming results

| If you | Read | Wait for |
| --- | --- | --- |
| split a prize | `results(...)["pass"]` | `final`, since the count matters |
| grant per-entrant access | `verdict_of(...) == "PASS"` | nothing; a verdict never changes |

`Bounty` and `Allowlist` in this repository are the two reference consumers.
Bounty is funded with GEN through `fund()` (a payable call; use genlayer-js or
`tools/pay.mjs`, since `genlayer write` sends no value).

## Writing a brief that judges well

- List requirements an entry can visibly meet: "must mention staking", not
  "must be insightful".
- One brief, one task. Two tasks in one brief make FAIL ambiguous.
- Say what is out of scope. The judge treats anything unclear as FAIL.
