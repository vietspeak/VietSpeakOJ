from utils.lcs import LongestCommonSubsequence


def test_lcs_equal_case():
    seq_1 = [5, 2, 3, 4]
    seq_2 = [5, 2, 3, 4]
    result = LongestCommonSubsequence.solve(seq_1, seq_2)
    assert result == [5, 2, 3, 4]


def test_lcs_diff_len():
    seq_1 = [5, 2, 3, 4]
    seq_2 = [5, 2, 1, 3, 4]
    result = LongestCommonSubsequence.solve(seq_1, seq_2)
    assert result == [5, 2, 3, 4]


def test_lcs_not_full():
    seq_1 = [2, 2, 3, 4, 5, 6]
    seq_2 = [2, 4, 6, 2, 3, 4, 2]
    result = LongestCommonSubsequence.solve(seq_1, seq_2)
    assert result == [2, 2, 3, 4]
    result = LongestCommonSubsequence.solve(seq_2, seq_1)
    assert result == [2, 2, 3, 4]
