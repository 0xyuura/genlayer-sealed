# Sealed

**Contest entries nobody could copy, judged against a brief nobody could move.**

Live on Testnet Bradbury at
[`0x956f35F171D0094dEdD26a46C3641CB362B942f4`](https://explorer-bradbury.genlayer.com/address/0x956f35F171D0094dEdD26a46C3641CB362B942f4).
Two consumer contracts act on its results in opposite ways; see
[Exercised on chain](#exercised-on-chain).

Call it without a local setup:
[open it in GenLayer Studio](https://studio.genlayer.com/?import-contract=0x956f35F171D0094dEdD26a46C3641CB362B942f4)

## The problem

Open contests on a public chain leak. If entries are posted in the clear, the
last entrant reads everyone else first and copies the best idea. If entries
can be edited, an entrant can watch the judging and quietly fix its text. If
the sponsor can edit the brief, it can move the target after seeing who
entered.

Every earlier primitive of this kind judges a document that already exists.
None deals with fairness over time: who could see what, and when.

## The move

| Phase | Who | What is on chain |
| --- | --- | --- |
| **Commit** | any entrant except the sponsor | `sha256(contest, address, salt, text)`. Nothing readable |
| **Reveal** | only the committer | salt and text; the contract recomputes the hash |
| **Judging** | anyone | one consensus verdict per entry: `PASS` or `FAIL` |
| **Closed** | nobody | results are final |

**The commitment binds the entrant's own address.** Without that, a copier
could publish someone else's commitment and open it once the real entrant
revealed. With it, the copier's reveal hashes to a different value and is
refused. That attack was run on chain, below.

**A bad reveal costs no inference.** The hash check is plain code on shared
state, so one changed character is refused before any model is called.

**Validators compare one name.** The model must answer exactly
`{"verdict": "PASS"}` or `{"verdict": "FAIL"}` against the brief stored at
opening. Validators rerun it and compare with `==`.

## Who may write

| Write | Who | Policy |
| --- | --- | --- |
| `open_contest` | anyone | the sender is the sponsor; brief and windows are fixed forever |
| `commit` | anyone but the sponsor | once per address, only in the commit window, at most 50 |
| `reveal` | the committer | only in the reveal window, only with the matching salt and text |
| `judge` | anyone | contest id and entrant only, judging window only, once per entry |

## Two consumers, two answers to "when is it decided"

| Consumer | Acts on | Waits for |
| --- | --- | --- |
| `Bounty` | the PASS list | the contest to be **final**, because an equal split depends on how many passed |
| `Allowlist` | one verdict | **nothing**, because a verdict is permanent and access is not shared |

Money waits for the field. Access does not.

Full argument in [docs/DESIGN.md](docs/DESIGN.md); interface in
[docs/INTEGRATING.md](docs/INTEGRATING.md).

## Exercised on chain

All three verified byte identical to the files here:

| Contract | Address |
| --- | --- |
| `Sealed` | [`0x956f35F171D0094dEdD26a46C3641CB362B942f4`](https://explorer-bradbury.genlayer.com/address/0x956f35F171D0094dEdD26a46C3641CB362B942f4) |
| `Bounty` (contest `k1`) | [`0x57E9a86C7063F649b115A9c16C7547cCC8fd8cA0`](https://explorer-bradbury.genlayer.com/address/0x57E9a86C7063F649b115A9c16C7547cCC8fd8cA0) |
| `Allowlist` (contest `k1`) | [`0x414963262eA24CFD97625c8082e52Cbb2E479b0A`](https://explorer-bradbury.genlayer.com/address/0x414963262eA24CFD97625c8082e52Cbb2E479b0A) |

Three parties: a **sponsor** `0x6ab9...d72c`, entrant **A** `0xfb33...a67d` and
entrant **B** `0xc221...0bcb`. Brief for both contests: *"Explain in plain
English, for someone new, what a validator does on GenLayer. The entry must say
that validators stake GEN, and that they check a proposed result and vote on
whether it is right."* Windows: 900 s commit, 600 s reveal, 3,600 s judging.

**Contest `k1`, the real one**

| Step | Result |
| --- | --- |
| sponsor opens `k1` | [tx](https://explorer-bradbury.genlayer.com/tx/0x738a5555ecaae65ff12dc6e67e36c9237a0af1a994f04ac673ed083cd4ad2c49) |
| A and B commit hashes; `get_entry` shows `text: ""` | [A](https://explorer-bradbury.genlayer.com/tx/0x8efec5c112504edfd3026854d9892747a0c3879292fa319b84fa96ff6c4f80cb), [B](https://explorer-bradbury.genlayer.com/tx/0x7605ab7c8222d710a12c462e8d5e344df1b7b36e70792d63157c42a9d7bae5eb) |
| sponsor tries to enter its own contest | `[EXPECTED] SPONSOR_CANNOT_ENTER` ([tx](https://explorer-bradbury.genlayer.com/tx/0x3a5410f0fab260f1867844eb857e1bb79b84601524828453bfb28e6b067b7b79)) |
| A reveals a plain validator explanation | [tx](https://explorer-bradbury.genlayer.com/tx/0x33134fb13adb3aec9eba1ccc16cbcaed2c49efc233e25f641ceeba9e5abc7c3e) |
| B reveals "GenLayer is the best chain ever. Buy GEN before it moons." | [tx](https://explorer-bradbury.genlayer.com/tx/0x229c294144aeec2b645fd5ddf721e96d3c4092e72c950595939991ea7779d601) |
| judge A | **PASS** ([tx](https://explorer-bradbury.genlayer.com/tx/0x804835ab27f3e8c99aa6f404be7ca7f83258b3a9700149b6e48423c5da14b739)) |
| judge B | **FAIL** ([tx](https://explorer-bradbury.genlayer.com/tx/0x58629871f480d04bac182bf61e7dcad1b2e61f2f46d93247dfbcee369c51572a)) |

```json
{"final": true, "pass": ["0xfb33...a67d"], "fail": ["0xc221...0bcb"], "unjudged": [], "unrevealed": []}
```

**Contest `k2`, the copy attack**

| Step | Result |
| --- | --- |
| A commits; its commitment is public, its text is not | [tx](https://explorer-bradbury.genlayer.com/tx/0x7ea6d463b8857aeac822b3e2d2f071cef7bf00ad32c7a78d07c856218a86be38) |
| B publishes A's exact commitment as its own | accepted ([tx](https://explorer-bradbury.genlayer.com/tx/0xb8a5058add5b11973607d08c856a6d7cea4f12fc35d92b25af90e903b6616085)) |
| A reveals, so its salt and text are now public | [tx](https://explorer-bradbury.genlayer.com/tx/0xfb4f16b97fa99255413c175ff13da6bee3be4391f533748428fad979e985c403) |
| B reveals with A's salt and A's text | `[EXPECTED] COMMIT_MISMATCH` ([tx](https://explorer-bradbury.genlayer.com/tx/0xe28e151c99156f588b6d517d60e1ce60d8deac70d1bf2885362148e69d804b32)) |

B's copied entry stays `COMMITTED` forever and never reaches a judge.

**The consumers on `k1`**

| Step | Result |
| --- | --- |
| sponsor funds `Bounty` with 0.01 GEN | [tx](https://explorer-bradbury.genlayer.com/tx/0xc7daf7a1b8ee83eba7bbac9f4a2908cc82876fc6c768c64f44e79fee2578ae9c) |
| `settle()` after results were final | the single PASS entrant credited 0.01 GEN ([tx](https://explorer-bradbury.genlayer.com/tx/0x8cb5d6a68346c49e304ca750dc777f473262c5d0c9c1f8b6d9e3bcb11e77e36b)) |
| A withdraws | [tx](https://explorer-bradbury.genlayer.com/tx/0xbb9f231d758c018c9f078b3ce0d5375e6f7bfe1fe6e9a582e41c610461cf4fb1) |
| A claims `Allowlist` | listed ([tx](https://explorer-bradbury.genlayer.com/tx/0x94b0e4ca27dae2fc4ea23f4ca6b89ab3e1fd2bc5ab40f764b44c43695ea08bf3)) |
| B claims `Allowlist` | `[EXPECTED] NOT_PASSED` ([tx](https://explorer-bradbury.genlayer.com/tx/0x00c5cd8eea69b690fd32e680c47cf68b33e21187cf2561f8938257b9ab4d9955)) |

```bash
genlayer call 0x956f35F171D0094dEdD26a46C3641CB362B942f4 results --args k1
genlayer call 0x956f35F171D0094dEdD26a46C3641CB362B942f4 get_entry --args k2 0xc2212086ae937ef00a55f3844998ddfdd2900bcb
genlayer call 0x57E9a86C7063F649b115A9c16C7547cCC8fd8cA0 status
genlayer call 0x414963262eA24CFD97625c8082e52Cbb2E479b0A status
```

A note on the first deployment: `0x0431b5019F2f071809FD718a52521D4386CD534A`
failed at construction because an editor had written a byte order mark before
the `# { "Depends": ... }` header. It was abandoned; nothing ran on it.

## Honest limitations

1. A verdict is the network's reading of the brief. Vague briefs give vague
   verdicts.
2. Sealed hides entries, not entrants: anyone can see who committed and when.
3. A sponsor can still enter through a second address. Only its own address
   is excluded.
4. Entries are public after reveal, so they should contain nothing private.
5. Entries up to 1,500 characters, briefs up to 1,200.
6. An entry nobody judges in time stays unjudged and does not pass.

## Tests

```bash
python -m unittest discover -s tests     # 22 tests, offline, no model, no chain
```

Covers the commitment (every bound part changes the hash, address case does
not), phase boundaries, every refusal code, the results tally and when it is
final, the verdict rule and prompt fence, the full contract flow with the
validator run on every verdict, the copied-commitment attack, both consumers,
and four mutations (a commitment without the address, a sponsor allowed to
enter, judging during reveal, finality before every reveal is judged).

## Layout

```
contracts/sealed.py      the primitive: commit, reveal, judge, results
contracts/bounty.py      consumer: equal split among PASS entries once final
contracts/allowlist.py   consumer: access for each PASS entrant immediately
tests/test_sealed.py     the suite
tools/pay.mjs            payable writes (funding the bounty)
docs/                    DESIGN.md, INTEGRATING.md
```

## Licence

MIT, see [LICENSE](LICENSE).
