from dataclasses import dataclass
from typing import List
from chia.types.blockchain_format.program import Program
from chia.types.blockchain_format.coin import Coin
from chia.types.blockchain_format.program import SerializedProgram, INFINITE_COST
from chia.types.condition_opcodes import ConditionOpcode
from chia.util.chain_utils import additions_for_solution, fee_for_solution
from chia.util.streamable import Streamable, streamable


@dataclass(frozen=True)
@streamable
class CoinSpend(Streamable):
    """
    This is a rather disparate data structure that validates coin transfers. It's generally populated
    with data from different sources, since burned coins are identified by name, so it is built up
    more often that it is streamed.
    """

    coin: Coin
    puzzle_reveal: SerializedProgram
    solution: SerializedProgram

    def additions(self) -> List[Coin]:
        return additions_for_solution(self.coin.name(), self.puzzle_reveal, self.solution, INFINITE_COST)

    def reserved_fee(self) -> int:
        return fee_for_solution(self.puzzle_reveal, self.solution, INFINITE_COST)

    def hints(self) -> List[bytes]:
        h_list = list()
        puzzle = Program.from_bytes(bytes(self.puzzle_reveal))
        solution = Program.from_bytes(bytes(self.solution))
        cost, result = puzzle.run_with_cost(INFINITE_COST, solution)
        for opcode_list in result.as_iter():

            if opcode_list.first() == ConditionOpcode.CREATE_COIN and len(opcode_list.as_python()) > 3:
                # (51 0xcafef00d 200 (hint))
                h_list.append(opcode_list.rest().rest().rest().first().first().as_atom())

        return h_list
