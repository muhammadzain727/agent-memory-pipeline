
import os
import psycopg2
from psycopg2.extras import RealDictCursor


def get_connection():
    """
    Create and return a PostgreSQL database connection.
    """

    connection = psycopg2.connect(
        host=os.getenv("DB_HOST", "postgres"),
        port=os.getenv("DB_PORT", "5432"),
        database=os.getenv("POSTGRES_DB", "agent_memory"),
        user=os.getenv("POSTGRES_USER", "admin"),
        password=os.getenv("POSTGRES_PASSWORD")
    )

    return connection


def test_connection():
    """
    Test PostgreSQL connectivity and inspect project schemas.
    """

    connection = None

    try:
        connection = get_connection()

        with connection.cursor(cursor_factory=RealDictCursor) as cursor:

            cursor.execute("""
                SELECT
                    current_database() AS database_name,
                    current_user AS username,
                    version() AS database_version;
            """)

            database_info = cursor.fetchone()

            print("\nDATABASE CONNECTION SUCCESSFUL")
            print("--------------------------------")
            print(f"Database: {database_info['database_name']}")
            print(f"User: {database_info['username']}")

            cursor.execute("""
                SELECT schema_name
                FROM information_schema.schemata
                WHERE schema_name IN (
                    'bronze',
                    'silver',
                    'gold',
                    'audit'
                )
                ORDER BY schema_name;
            """)

            schemas = cursor.fetchall()

            print("\nPROJECT SCHEMAS")
            print("---------------")

            for schema in schemas:
                print(f"Found: {schema['schema_name']}")

            cursor.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'audit'
                ORDER BY table_name;
            """)

            tables = cursor.fetchall()

            print("\nAUDIT TABLES")
            print("------------")

            for table in tables:
                print(f"Found: {table['table_name']}")

        print("\nPython and PostgreSQL integration verified.")

    except Exception as error:
        print(f"\nDATABASE CONNECTION FAILED: {error}")
        raise

    finally:
        if connection:
            connection.close()


if __name__ == "__main__":
    test_connection()
