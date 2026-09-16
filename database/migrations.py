from database.database import initialize_database


def run_migrations() -> None:
    initialize_database()
