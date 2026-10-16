# Sealed design

## Claim

No entrant in a Sealed contest can read another entry before the commit
window closes, and no entrant can change a single character of its own entry
after it does. Every verdict is reached by consensus against a brief that was
fixed when the contest opened.

## The problem this exists for

Open contests on a public chain leak. If entries are posted in the clear, the
last entrant gets to read everyone else first, copy the best idea, or tune its
own entry to beat the field. If entries can be edited, an entrant can watch
how judging goes and quietly improve its text before its turn. And if the
sponsor can edit the brief, it can move the target after seeing who entered.

Every earlier primitive of this kind judges a document that already exists.
None of them deals with fairness over time: who could see what, and when.

## The move: commit, then reveal, then judge

| Phase | Who | What happens |
| --- | --- | --- |
| Commit | any entrant except the sponsor | publish `sha256(contest, address, salt, text)`, nothing readable |
| Reveal | only the committer | publish salt and text; the contract recomputes the hash |
| Judging | anyone | one consensus call per revealed entry: PASS or FAIL |
| Closed | nobody | results are final |

Phase boundaries are inclusive at the end: a commit at exactly `commit_end` is
still a commit, a reveal one second later is a reveal.

## What the commitment binds

```
sha256( contest_id  0x1f  entrant_address  0x1f  salt  0x1f  exact_text )
```

- **The contest id** stops an entry being replayed into another contest.
- **The entrant's address** is the important one. Without it, a copier could
  publish someone else's commitment and, once that entrant revealed, open it
  with the same salt and text. With it, the copier's reveal hashes to a
  different value and is refused as `COMMIT_MISMATCH`. This attack was run on
  chain.
- **The salt** (16 to 64 characters) stops anyone guessing short entries by
  hashing candidates.
- **The exact text** means a single changed character, even trailing
  whitespace, is a mismatch.

The check is pure hashing on shared state, so a bad reveal is refused before
any model is involved, at no inference cost.

## What validators compare

One name from a closed set: `PASS` or `FAIL`. The reply must be exactly
`{"verdict": "PASS"}` or `{"verdict": "FAIL"}`; anything else is a model error
and stores nothing. Validators rerun the same prompt over the same stored
brief and text and compare with `==`.

Two labels, deliberately. A score would need a tolerance band to reach
agreement, and a band is exactly where a judge can be argued with. Consumers
need to know whether an entry met the brief.

## Who may write

| Write | Who | Policy |
| --- | --- | --- |
| `open_contest` | anyone | the sender becomes the sponsor; brief and windows are fixed forever |
| `commit` | anyone but the sponsor | once per address, only in the commit window, at most 50 entrants |
| `reveal` | the committer | only in the reveal window, only with the matching salt and text |
| `judge` | anyone | contest id and entrant only, only in the judging window, once per entry |

`judge` is open on purpose: the caller supplies no text and no opinion, so
paying for it gives no influence. The sponsor is excluded from entering so it
cannot both set the brief and compete under it.

## Two consumers, two answers to "when is it decided"

| Consumer | Acts on | Waits for |
| --- | --- | --- |
| `Bounty` | the whole PASS list | the contest to be final, because an equal split depends on how many passed |
| `Allowlist` | one entrant's verdict | nothing more, because a verdict is permanent and access is not shared |

Results become final when judging closes, or earlier, as soon as every
revealed entry has a verdict.

## Failure classes

| Class | Example | Result |
| --- | --- | --- |
| Peeking | read entries during the commit window | nothing to read: only hashes are stored |
| Copying a commitment | publish someone else's hash | refused at reveal, `COMMIT_MISMATCH` |
| Editing after the fact | reveal different text | refused, `COMMIT_MISMATCH`, no model call |
| Sponsor entering | the sponsor commits | refused, `SPONSOR_CANNOT_ENTER` |
| Late reveal | after the reveal window | refused, `REVEAL_CLOSED`; the entry stays unrevealed |
| Judging early | during commit or reveal | refused, `REVEAL_RUNNING` |
| Model error | wrong shape or label | `[LLM_ERROR]`, nothing stored, judge again |
| Honest disagreement | validators read the entry differently | nothing stored, judge again |
| Never judged | nobody called judge in time | listed as unjudged; counts as not passing |

## Limits

1. **A verdict is the network's reading of a brief.** A vague brief gives
   vague verdicts. Write requirements an entry can visibly meet.
2. **Sealed hides entries, not entrants.** Commitments are public, so anyone
   can see who entered and when.
3. **A sponsor can still enter through another address.** Excluding the
   sponsor's own address stops the obvious case only.
4. **Entries are public after reveal.** That is the point, but it means an
   entry should contain nothing private.
5. **1,500 characters per entry, 1,200 per brief.** Longer work should be
   summarised, or hosted elsewhere and described in the entry.

## Rejected alternatives

- **Encrypt entries to the sponsor.** The sponsor could read entries early
  and leak them, and validators could not judge what they cannot read.
- **Hash only the text.** Allows copying a commitment and opening it later.
- **Let the sponsor judge.** Puts the verdict back in one party's hands.
- **Score entries 1 to 10.** Needs a tolerance band for agreement, which is
  where disputes live.
- **Let entrants re-commit.** Gives an entrant a way to replace its entry
  after watching who else committed.
