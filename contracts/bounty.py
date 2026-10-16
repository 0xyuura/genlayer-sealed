# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
"""Bounty: a prize pot split equally among every entry Sealed judged PASS.

It holds no model and no web access. Anyone may add to the pot until it is
settled. Settlement waits until Sealed reports the contest's results as final,
because an equal split depends on how many entries passed, and an entry still
waiting for its verdict could change that number. Then every PASS entrant is
credited the same share and withdraws it by pull.

If nobody passed, every funder is credited back exactly what it put in. The
few wei left by integer division go back to the first funder.

On Bradbury a payable write that reverts keeps its value, so a refused top up
credits the value back to the sender instead of reverting.
"""

import json
import typing
from genlayer import *

ERROR_EXPECTED = "[EXPECTED]"
REFUSED = "[REFUSED]"
_HEX = set("0123456789abcdef")


def address_text(value: typing.Any) -> str:
    text = value if isinstance(value, str) else str(value)
    ok = len(text) == 42 and text[:2] == "0x" and set(text[2:].lower()) <= _HEX
    return text.lower() if ok else ""


def split(pot: int, winners: list, funders: list) -> dict:
    """Credits per address. funders is [(address, amount), ...] in order."""
    out = {}
    if pot <= 0:
        return out
    if not winners:
        for who, amt in funders:
            out[who] = out.get(who, 0) + amt
        return out
    share = pot // len(winners)
    for w in winners:
        out[w] = out.get(w, 0) + share
    rest = pot - share * len(winners)
    if rest and funders:
        first = funders[0][0]
        out[first] = out.get(first, 0) + rest
    return out


def _fail(code: str) -> typing.NoReturn:
    raise gl.vm.UserError(ERROR_EXPECTED + " " + code)


@gl.evm.contract_interface
class _Recipient:
    class View:
        pass

    class Write:
        pass


class Bounty(gl.Contract):
    sealed: Address
    contest_id: str
    pot: u256
    settled: bool
    funders: DynArray[str]
    credits: TreeMap[str, u256]

    def __init__(self, sealed: typing.Any, contest_id: str) -> None:
        self.sealed = sealed if isinstance(sealed, Address) else Address(str(sealed))
        self.contest_id = str(contest_id)
        json.loads(gl.get_contract_at(self.sealed).view().get_contest(self.contest_id))
        self.pot = u256(0)
        self.settled = False

    @gl.public.write.payable
    def fund(self) -> str:
        paid = int(gl.message.value)
        if paid == 0:
            _fail("NOTHING_SENT")
        who = address_text(gl.message.sender_address)
        if bool(self.settled):
            self._credit(who, paid)
            return REFUSED + " ALREADY_SETTLED"
        self.pot = u256(int(self.pot) + paid)
        self.funders.append(json.dumps([who, paid]))
        return "FUNDED"

    @gl.public.write
    def settle(self) -> str:
        if bool(self.settled):
            _fail("ALREADY_SETTLED")
        res = json.loads(gl.get_contract_at(self.sealed).view().results(self.contest_id))
        if not res["final"]:
            _fail("NOT_FINAL")
        funders = [tuple(json.loads(str(f))) for f in self.funders]
        for who, amt in split(int(self.pot), list(res["pass"]), funders).items():
            self._credit(who, amt)
        self.settled = True
        return json.dumps({"winners": len(res["pass"]), "pot": str(int(self.pot))})

    @gl.public.write
    def withdraw(self) -> None:
        who = address_text(gl.message.sender_address)
        amount = int(self.credits[who]) if who in self.credits else 0
        if amount == 0:
            _fail("NOTHING_TO_WITHDRAW")
        self.credits[who] = u256(0)
        _Recipient(gl.message.sender_address).emit_transfer(value=u256(amount))

    @gl.public.view
    def credit_of(self, who: typing.Any) -> str:
        key = address_text(who)
        return str(int(self.credits[key]) if key in self.credits else 0)

    @gl.public.view
    def status(self) -> str:
        return json.dumps({"contest_id": str(self.contest_id), "pot": str(int(self.pot)),
                           "settled": bool(self.settled), "funders": len(self.funders)},
                          sort_keys=True)

    def _credit(self, who: str, amount: int) -> None:
        held = int(self.credits[who]) if who in self.credits else 0
        self.credits[who] = u256(held + amount)
