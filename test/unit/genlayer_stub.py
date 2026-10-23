"""Minimal in-memory stand-in for the `genlayer` package so the contract's
pure logic and its storage flow can be tested off-chain with plain `unittest`.

The stub's run_nondet_unsafe runs the leader, then runs the validator against
the leader's result, and raises ConsensusRejected if the validator says no.
Tests change `STATE.pages` between leader and validator via `STATE.on_validate`
to simulate validators seeing different data than the leader.

This is NOT a GenVM emulator. It only proves the contract logic; run
test/integration against Studio Next to prove real consensus behavior.
"""
import importlib.util
import sys
import types
from pathlib import Path


class ConsensusRejected(Exception):
    pass


class UserError(Exception):
    pass


class Address:
    def __init__(self, value="0x" + "11" * 20):
        self.as_hex = value if isinstance(value, str) else value.as_hex


class _Return:
    def __init__(self, calldata):
        self.calldata = calldata


class _State:
    pages = {}          # url -> page text
    llm = None          # callable(prompt) -> str
    on_validate = None  # callable() run right before the validator executes
    sender = "0x" + "aa" * 20
    now = "2026-10-07T12:00:00Z"


STATE = _State()


def _build():
    gl = types.ModuleType("genlayer")

    class Contract:
        pass

    gl.contract = types.SimpleNamespace(Contract=Contract)

    def write(f):
        return f

    write.payable = write
    gl.public = types.SimpleNamespace(view=lambda f: f, write=write)

    class TreeMap:
        def __class_getitem__(cls, item):
            return dict

    gl.storage = types.SimpleNamespace(TreeMap=TreeMap)

    def run_nondet_unsafe(leader, validator):
        out = leader()
        if STATE.on_validate:
            STATE.on_validate()
        if not validator(_Return(out)):
            raise ConsensusRejected("validator rejected leader result")
        return out

    gl.vm = types.SimpleNamespace(
        UserError=UserError,
        Return=_Return,
        Result=object,
        run_nondet_unsafe=run_nondet_unsafe,
    )

    def render(url, mode="text"):
        if url not in STATE.pages:
            raise RuntimeError("fetch failed: " + url)
        return STATE.pages[url]

    gl.nondet = types.SimpleNamespace(
        web=types.SimpleNamespace(render=render),
        exec_prompt=lambda prompt: STATE.llm(prompt),
    )
    gl.message = types.SimpleNamespace(sender_address=Address(STATE.sender))
    gl.message_raw = {"datetime": STATE.now}

    gtypes = types.ModuleType("genlayer.types")
    gtypes.u256 = int
    gtypes.Address = Address
    gtypes.__all__ = ["u256", "Address"]
    sys.modules["genlayer"] = gl
    sys.modules["genlayer.types"] = gtypes
    return gl


def load_contract_module():
    _build()
    path = Path(__file__).resolve().parents[2] / "contracts" / "oracle_reconciler.py"
    spec = importlib.util.spec_from_file_location("oracle_reconciler", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def new_contract(mod):
    """Instantiate without running the VM; storage maps become plain dicts."""
    c = mod.OracleReconciler.__new__(mod.OracleReconciler)
    c.owner = Address(STATE.sender)
    for name in ("feeds", "latest", "attempts", "rounds", "history", "src_stats"):
        setattr(c, name, {})
    return c
