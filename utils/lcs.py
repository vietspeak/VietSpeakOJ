from dataclasses import dataclass
from functools import cache
from typing import Hashable, List, Tuple


@dataclass
class LCSResult:
    values: List[Hashable]
    locations: List[Tuple[int, int]]

    def __len__(self) -> int:
        return len(self.values)


class LongestCommonSubsequence:
    @classmethod
    def solve(cls, seq_1: List[Hashable], seq_2: List[Hashable]) -> LCSResult:
        n = len(seq_1)
        m = len(seq_2)

        @cache
        def dp(x, y):
            if x == n or y == m:
                return 0

            result = max(dp(x + 1, y), dp(x, y + 1))
            if seq_1[x] == seq_2[y]:
                result = max(result, dp(x + 1, y + 1) + 1)

            return result

        def trace_reverse(x, y) -> List[Tuple[int, int]]:
            if x == n or y == m:
                return []

            result = dp(x, y)
            if result == dp(x + 1, y):
                return trace_reverse(x + 1, y)

            if result == dp(x, y + 1):
                return trace_reverse(x, y + 1)

            if seq_1[x] == seq_2[y] and result == dp(x + 1, y + 1) + 1:
                tmp = trace_reverse(x + 1, y + 1)
                tmp.append((x, y))
                return tmp

        dp(0, 0)
        trace_result = trace_reverse(0, 0)
        trace_result.reverse()
        values = [seq_1[x[0]] for x in trace_result]
        return LCSResult(values, trace_result)
