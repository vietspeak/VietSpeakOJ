from utils.lcs import LongestCommonSubsequence


def test_lcs_equal_case():
    seq_1 = [5, 2, 3, 4]
    seq_2 = [5, 2, 3, 4]
    result = LongestCommonSubsequence.solve(seq_1, seq_2)
    assert len(result) == 4
    assert result.values == [5, 2, 3, 4]
    assert result.locations == [(i, i) for i in range(4)]


def test_lcs_diff_len():
    seq_1 = [5, 2, 3, 4]
    seq_2 = [5, 2, 1, 3, 4]
    result = LongestCommonSubsequence.solve(seq_1, seq_2)
    assert len(result) == 4
    assert result.values == [5, 2, 3, 4]
    assert result.locations == [(0, 0), (1, 1), (2, 3), (3, 4)]


def test_lcs_not_full():
    seq_1 = [2, 2, 3, 4, 5, 6]
    seq_2 = [2, 4, 6, 2, 3, 4, 2]
    result = LongestCommonSubsequence.solve(seq_1, seq_2)
    assert len(result) == 4
    assert result.values == [2, 2, 3, 4]
    assert result.locations == [(0, 0), (1, 3), (2, 4), (3, 5)]
    result_2 = LongestCommonSubsequence.solve(seq_2, seq_1)
    assert len(result_2) == 4
    assert result_2.values == [2, 2, 3, 4]
    assert result_2.locations == [(y, x) for x, y in result.locations]
