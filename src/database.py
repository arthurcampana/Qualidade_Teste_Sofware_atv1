"""
database.py
Módulo responsável por gerenciar a conexão e as operações no banco
de dados SQLite local (tabelas de aeronaves e agendamentos).
"""

import sqlite3
from typing import Optional


def get_connection(db_path: str = ":memory:") -> sqlite3.Connection:
    """Retorna uma conexão com o banco de dados SQLite."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables(conn: sqlite3.Connection) -> None:
    """Cria as tabelas necessárias para o sistema de agendamento."""
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS aeronaves (
            id          TEXT PRIMARY KEY,
            modelo      TEXT NOT NULL,
            capacidade  INTEGER NOT NULL,
            status_manutencao TEXT NOT NULL DEFAULT 'LIBERADO'
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agendamentos (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            aeronave_id     TEXT NOT NULL,
            destino         TEXT NOT NULL,
            horario_inicio  TEXT NOT NULL,
            horario_fim     TEXT NOT NULL,
            status          TEXT NOT NULL DEFAULT 'AGENDADO',
            FOREIGN KEY (aeronave_id) REFERENCES aeronaves(id)
        )
    """)

    conn.commit()


def inserir_aeronave(conn: sqlite3.Connection,
                     aeronave_id: str,
                     modelo: str,
                     capacidade: int,
                     status_manutencao: str = "LIBERADO") -> None:
    """Insere uma aeronave no banco de dados."""
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO aeronaves (id, modelo, capacidade, status_manutencao) "
        "VALUES (?, ?, ?, ?)",
        (aeronave_id, modelo, capacidade, status_manutencao),
    )
    conn.commit()


def buscar_aeronave(conn: sqlite3.Connection, aeronave_id: str) -> Optional[sqlite3.Row]:
    """Retorna os dados de uma aeronave pelo ID, ou None se não encontrada."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM aeronaves WHERE id = ?", (aeronave_id,))
    return cursor.fetchone()


def inserir_agendamento(conn: sqlite3.Connection,
                        aeronave_id: str,
                        destino: str,
                        horario_inicio: str,
                        horario_fim: str) -> int:
    """
    Insere um agendamento no banco de dados com status AGENDADO.
    Retorna o ID gerado.
    """
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO agendamentos "
        "(aeronave_id, destino, horario_inicio, horario_fim, status) "
        "VALUES (?, ?, ?, ?, 'AGENDADO')",
        (aeronave_id, destino, horario_inicio, horario_fim),
    )
    conn.commit()
    return cursor.lastrowid


def buscar_agendamento_por_id(conn: sqlite3.Connection, agendamento_id: int) -> Optional[sqlite3.Row]:
    """Retorna um agendamento pelo ID."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM agendamentos WHERE id = ?", (agendamento_id,))
    return cursor.fetchone()


def verificar_conflito_horario(conn: sqlite3.Connection,
                                aeronave_id: str,
                                horario_inicio: str,
                                horario_fim: str) -> bool:
    """
    Verifica se existe conflito de horário para a aeronave informada.
    Retorna True se houver conflito, False caso contrário.
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT COUNT(*) FROM agendamentos
        WHERE aeronave_id = ?
          AND status = 'AGENDADO'
          AND horario_inicio < ?
          AND horario_fim   > ?
        """,
        (aeronave_id, horario_fim, horario_inicio),
    )
    count = cursor.fetchone()[0]
    return count > 0


def contar_agendamentos(conn: sqlite3.Connection) -> int:
    """Retorna o total de agendamentos na base."""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM agendamentos")
    return cursor.fetchone()[0]
