# Written by ChatGPT
from typing import List, Optional, Tuple
import math

def find_three_way_cut(x: List[float], eps=1e-9
                      ) -> Optional[Tuple[int,int,float,float,float]]:
    """
    Find indices i < j and fractions alpha, beta (each in [0,1]) such that:
      A = sum(x[0:i]) + alpha * x[i]
      B = (1-alpha)*x[i] + sum(x[i+1:j]) + beta * x[j]
      C = (1-beta)*x[j] + sum(x[j+1:])

    (Here i and j are zero-based indices for the *split elements* x[i] and x[j].)
    Returns (i, j, alpha, beta, common_sum) on success, or None if impossible.
    """
    n = len(x)
    if n < 3:
        return None

    # prefix sums P[t] = sum of x[0..t-1], P[0]=0, P[n]=total
    P = [0.0]*(n+1)
    for t in range(1, n+1):
        P[t] = P[t-1] + x[t-1]

    total = P[n]

    # iterate i from 0..n-2 (x[i] is the element split between A/B),
    # j from i+1..n-1 (x[j] is the element split between B/C)
    for i in range(0, n-1):
        for j in range(i+1, n):
            # a = x[i], b = x[j] (these are the split elements in our notation)
            a = x[i]
            b = x[j]

            # convert to notation used in derivation:
            # recall prefix sums P[t] use 1-based in math; here P indices already adjusted:
            # math's P[i] = sum up to x_i, which is P[i] in our array if i is count.
            # Using the derivation mapping we want:
            # A = P[j] - 2*P[i]
            # B = P[n] + P[i+1] - 2*P[j]
            A = P[j+1] - 2.0 * P[i+1]    # careful: derivation used 1-based; this aligns with zero-based indexing mapping
            B = P[n] + P[i+1] - 2.0 * P[j+1]

            # NOTE on indexing: The derivation assumed x_{i+1} and x_{j+1} as the split elements
            # when using 1-based indices. We here use zero-based x[i] and x[j] and adjusted A,B accordingly.
            # If you prefer to reason with 1-based prefixes, shift indices appropriately.

            # Solve linear system; determinant = 5*a*b (derived). Handle degenerate a or b = 0.
            alpha = None
            beta  = None

            # tolerances for considering a or b zero
            if abs(a) > eps and abs(b) > eps:
                # closed form:
                alpha = (2.0*A + B + a) / (5.0 * a)
                beta  = (-A + 2.0*B + 2.0*a) / (5.0 * b)
            else:
                # handle degenerate cases by solving the original two linear equalities directly.
                # Build the two linear equations in alpha and beta and solve reliably.
                # Equations (in zero-based, consistent with A,B,a,b above):
                # eq1: 2*a*alpha - b*beta = A
                # eq2: a*alpha + 2*b*beta = B + a
                # We attempt to solve them with safe branching.
                # Several subcases:
                if abs(a) <= eps and abs(b) <= eps:
                    # both split-elements are zero -> all three groups sums are integer sums of remaining elements.
                    # Check whether the sums of integer-assigned parts are equal:
                    sumA = P[i]  # sum up to x[i-1]
                    sumB = (P[j] - P[i+1])  # x[i+1]..x[j-1] (zero-based)
                    sumC = P[n] - P[j+1]
                    if abs(sumA - sumB) <= eps and abs(sumB - sumC) <= eps:
                        # any alpha,beta are fine; return 0,0
                        return (i, j, 0.0, 0.0, sumA)
                    else:
                        continue

                # if a is zero, eq1 reduces to -b*beta = A  => beta = -A/b
                if abs(a) <= eps and abs(b) > eps:
                    beta = -A / b
                    # eq2 then a*alpha + 2*b*beta = B + a  -> a*alpha = B + a - 2*b*beta
                    # but a==0 so RHS must be zero for consistency
                    rhs = B + a - 2.0*b*beta
                    if abs(rhs) > 1e-6:
                        continue
                    alpha = 0.0  # arbitrary, because a==0 contributes nothing
                elif abs(b) <= eps and abs(a) > eps:
                    # if b==0, eq2 reduces to a*alpha = B + a  => alpha = (B + a)/a
                    alpha = (B + a) / a
                    # eq1 then 2*a*alpha = A  => check consistency
                    if abs(2.0*a*alpha - A) > 1e-6:
                        continue
                    beta = 0.0  # arbitrary since b==0
                else:
                    # fallback numeric solve (shouldn't reach here)
                    det = 5.0 * a * b
                    if abs(det) <= eps:
                        continue
                    alpha = (2.0*A + B + a) / (5.0*a)
                    beta  = (-A + 2.0*B + 2.0*a) / (5.0*b)

            # check alpha,beta exist and in [0,1]
            if alpha is None or beta is None:
                continue
            if not (-eps <= alpha <= 1.0 + eps and -eps <= beta <= 1.0 + eps):
                continue

            # clamp for numeric
            alpha = max(0.0, min(1.0, alpha))
            beta  = max(0.0, min(1.0, beta))

            # compute the three sums and verify equality
            sumA = P[i] + alpha * a
            sumB = (1.0 - alpha) * a + (P[j] - P[i+1]) + beta * b
            sumC = (1.0 - beta) * b + (P[n] - P[j+1])

            if abs(sumA - sumB) <= 1e-7 and abs(sumB - sumC) <= 1e-7:
                return (i, j, alpha, beta, sumA)

    # nothing found -> impossible under these "single-split" constraints
    return None

def split_into_three_groups(x: List[float], eps=1e-12
    ) -> Optional[Tuple[int, float, int, float, float]]:
    """
    Finds a three-way ordered split of x into A,B,C such that all three groups
    have equal total sum after allowing a fractional split of at most one element
    at the A/B boundary and at most one element at the B/C boundary.

    Returns:
        (i, alpha, j, beta, target_sum)
        where
            - A consists of x[0 .. i-1] plus alpha * x[i]
            - B consists of (1-alpha) * x[i], x[i+1 .. j-1], plus beta * x[j]
            - C consists of (1-beta) * x[j], x[j+1 .. end]
        and all three sums equal target_sum.

    If impossible, returns None.
    """

    n = len(x)
    if n < 3:
        return None

    # Prefix sums S[k] = sum of x[0 .. k-1]
    S = [0.0] * (n + 1)
    for k in range(1, n + 1):
        S[k] = S[k-1] + x[k-1]

    total = S[n]
    target = total / 3.0

    # ----------------------------------------------------------------------
    # Find i, alpha such that A = S[i] + alpha * x[i] == target
    # i ranges 0 .. n-2 because we need at least two more segments
    # ----------------------------------------------------------------------
    i = None
    alpha = None

    for k in range(0, n-1):
        a = x[k]
        before = S[k]   # sum of A before fractional element

        if abs(a) <= eps:
            # x[k] == 0 → alpha contributes nothing
            # Feasible only if S[k] == target
            if abs(before - target) <= eps:
                i = k
                alpha = 0.0  # arbitrary
                break
            else:
                continue
        else:
            ak = (target - before) / a
            if -eps <= ak <= 1.0 + eps:
                i = k
                alpha = max(0.0, min(1.0, ak))
                break

    if i is None:
        return None  # no feasible A/B boundary

    # Compute the fixed part of B that depends only on i and alpha
    B_fixed = (1.0 - alpha) * x[i]
    # After integer elements up to j-1:
    # sum(B integer part up to j) = B_fixed + (S[j] - S[i+1])

    # ----------------------------------------------------------------------
    # Find j, beta such that B == target
    # j ranges i+1 .. n-1
    # ----------------------------------------------------------------------
    j = None
    beta = None

    for k in range(i+1, n):
        b = x[k]
        B_without_beta = B_fixed + (S[k] - S[i+1])

        if abs(b) <= eps:
            if abs(B_without_beta - target) <= eps:
                j = k
                beta = 0.0  # arbitrary
                break
            else:
                continue
        else:
            bk = (target - B_without_beta) / b
            if -eps <= bk <= 1.0 + eps:
                j = k
                beta = max(0.0, min(1.0, bk))
                break

    if j is None:
        return None  # no feasible B/C boundary

    # If we've reached here, both boundaries are valid
    return i, alpha, j, beta, target


def split_into_two_groups(x: List[float], eps=1e-18
    ) -> Optional[Tuple[int, float, float]]:
    """
    Find a two-way ordered split of x into A,B such that both groups
    have equal total sum after allowing a fractional split of at most
    one element at the boundary.

    Returns:
        (i, alpha, target_sum)
        where
            - A = x[0 .. i-1] + alpha * x[i]
            - B = (1-alpha) * x[i] + x[i+1 .. end]
        If impossible, returns None.
    """

    n = len(x)
    if n < 1:
        return None

    # Prefix sums
    S = [0] * (n + 1)
    for k in range(1, n + 1):
        S[k] = S[k-1] + x[k-1]

    total = S[n]
    target = total / 2.0

    # Scan for boundary
    for k in range(0, n):
        a = x[k]
        before = S[k]

        if abs(a) <= eps:
            # zero element
            if abs(before - target) <= eps:
                return k, 0.0, target
            else:
                continue
        else:
            alpha = (target - before) / a
            if -eps <= alpha <= 1.0 + eps:
                alpha = max(0.0, min(1.0, alpha))
                return k, alpha, target

    return None  # impossible


if __name__ == "__main__":
    print("---------")
    x = [9,9,9]

    result = split_into_three_groups(x)
    if result is None:
        print("Impossible")
    else:
        i, alpha, j, beta, target = result
        print("i =", i, "alpha =", alpha)
        print("j =", j, "beta =", beta)
        print("Each group sum =", target)
        
        group1 = x[:i]    + [alpha*x[i]]
        group2 = x[i+1:j] + [(1-alpha)*x[i]] + [beta*x[j]]
        group3 = x[j+1:]  + [(1-beta)*x[j]]
        print(group1,sum(group1))
        print(group2,sum(group2))
        print(group3,sum(group3))

    print("---------")
    x = [3.0, 7.0, 2.0, 5.0, 6.0]
    result = split_into_two_groups(x)
    if result is None:
        print("Impossible")
    else:
        i, alpha, target = result
        print("Split at index:", i)
        print("Fractional split alpha:", alpha)
        print("Each group sum:", target)
        group1 = x[:i]   + [alpha*x[i]]
        group2 = x[i+1:] + [(1-alpha)*x[i]]
        print(group1,sum(group1))
        print(group2,sum(group2))
