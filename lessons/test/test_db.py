import pytest
from unittest.mock import patch
import pandas as pd
from sqlite3 import IntegrityError
from src.db import DatabaseManager, DatabaseResult

@pytest.fixture
def memory_db_path():
    return ":memory:"

@pytest.fixture
def test_db_path():
    return "file:test?mode=memory&cache=private"


@pytest.fixture
def example_result():
    return DatabaseResult(
        n=5,
        alg_name="TestSort",
        elapsed_time=0.123,
        array=[5, 3, 4, 1, 2],
        sorted_array=[1, 2, 3, 4, 5],
        array_id="test_array_001"
    )

@pytest.fixture
def example_results():
    return [
        DatabaseResult(
            n=1,
            alg_name="TestSort1",
            elapsed_time=0.01,
            array=[1],
            sorted_array=[1],
            array_id="array_001"
        ),
        DatabaseResult(
            n=5,
            alg_name="TestSort1",
            elapsed_time=0.05,
            array=[5, 4, 3, 2, 1],
            sorted_array=[1, 2, 3, 4, 5],
            array_id="array_002"
        ),
        DatabaseResult(
            n=5,
            alg_name="TestSort2",
            elapsed_time=0.10,
            array=[5, 4, 3, 2, 1],
            sorted_array=[1, 2, 3, 4, 5],
            array_id="array_002"
        ),
        DatabaseResult(
            n=5,
            alg_name="TestSort3",
            elapsed_time=0.15,
            array=[5, 4, 3, 2, 1],
            sorted_array=[1, 2, 3, 4, 5],
            array_id="array_002"
        ),
        DatabaseResult(
            n=5,
            alg_name="TestSort2",
            elapsed_time=0.02,
            array=[10, 9, 8, 7, 6],
            sorted_array=[6, 7, 8, 9, 10],
            array_id="array_003"
        )
    ]

@pytest.fixture
def single_record_db(test_db_path, example_result):
    with DatabaseManager(test_db_path) as db:
        db.init_db()
        db.add_result(example_result)
        yield db
        db.clear_all_results()

@pytest.fixture
def populated_db(test_db_path, example_results):
    with DatabaseManager(test_db_path) as db:
        db.init_db()
        for res in example_results:
            db.add_result(res)
        yield db
        db.clear_all_results()

def test_context_manager(memory_db_path, example_result):
    with DatabaseManager(memory_db_path) as db:
        db.init_db()
        ex_res = db.add_result(example_result)
        assert ex_res == 1
        df = pd.read_sql_query("SELECT * FROM sort_results", db.conn)
        print(df)


def test_context_manager_rollback(test_db_path, example_result):
    with pytest.raises(Exception):
        with DatabaseManager(test_db_path) as db:
            db.init_db()
            db.add_result(example_result)
            raise Exception("Force rollback")
    with DatabaseManager(test_db_path) as db:
        all_records = db.get_all_results()
        assert len(all_records) == 0

        db.clear_all_results()

def test_add_and_get_result(single_record_db, example_result):
        db_results = single_record_db.get_result(alg_name="TestSort")
        assert len(db_results) == 1
        assert db_results[0] == example_result

def test_get_results_by_name(populated_db):
    test_sort_1_results = populated_db.get_result(alg_name="TestSort1")
    test_sort_2_results = populated_db.get_result(alg_name="TestSort2")
    test_sort_3_results = populated_db.get_result(alg_name="TestSort3")
    assert (len(test_sort_1_results), len(test_sort_2_results), len(test_sort_3_results)) == (2, 2, 1)
    assert all(res.alg_name == "TestSort1" for res in test_sort_1_results)
    assert all(res.alg_name == "TestSort2" for res in test_sort_2_results)
    assert all(res.alg_name == "TestSort3" for res in test_sort_3_results)

def test_get_results_by_n(populated_db):
    n_1_results = populated_db.get_result(n=1)
    n_5_results = populated_db.get_result(n=5)
    assert (len(n_1_results), len(n_5_results)) == (1, 4)
    assert all(res.n == 1 for res in n_1_results)
    assert all(res.n == 5 for res in n_5_results)

def test_get_results_by_array_id(populated_db):
    array_001_results = populated_db.get_result(array_id="array_001")
    array_002_results = populated_db.get_result(array_id="array_002")
    array_003_results = populated_db.get_result(array_id="array_003")
    assert (len(array_001_results), len(array_002_results), len(array_003_results)) == (1, 3, 1)
    assert all(res.array_id == "array_001" for res in array_001_results)
    assert all(res.array_id == "array_002" for res in array_002_results)
    assert all(res.array_id == "array_003" for res in array_003_results)

def test_get_results_in_asc_elapsed_time(populated_db):
    n_5_results = populated_db.get_result(n=5)
    last_time = 0.0
    for res in n_5_results:
        assert res.elapsed_time >= last_time
        last_time = res.elapsed_time

def test_clear_all_results(populated_db):
    populated_db.clear_all_results()
    all_results = populated_db.get_all_results()
    assert len(all_results) == 0

def test_get_all_results(populated_db, example_results):
    all_results = populated_db.get_all_results()
    assert len(all_results) == len(example_results)
    for res in example_results:
        assert res in all_results
