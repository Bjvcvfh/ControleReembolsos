import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from utils.paths import database_path


DEFAULT_SERVICE_TYPES = [
    "PEDAGIO",
    "LAVAGEM",
    "TROCA DE PNEU",
    "MANUTENCAO",
    "COMBUSTIVEL",
    "ESTACIONAMENTO",
]


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(database_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def transaction() -> Iterator[sqlite3.Connection]:
    conn = get_connection()
    try:
        conn.execute("BEGIN")
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def initialize_database(db_path: Path | None = None) -> None:
    path = db_path or database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS app_sequence (
                name TEXT PRIMARY KEY,
                value INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS motoristas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL UNIQUE COLLATE NOCASE,
                ativo INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS tipos_servico (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descricao TEXT NOT NULL UNIQUE COLLATE NOCASE,
                ativo INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS reembolsos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero TEXT NOT NULL UNIQUE,
                motorista_id INTEGER,
                motorista_nome TEXT NOT NULL,
                placa TEXT NOT NULL DEFAULT '',
                data_hora TEXT NOT NULL,
                valor_total_centavos INTEGER NOT NULL,
                pdf_path TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (motorista_id) REFERENCES motoristas(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS reembolso_itens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reembolso_id INTEGER NOT NULL,
                tipo_servico_id INTEGER,
                tipo_servico_descricao TEXT NOT NULL,
                data_servico TEXT NOT NULL,
                os TEXT,
                valor_centavos INTEGER NOT NULL,
                FOREIGN KEY (reembolso_id) REFERENCES reembolsos(id) ON DELETE CASCADE,
                FOREIGN KEY (tipo_servico_id) REFERENCES tipos_servico(id) ON DELETE SET NULL
            );

            CREATE INDEX IF NOT EXISTS idx_reembolsos_numero ON reembolsos(numero);
            CREATE INDEX IF NOT EXISTS idx_reembolsos_data_hora ON reembolsos(data_hora);
            CREATE INDEX IF NOT EXISTS idx_reembolsos_motorista ON reembolsos(motorista_nome);
            CREATE INDEX IF NOT EXISTS idx_itens_servico ON reembolso_itens(tipo_servico_descricao);
            """
        )
        conn.execute(
            "INSERT OR IGNORE INTO app_sequence (name, value) VALUES ('reembolso', 0)"
        )
        for description in DEFAULT_SERVICE_TYPES:
            conn.execute(
                "INSERT OR IGNORE INTO tipos_servico (descricao, ativo) VALUES (?, 1)",
                (description,),
            )
        columns = [
            row[1]
            for row in conn.execute("PRAGMA table_info(reembolso_itens)").fetchall()
        ]
        if "data_servico" not in columns:
            conn.execute(
                "ALTER TABLE reembolso_itens ADD COLUMN data_servico TEXT NOT NULL DEFAULT ''"
            )
        reimbursement_columns = [
            row[1]
            for row in conn.execute("PRAGMA table_info(reembolsos)").fetchall()
        ]
        if "placa" not in reimbursement_columns:
            conn.execute(
                "ALTER TABLE reembolsos ADD COLUMN placa TEXT NOT NULL DEFAULT ''"
            )
        conn.commit()
    finally:
        conn.close()
