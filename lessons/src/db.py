import sqlite3
import struct
from typing import List, Optional
from pydantic import BaseModel


class DatabaseResult(BaseModel):
    n: int
    alg_name: str
    elapsed_time: float
    array: List[int]
    sorted_array: List[int]
    array_id: str


class DatabaseManager:

    def __init__(self, db_path: str = 'data.db'):
        self.db_path = db_path

    def __enter__(self):
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None:
            self.conn.commit()
        else:
            self.conn.rollback()

        self.cursor.close()

    def _serialize_array(self, array: List[int]) -> bytes:
        """
        Convert integer array to binary BLOB using struct.

        Format: [count][int1][int2][int3]...
        - First 4 bytes: unsigned int for array length
        - Remaining bytes: signed integers (4 bytes each)

        Args:
            array: List of integers to serialize

        Returns:
            Binary data (bytes)
        """
        count = len(array)
        format_str = f'I{count}i'
        return struct.pack(format_str, count, *array)

    def _deserialize_array(self, blob: bytes) -> List[int]:
        """
        Convert binary BLOB back to integer array.

        Args:
            blob: Binary data from database

        Returns:
            List of integers
        """
        count = struct.unpack('I', blob[:4])[0]
        format_str = f'{count}i'
        integers = struct.unpack(format_str, blob[4:])
        return list(integers)

    def init_db(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS sort_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                n DEC NOT NULL,
                alg_name TEXT NOT NULL,
                elapsed_time FLOAT NOT NULL,
                array_id string NOT NULL,
                input_array BLOB NOT NULL,
                sorted_array BLOB NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

    def add_result(self, db_result: DatabaseResult) -> Optional[int]:
        serialized_array = self._serialize_array(db_result.array)
        sorted_serialized_array = self._serialize_array(db_result.sorted_array)
        self.cursor.execute('''
            INSERT INTO sort_results (n ,alg_name, elapsed_time, array_id, input_array, sorted_array)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (db_result.n, db_result.alg_name, db_result.elapsed_time, db_result.array_id,
              serialized_array, sorted_serialized_array))
        return self.cursor.lastrowid

    def get_result(self, array_id: Optional[str] = None, alg_name: Optional[str] = None, n: Optional[int] = None) -> List[DatabaseResult]:
        self.cursor.execute('''
            SELECT n, alg_name, elapsed_time, array_id, input_array, sorted_array
            FROM sort_results
            WHERE n = ? OR array_id = ? OR alg_name = ?
            ORDER BY elapsed_time ASC
        ''', (n, array_id, alg_name))
        rows = self.cursor.fetchall()
        results = []
        for row in rows:
            deserialized_array = self._deserialize_array(row["input_array"])
            deserialized_sorted_array = self._deserialize_array(row["sorted_array"])
            result = DatabaseResult(
                n=row["n"],
                alg_name=row["alg_name"],
                elapsed_time=row["elapsed_time"],
                array_id=row["array_id"],
                array=deserialized_array,
                sorted_array=deserialized_sorted_array
            )
            results.append(result)
        return results

    def clear_all_results(self):
        self.cursor.execute('DELETE FROM sort_results')

    def get_all_results(self) -> List[DatabaseResult]:
        self.cursor.execute('SELECT * FROM sort_results')
        rows = self.cursor.fetchall()
        results = []
        for row in rows:
            deserialized_array = self._deserialize_array(row["input_array"])
            deserialized_sorted_array = self._deserialize_array(row["sorted_array"])
            result = DatabaseResult(
                n=row["n"],
                alg_name=row["alg_name"],
                elapsed_time=row["elapsed_time"],
                array_id=row["array_id"],
                array=deserialized_array,
                sorted_array=deserialized_sorted_array
            )
            results.append(result)
        return results




