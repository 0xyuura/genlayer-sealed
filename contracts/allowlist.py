# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
"""Allowlist: access for whoever Sealed judged PASS, the moment it is judged.

It holds no model and no web access. An entrant claims a place for itself,
and only for itself, once its own entry carries a PASS verdict. Unlike Bounty
it does not wait for the whole contest to finish: a verdict is permanent, and
granting access to one entrant takes nothing from another, so there is no
reason to make a passing entrant wait for the slowest one.

Bounty waits for the field because money is shared. Access is not.
"""

import json
import typing
from genlayer import *

ERROR_EXPECTED = "[EXPECTED]"
_HEX = set("0123456789abcdef")


def address_text(value: typing.Any) -> str:
    text = value if isinstance(value, str) else str(value)
    ok = len(text) == 42 and text[:2] == "0x" and set(text[2:].lower()) <= _HEX
    return text.lower() if ok else ""


def may_claim(verdict: str, already: bool) -> str:
    if already:
        return "ALREADY_LISTED"
    if verdict == "":
        return "NOT_AN_ENTRANT"
    if verdict != "PASS":
        return "NOT_PASSED"
    return ""


def _fail(code: str) -> typing.NoReturn:
    raise gl.vm.UserError(ERROR_EXPECTED + " " + code)


class Allowlist(gl.Contract):
    sealed: Address
    contest_id: str
    listed: TreeMap[str, u256]
    members: DynArray[str]

    def __init__(self, sealed: typing.Any, contest_id: str) -> None:
        self.sealed = sealed if isinstance(sealed, Address) else Address(str(sealed))
        self.contest_id = str(contest_id)
        json.loads(gl.get_contract_at(self.sealed).view().get_contest(self.contest_id))

    @gl.public.write
    def claim(self) -> None:
        who = address_text(gl.message.sender_address)
        verdict = str(gl.get_contract_at(self.sealed).view().verdict_of(self.contest_id, who))
        reason = may_claim(verdict, who in self.listed)
        if reason:
            _fail(reason)
        self.listed[who] = u256(len(self.members) + 1)
        self.members.append(who)

    @gl.public.view
    def is_listed(self, who: typing.Any) -> bool:
        return address_text(who) in self.listed

    @gl.public.view
    def status(self) -> str:
        return json.dumps({"contest_id": str(self.contest_id),
                           "members": [str(m) for m in self.members]})
