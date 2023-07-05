# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023 Valory AG
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------


"""Custom objects for the MarketManager ABCI application."""

import dataclasses
import json
from typing import Any, Dict, Iterator, List, Optional, Tuple

from aea.helpers.ipfs.base import IPFSHashOnly

from packages.valory.skills.abstract_round_abci.models import ApiSpecs, BaseParams
from packages.valory.skills.abstract_round_abci.models import (
    BenchmarkTool as BaseBenchmarkTool,
)
from packages.valory.skills.abstract_round_abci.models import Requests as BaseRequests
from packages.valory.skills.abstract_round_abci.models import (
    SharedState as BaseSharedState,
)
from packages.valory.skills.market_manager_abci.rounds import MarketManagerAbciApp


Requests = BaseRequests
BenchmarkTool = BaseBenchmarkTool


@dataclasses.dataclass
class Bet:
    """A bet's structure."""

    id: str
    title: str
    creator: str
    fee: int
    openingTimestamp: int
    outcomeSlotCount: int
    outcomeTokenAmounts: List[int]
    outcomeTokenMarginalPrices: List[float]
    outcomes: Optional[List[str]]

    def __post_init__(self) -> None:
        """Post initialization to adjust the optional values."""
        if self.outcomes == "null":
            self.outcomes = None


class BetEncoder(json.JSONEncoder):
    """JSON encoder for a bet."""

    def default(self, o: Any) -> Any:
        """The default encoder."""
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)


class SharedState(BaseSharedState):
    """Keep the current shared state of the skill."""

    abci_app_cls = MarketManagerAbciApp

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the state."""
        # list of bets mapped to prediction markets
        self.bets: Dict[str, List[Bet]] = {}
        super().__init__(*args, **kwargs)

    @property
    def bets_hash(self) -> str:
        """Fetch and update the bets of interest, and return the result's hash."""
        bets = json.dumps(self.bets, cls=BetEncoder).encode()
        return IPFSHashOnly.hash_bytes(bets)


class RandomnessApi(ApiSpecs):
    """A model that wraps ApiSpecs for randomness api specifications."""


class MarketManagerParams(BaseParams):
    """Market manager's parameters."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the parameters' object."""
        # this is a mapping from a prediction market spec's attribute to the creators we want to take into account
        self.creator_per_market: Dict[str, List[str]] = self._ensure(
            "creator_per_subgraph", kwargs, Dict[str, List[str]]
        )
        self.slot_count: int = self._ensure("slot_count", kwargs, int)
        self.opening_margin: int = self._ensure("opening_margin", kwargs, int)
        self.languages: List[str] = self._ensure("languages", kwargs, List[str])
        super().__init__(*args, **kwargs)

    @property
    def creators_iterator(self) -> Iterator[Tuple[str, List[str]]]:
        """Return an iterator of market per creators."""
        return iter(self.creator_per_market.items())
