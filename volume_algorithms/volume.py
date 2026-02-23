import numpy as np
import time
from numba import njit, jit
from functools import lru_cache
from functools import lru_cache, wraps


def np_cache(*args, **kwargs):
    """LRU cache implementation for functions whose FIRST parameter is a numpy array
    >>> array = np.array([[1, 2, 3], [4, 5, 6]])
    >>> @np_cache(maxsize=256)
    ... def multiply(array, factor):
    ...     print("Calculating...")
    ...     return factor*array
    >>> multiply(array, 2)
    Calculating...
    array([[ 2,  4,  6],
           [ 8, 10, 12]])
    >>> multiply(array, 2)
    array([[ 2,  4,  6],
           [ 8, 10, 12]])
    >>> multiply.cache_info()
    CacheInfo(hits=1, misses=1, maxsize=256, currsize=1)

    """

    def decorator(function):
        @wraps(function)
        def wrapper(np_array, *args, **kwargs):
            hashable_array = array_to_tuple(np_array)
            return cached_wrapper(hashable_array, *args, **kwargs)

        @lru_cache(*args, **kwargs)
        def cached_wrapper(hashable_array, *args, **kwargs):
            array = np.array(hashable_array)
            return function(array, *args, **kwargs)

        def array_to_tuple(np_array):
            """Iterates recursivelly."""
            try:
                return tuple(array_to_tuple(_) for _ in np_array)
            except TypeError:
                return np_array

        # copy lru_cache attributes over too
        wrapper.cache_info = cached_wrapper.cache_info
        wrapper.cache_clear = cached_wrapper.cache_clear

        return wrapper

    return decorator


def volume_compute(constraints):
    """
    Compute volume based of:
    https://link-springer-com.ezp.sub.su.se/article/10.1007/BF00934543#preview
    """
    print(" ")
    print("###################")
    print("###### START ######")
    print("###################")

    st = time.time()
    dimension = constraints.shape[1] - 1

    def volume_calculation(Abmatrix: np.ndarray, depth) -> float:
        non_zero_mask = ~np.all(Abmatrix[:, 1:] == 0, axis=1)
        if np.any(non_zero_mask == False):
            if np.any(Abmatrix[~non_zero_mask][:, 0] < 0):
                return 0
            else:
                Abmatrix = Abmatrix[non_zero_mask]

        if Abmatrix.shape[1] == 3:

            vol_terms = []
            for i in range(Abmatrix.shape[0]):
                Abrow_i = Abmatrix[i, :]

                if Abrow_i[0] == 0:
                    continue

                for idx, aj in enumerate(Abrow_i[1:], start=1):
                    if aj != 0:
                        ti = idx
                        break

                max_terms, min_terms = [], []
                for k, Abrow_k in enumerate(Abmatrix):
                    if k == i:
                        continue

                    for j, ab_kj in enumerate(Abrow_k):
                        if j == 0:
                            beta = ab_kj - Abrow_k[ti] * Abrow_i[0] / Abrow_i[ti]
                            continue
                        elif j == ti:
                            continue

                        alpha = ab_kj - Abrow_k[ti] * Abrow_i[j] / Abrow_i[ti]

                        xj = beta / alpha

                        if alpha < 0:
                            max_terms.append(xj)
                        else:
                            min_terms.append(xj)

                if len(min_terms) == 0:
                    min_part = 0  # XX Om min_terms är tom borde det bli inf?
                else:
                    min_part = min(min_terms)
                if len(max_terms) == 0:
                    max_part = 0  # XX Om max_terms är tom borde det bli inf?
                else:
                    max_part = max(max_terms)

                vol_terms.append(
                    Abrow_i[0] * max(0, min_part - max_part) / abs(Abrow_i[ti])
                )
            if vol_terms:
                total_volume = sum(vol_terms) / 2
            else:
                total_volume = 0

            return total_volume, Abmatrix.shape[1] - 1
        else:
            print("depth", Abmatrix.shape[1] - 1)

            volume_terms = []
            for i in range(Abmatrix.shape[0]):
                Abtilde = np.zeros(Abmatrix.shape)
                Abrow_i = Abmatrix[i, :]
                for idx, aj in enumerate(Abrow_i[1:]):
                    if aj != 0:
                        ti = idx + 1
                        break

                for k, Abrow_k in enumerate(Abmatrix):
                    if k == i:
                        continue

                    for j, ab_kj in enumerate(Abrow_k):
                        if j == 0:
                            # bk_tilde
                            Abtilde[k, 0] = (
                                ab_kj - Abrow_k[ti] * Abrow_i[0] / Abrow_i[ti]
                            )
                            continue
                        elif j == ti:
                            continue

                        # akj_tilde
                        Abtilde[k, j] = ab_kj - Abrow_k[ti] * Abrow_i[j] / Abrow_i[ti]

                row_mask = np.ones(Abtilde.shape[0], dtype=bool)
                row_mask[i] = 0

                col_mask = np.ones(Abtilde.shape[1], dtype=bool)
                col_mask[ti] = 0

                Abtilde = Abtilde[row_mask, :][:, col_mask]

                print(f"depth ({i}): ", Abtilde.shape[1] - 1)
                volume_term, depth = volume_calculation(Abtilde, Abtilde.shape[1] - 1)

                if volume_term:
                    # print("vol_term: ", Abrow_i[0] * volume_term / abs(Abrow_i[ti]))
                    volume_terms.append(Abrow_i[0] * volume_term / abs(Abrow_i[ti]))

                    # volume_terms.append(volume_term)
            print("Next depth", Abmatrix.shape[1] - 1)
            final_volume = sum(volume_terms) / (Abmatrix.shape[1] - 1)

            return final_volume, depth

    final_vol, iters = volume_calculation(constraints, constraints.shape[1] - 1)

    print("Final volume: ", final_vol)
    print(f"Run time: {time.time()-st}")


if __name__ == "__main__":

    with open("./latte/pbtech/lasserre5d.hrep.latte", "r") as f:
        hrep_content = f.readlines()

    hrep = []
    for constraint in hrep_content[1:]:  # bcs.split("\n") + tcs.split("\n"):
        constraint = constraint.replace("\n", "")
        if len(constraint) == 0:
            continue
        hrep.append([int(val) for val in constraint.split(" ") if len(val) > 0])

    hrep = np.array(hrep)
    print("hrep:", hrep.shape)

    constraints = np.concatenate(
        [np.array(hrep)[:, 0].reshape(hrep.shape[0], 1), -1 * np.array(hrep)[:, 1:]],
        axis=1,
    )
    print(constraints)
    # constraints = np.array(
    #     [
    #         [2, 2, -2, -2],
    #         [3, -4, -2, -2],
    #         [4, -1, 2, 2],
    #         [0, 1, 0, 0],
    #         [0, 0, 1, 0],
    #         [0, 0, 0, 1],
    #     ]
    # )
    volume_compute(constraints)
