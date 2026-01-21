import numpy as np
from pydantic import BaseModel


class ArrayParams(BaseModel):
    n: int
    min_num: int
    max_num: int
    allow_duplicates: bool = True

def generate_array(params: ArrayParams) -> list[int]:
    """Generates an array of random integers based on the given parameters."""
    if params.n <= 0:
        raise ValueError("Expected n > 0")
    if params.min_num >= params.max_num:
        raise ValueError("Expected min_num < max_num")
    start = params.min_num # Min of range
    end = params.max_num + 1   # Max of range and + 1 to be inclusive
    if not params.allow_duplicates and params.n >= (end - start):
        raise ValueError("Not enough unique numbers in the specified range")
    rng = np.random.default_rng()
    return rng.choice(
        np.arange(start, end), size=params.n, replace=params.allow_duplicates
    ).tolist()




