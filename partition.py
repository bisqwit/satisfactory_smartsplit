# Written by ChatGPT
from fractions import Fraction
from math import gcd
from typing import List, Optional, Tuple, Generator, Set

def lcm(a: int, b: int) -> int:
    return a // gcd(a, b) * b

def compute_scale(nums: List[float]) -> int:
    den = 1
    for x in nums:
        fr = Fraction(x).limit_denominator()
        den = lcm(den, fr.denominator)
    return den

def to_scaled_ints(nums: List[float]) -> Tuple[List[int], int]:
    scale = compute_scale(nums)
    arr = [int(Fraction(x).limit_denominator() * scale) for x in nums]
    return arr, scale

def build_dp_sets(arr: List[int]) -> List[Set[int]]:
    """
    dp[i] = set of sums reachable using first i items (indices 0..i-1)
    """
    n = len(arr)
    dp = [set() for _ in range(n + 1)]
    dp[0].add(0)
    for i in range(1, n + 1):
        x = arr[i-1]
        # copy previous sums
        dp[i] |= dp[i-1]
        # add sums formed by including x
        for s in dp[i-1]:
            dp[i].add(s + x)
    return dp

def enumerate_subsets_summing(dp: List[Set[int]], arr: List[int], target: int) -> Generator[List[int], None, None]:
    """
    Enumerate subsets (as index lists) that sum to target using dp table for pruning.
    Yields index lists in arbitrary order. Uses backtracking from dp.
    """
    n = len(arr)

    def backtrack(i: int, t: int, path: List[int]):
        # i: consider first i elements (0..i-1), we aim to form sum t
        if t == 0:
            yield list(reversed(path))
            return
        if i == 0:
            return
        # If sum t is achievable without using element i-1, we can skip it
        if t in dp[i-1]:
            # branch: do not take arr[i-1]
            yield from backtrack(i-1, t, path)
        # If t - arr[i-1] achievable without arr[i-1], we can take it
        prev_t = t - arr[i-1]
        if prev_t >= 0 and prev_t in dp[i-1]:
            path.append(i-1)
            yield from backtrack(i-1, prev_t, path)
            path.pop()

    # If target not reachable at all, nothing to yield
    if target not in dp[n]:
        return
        yield  # make this a generator in structure (never reached)
    yield from backtrack(n, target, [])

def subset_sum_indices_once(arr: List[int], target: int) -> Optional[List[int]]:
    """Simple single-subset finder using dp with predecessor (used for second-stage quick check)."""
    if target < 0:
        return None
    n = len(arr)
    prev = {0: None}  # sum -> index used to first create this sum
    for i, x in enumerate(arr):
        # iterate snapshot of keys
        for s in list(prev.keys()):
            s2 = s + x
            if s2 > target:
                continue
            if s2 not in prev:
                prev[s2] = i
            if s2 == target:
                break
        if target in prev:
            break
    if target not in prev:
        return None
    # reconstruct
    indices = []
    s = target
    while s != 0:
        i = prev[s]
        indices.append(i)
        s -= arr[i]
    indices.reverse()
    return indices

def find_2_or_3_way_partition(nums: List[float]) -> Optional[Tuple[int, List[List[float]]]]:
    """
    Try to partition nums into 2 or 3 groups of equal sum.
    Returns (k, groups) where groups are lists of original floats, or None.
    """
    if not nums:
        return None

    arr, scale = to_scaled_ints(nums)
    total = sum(arr)

    # ------------- try 2-way -------------
    if total % 2 == 0:
        half = total // 2
        idxs = subset_sum_indices_once(arr, half)
        if idxs is not None:
            used = set(idxs)
            A = [nums[i] for i in idxs]
            B = [nums[i] for i in range(len(nums)) if i not in used]
            return 2, [A, B]

    # ------------- try 3-way -------------
    if total % 3 == 0:
        third = total // 3
        dp = build_dp_sets(arr)
        if third not in dp[len(arr)]:
            return None  # no subset even for first third

        # Enumerate candidate first subsets; for each, check if remainder contains a subset summing to third.
        # Stop at first success.
        for subset1 in enumerate_subsets_summing(dp, arr, third):
            used1 = set(subset1)
            remaining_arr = [arr[i] for i in range(len(arr)) if i not in used1]
            remaining_idx_map = [i for i in range(len(arr)) if i not in used1]

            # Quick check: if remaining sum != 2*third, skip (shouldn't happen but safe)
            if sum(remaining_arr) != 2 * third:
                continue

            # Try to find one subset in remaining that makes third
            idxs2_rel = subset_sum_indices_once(remaining_arr, third)
            if idxs2_rel is not None:
                # map back to original indices
                subset2 = [remaining_idx_map[i] for i in idxs2_rel]
                used12 = used1 | set(subset2)
                subset3 = [i for i in range(len(arr)) if i not in used12]
                A = [nums[i] for i in subset1]
                B = [nums[i] for i in subset2]
                C = [nums[i] for i in subset3]
                return 3, [A, B, C]
        # exhausted all candidate first subsets
    return None
