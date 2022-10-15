from functools import cache
from typing import Hashable, List


class LongestCommonSubsequence:
    @classmethod
    def solve(cls, seq_1: List[Hashable], seq_2: List[Hashable]) -> List[Hashable]:
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

        def trace_reverse(x, y):
            if x == n or y == m:
                return []

            result = dp(x, y)
            if result == dp(x + 1, y):
                return trace_reverse(x + 1, y)

            if result == dp(x, y + 1):
                return trace_reverse(x, y + 1)

            if seq_1[x] == seq_2[y] and result == dp(x + 1, y + 1) + 1:
                tmp = trace_reverse(x + 1, y + 1)
                tmp.append(x)
                return tmp

        dp(0, 0)
        trace_result = trace_reverse(0, 0)
        trace_result.reverse()
        result = [seq_1[x] for x in trace_result]
        return result
