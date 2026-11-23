import argparse
import json
import os
from contextlib import closing
from pathlib import Path

FIELDS = {"name", "category", "status"}
STATUSES = {"draft", "active", "archived"}


def validate(payload):
    if not isinstance(payload, dict) or payload.keys() != FIELDS:
        raise ValueError("Expected exactly name, category and status")
    if any(not isinstance(payload[key], str) or not 1 <= len(payload[key].strip()) <= 80
           for key in FIELDS):
        raise ValueError("All fields must be strings of 1 to 80 characters")
    name, category, status = (payload[key].strip() for key in ("name", "category", "status"))
    if status not in STATUSES:
        raise ValueError("Status must be draft, active or archived")
    return name, category, status


class RecordStore:
    def __init__(self, connection, parameter):
        self.connection = connection
        self.parameter = parameter

    def execute(self, sql, values=(), read=False):
        with closing(self.connection.cursor()) as cursor:
            try:
                cursor.execute(sql.replace("?", self.parameter), values)
                if read:
                    fields = [column[0] for column in cursor.description]
                    result = [dict(zip(fields, row)) for row in cursor.fetchall()]
                else:
                    result = cursor.rowcount
                self.connection.commit()
                return result
            except Exception:
                self.connection.rollback()
                raise

    def add(self, payload):
        return self.execute("INSERT INTO records (name, category, status) VALUES (?, ?, ?)",
                            validate(payload))

    def update(self, record_id, payload):
        return self.execute("UPDATE records SET name=?, category=?, status=? WHERE id=?",
                            (*validate(payload), record_id))

    def delete(self, record_id):
        return self.execute("DELETE FROM records WHERE id=?", (record_id,))

    def get(self, record_id):
        rows = self.execute("SELECT id, name, category, status FROM records WHERE id=?",
                            (record_id,), read=True)
        return rows[0] if rows else None

    def search(self, term):
        return self.execute(
            "SELECT id, name, category, status FROM records WHERE LOWER(name) LIKE LOWER(?) ORDER BY id",
            (f"%{term}%",), read=True
        )


def main():
    import mysql.connector

    parser = argparse.ArgumentParser(description="Manage configuration records in MySQL")
    sub = parser.add_subparsers(dest="command", required=True)
    for action in ("add", "update", "delete", "get", "search"):
        command = sub.add_parser(action)
        if action in {"update", "delete", "get"}:
            command.add_argument("id", type=int)
        if action in {"add", "update"}:
            command.add_argument("file", type=Path)
        if action == "search":
            command.add_argument("term", nargs="?", default="")
    args = parser.parse_args()
    try:
        with closing(mysql.connector.connect(
            host=os.getenv("DB_HOST", "127.0.0.1"),
            port=int(os.getenv("DB_PORT", "3307")),
            user=os.getenv("DB_USER", "portfolio"),
            password=os.environ["DB_PASSWORD"],
            database=os.getenv("DB_NAME", "portfolio"),
        )) as connection:
            store = RecordStore(connection, "%s")
            arguments = []
            if hasattr(args, "id"):
                arguments.append(args.id)
            if hasattr(args, "file"):
                arguments.append(json.loads(args.file.read_text(encoding="utf-8")))
            if hasattr(args, "term"):
                arguments.append(args.term)
            result = getattr(store, args.command)(*arguments)
            if args.command == "get" and result is None:
                parser.exit(1, "Record not found\n")
            print(json.dumps(result, indent=2))
    except (ValueError, KeyError, OSError, mysql.connector.Error) as error:
        parser.exit(1, f"Operation failed: {error}\n")


if __name__ == "__main__":
    main()
