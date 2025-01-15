import datetime
import pytest
import psycopg2

# This needs to be productionified at some point.
# but right now its really useful for making sure logic changes
# don't break things.
#
# Run this after running load/load_csvs.sh

@pytest.fixture(scope="module")
def db_connection():
    conn = psycopg2.connect(
        dbname="dbt",
        user="user",
        password="user",
        host="localhost",
        port="5432"
    )
    yield conn
    conn.close()

def test_freeze_fridge_alarms(db_connection):

    expected_results = [
        (
            datetime.datetime(2023, 11, 22, 3, 0),
            datetime.datetime(2023, 11, 22, 4, 0),
            "a"
        ),
        (
            datetime.datetime(2023, 11, 22, 5, 30),
            None,
            "a"
        ),
        (
            datetime.datetime(2023, 11, 22, 3, 0),
            datetime.datetime(2023, 11, 22, 4, 0),
            "b"
        )
    ]
    cursor = db_connection.cursor()
    cursor.execute("SELECT begin, stop, cce_id FROM temperature_alarms WHERE alarm_cce_type = 'fridge' AND alarm_temperature_type = 'freeze' ORDER BY cce_id, begin")
    results = cursor.fetchall()

    print(results)
    for result, expected_result in zip(results, expected_results):
        assert result == expected_result, f"{result}, {expected_result}"

def test_heat_freezer_alarms(db_connection):

    expected_results = [
        (
            datetime.datetime(2023, 11, 22, 1, 30),
            None,
            "a"
        ),
        (
            datetime.datetime(2023, 11, 22, 1, 30),
            None,
            "b"
        ),
    ]
    cursor = db_connection.cursor()
    cursor.execute("SELECT begin, stop, cce_id FROM temperature_alarms WHERE alarm_cce_type = 'freezer' AND alarm_temperature_type = 'fridge' ORDER BY cce_id, begin")
    results = cursor.fetchall()

    print(results)
    for result, expected_result in zip(results, expected_results):
        assert result == expected_result, f"{result}, {expected_result}"

def test_heat_fridge_alarms(db_connection):

    expected_results = []
    cursor = db_connection.cursor()
    cursor.execute("SELECT begin, stop, cce_id FROM temperature_alarms WHERE alarm_cce_type = 'fridge' AND alarm_temperature_type = 'heat' ORDER BY cce_id, begin")
    results = cursor.fetchall()

    print(results)
    for result, expected_result in zip(results, expected_results):
        assert result == expected_result, f"{result}, {expected_result}"

def test_non_temperature_alarms(db_connection):
    for expected_results, table_name in (
    ([
        (
            datetime.datetime(2023, 11, 23, 0, 0),
            None,
            "a"
        )
    ], "power_alarms"),
    ([
        (
            datetime.datetime(2023, 11, 21, 1, 30),
            None,
            "a"
        )
    ], "emd_connection_alarms"),
    ([
        (
            datetime.datetime(2023, 11, 21, 0, 15),
            datetime.datetime(2023, 11, 21, 0, 16),
            "a"
        ),
        # Verify time series data that isn't even in spacing still results
        # in alarms.
        (
            datetime.datetime(2023, 11, 21, 0, 7),
            None,
            "b"
        ),
        # Alarm should start between time series points if that's where the
        # threshold duration would end.
        # TODO: do this later.
        (
            # datetime.datetime(2023, 11, 21, 0, 7),
            datetime.datetime(2023, 11, 21, 0, 9),
            None,
            "c"
        ),

        # Just a single door open tsf should result in an alarm.
        # (
        #     datetime.datetime(2023, 11, 21, 0, 7),
        #     None,
        #     "d"
        # )
        # There is no alarm here, but CCE 'e' should have 0 alarms since
        # changing monitors shouldn't affect alarm computation.
    ], "door_alarms")
    ):
        cursor = db_connection.cursor()
        cursor.execute(f"SELECT begin, stop, cce_id FROM {table_name} ORDER BY cce_id, begin")
        results = cursor.fetchall()

        for result, expected_result in zip(results, expected_results):
            assert result == expected_result, f"{table_name}, {result}, {expected_result}"

        # strict=True does the len check, but it makes it more difficult to show
        # debugging info
        assert len(results) == len(expected_results), f"{table_name}, {results}, {expected_results}"