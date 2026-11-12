
import gzip
import socket
import struct
import csv
import json

from bson import BSON

MONGO_HOST = "jira-mongodb"
MONGO_PORT = 27017

DATABASE = "JiraReposAnon"
COLLECTION = "Apache"

OUTPUT_FILE = "/opt/airflow/data/jira/extracted/apache_issues_10000.csv"
MAX_RECORDS = 10000

FIELDS = [
    "key",
    "id",
    "project",
    "issuetype",
    "status",
    "created",
    "updated",
    "summary"
]


def main():
    raise NotImplementedError(
        "We will implement archive streaming after inspecting BSON framing."
    )


if __name__ == "__main__":
    main()
