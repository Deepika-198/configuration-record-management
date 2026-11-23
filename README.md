# Configuration Record Management Application

A Python command-line application for managing fictional configuration records in MySQL. It validates JSON before writing data and uses parameterized SQL for create, retrieve, update, delete, and search operations.

## Run the demo

Requires Python 3.12+ and Docker Compose. The commands below use PowerShell and a fresh demo database.

    python -m pip install -r requirements.txt
    $env:DB_PASSWORD = 'local-demo-password'
    docker compose up -d --wait

Run the following commands in sequence. Use the ID returned by search in place of 1 if the demo database already contains records.

    python records.py add examples/record.json
    python records.py search Demo
    python records.py get 1
    python records.py update 1 examples/archived.json
    python records.py get 1
    python records.py delete 1
    python records.py get 1

Expected result: the record appears as active, becomes archived after the update, and the final command reports that the record was not found. To try validation, change the example status to a value other than draft, active, or archived.

## Run the tests

    python -m pytest -v

The default suite exercises validation and CRUD using an in-memory SQLite database. To include MySQL, start the demo database and run:

    $env:TEST_MYSQL = '1'
    python -m pytest -v

GitHub Actions runs both database paths. The MySQL container is bound to localhost. Stop it with `docker compose down`. The named volume retains records between runs.
