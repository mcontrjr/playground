import pytest
from src.generator import generate_array, ArrayParams


@pytest.mark.parametrize("length_params", [
    ArrayParams(n=5, min_num=1, max_num=10, allow_duplicates=True),
    ArrayParams(n=100, min_num=-10, max_num=10, allow_duplicates=True),
    ArrayParams(n=1, min_num=0, max_num=100, allow_duplicates=False),
    ArrayParams(n=0, min_num=0, max_num=100, allow_duplicates=False)
    ]
)

def test_generator_length(length_params):
    if length_params.n == 0:
        print("N is 0")
        with pytest.raises(ValueError) as e:
            generate_array(length_params)
            assert str(e.value) == "Expected n > 0"
    else:
        arr = generate_array(length_params)
        assert len(arr) == length_params.n, f"Expected length {length_params.n}, got {len(arr)}"


@pytest.mark.parametrize("range_exc_params", [
    ArrayParams(n=20, min_num=10, max_num=10, allow_duplicates=True),
    ArrayParams(n=20, min_num=100, max_num=10, allow_duplicates=True),
    ArrayParams(n=201, min_num=-100, max_num=100, allow_duplicates=False)
    ]
)

def test_generator_range(range_exc_params):
    with pytest.raises(ValueError) as e:
        generate_array(range_exc_params)
        if range_exc_params.min_num >= range_exc_params.max_num:
            assert str(e.value) == "Expected min_num < max_num"
        else:
            assert str(e.value) == "Not enough unique numbers in the specified range"


@pytest.mark.parametrize("value_params",
    [
        ArrayParams(n=100, min_num=0, max_num=10, allow_duplicates=True),
        ArrayParams(n=100000, min_num=-100, max_num=100, allow_duplicates=True),
        ArrayParams(n=1, min_num=10, max_num=11, allow_duplicates=False)
    ]
)

def test_min_max_valuies(value_params):
    arr = generate_array(value_params)
    arr_min = min(arr)
    arr_max = max(arr)
    assert arr_min >= value_params.min_num, f"Expected min >= {value_params.min_num}, got min of {arr_min}"
    assert arr_max <= value_params.max_num, f"Expected max <= {value_params.max_num}, got max of {arr_max}"

