# v0.3.0
# { "Depends": "py-genlayer:5jycge4q8k23462jtb0b9fyey1s9qz928sz2nbrd9mg4sxqg2qng" }

# Example CONSUMER of OracleReconciler.
# A gate that only lets an action through if a reconciled price is above a floor
# AND the feed has advanced past a round recorded at configuration time.

import genlayer as gl
from genlayer.types import *


class CollateralGate(gl.contract.Contract):
    oracle: Address
    feed_id: str
    floor: u256          # fixed-point, same decimals as the feed
    min_round: u256      # feed must have reached at least this round
    approvals: u256

    def __init__(self, oracle_address: str, feed_id: str, floor: int, min_round: int):
        self.oracle = Address(oracle_address)
        self.feed_id = feed_id
        self.floor = floor
        self.min_round = min_round
        self.approvals = 0

    @gl.public.write
    def approve(self) -> None:
        # get_value_checked reverts if the feed is stale (round < min_round) or empty
        price = gl.get_contract_at(self.oracle).view().get_value_checked(
            self.feed_id, int(self.min_round)
        )
        if price < int(self.floor):
            raise gl.vm.UserError("price below floor")
        self.approvals = self.approvals + 1

    @gl.public.view
    def get_approvals(self) -> int:
        return int(self.approvals)
