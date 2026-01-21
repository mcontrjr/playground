import pytest
from src.generator import generate_array, ArrayParams
from src.sorting import (Algorithm, BubbleSort, SelectionSort, InsertionSort, \
                    MergeSort, MyQuickSort, QuickSort, Result)

sorters = [
            BubbleSort(),
            SelectionSort(),
            InsertionSort(),
            MergeSort(),
            MyQuickSort(),
            QuickSort(),
        ]

@pytest.mark.parametrize("sorter", sorters)
def test_sorters(sorter: Algorithm):
    arr = generate_array(ArrayParams(n=100, min_num=0, max_num=10000, allow_duplicates=True))
    sorted_arr = sorter.alg(arr.copy())
    # Test with built-in sorted function
    builtin_sorted = sorted(arr)
    assert sorted_arr == builtin_sorted, f"{sorter.name} did not sort the array correctly."

@pytest.mark.parametrize("sorter", sorters)
def test_results(sorter: Algorithm):
    arr = generate_array(ArrayParams(n=100, min_num=-5000, max_num=5000, allow_duplicates=True))
    alg_result = sorter.record(arr.copy())
    assert type(alg_result) is Result
    assert type(alg_result.elapsed_time) is float, "Expected elapsed_time to be of type float."
    assert alg_result.alg_name == sorter.name, f"Expected name to be {sorter.name}, got {alg_result.alg_name}."
    assert alg_result.result_array == sorted(arr), f"{sorter.name} result array is incorrect."
