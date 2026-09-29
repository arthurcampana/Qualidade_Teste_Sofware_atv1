"""
conftest.py
Fixtures do pytest para criação e limpeza do banco de dados temporário.
Garante isolamento completo entre os testes — cada teste recebe um banco
SQLite em memória limpo, populado com dados iniciais controlados.
"""

import sys
import os
import pytest

# Adiciona src/ ao path para que os módulos sejam encontrados
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from database import get_connection, create_tables, inserir_aeronave
from booking_service import FlightBookingService


@pytest.fixture
def conn():
    """
    Fixture de conexão isolada.
    Cria um banco SQLite em memória, cria as tabelas e insere aeronaves
    padrão para os testes. A conexão é fechada automaticamente ao fim
    de cada teste — nenhum dado persiste entre execuções.
    """
    connection = get_connection(":memory:")
    create_tables(connection)

    # Aeronave liberada para voo
    inserir_aeronave(
        connection,
        aeronave_id="PS-HLG",
        modelo="Sikorsky S-76",
        capacidade=12,
        status_manutencao="LIBERADO",
    )

    # Aeronave em inspeção (indisponível para voo)
    inserir_aeronave(
        connection,
        aeronave_id="PS-OFB",
        modelo="Airbus H175",
        capacidade=16,
        status_manutencao="EM_INSPECAO",
    )

    yield connection

    connection.close()


@pytest.fixture
def service(conn):
    """
    Fixture do FlightBookingService já conectado ao banco isolado.
    Depende da fixture 'conn', herdando o mesmo isolamento por teste.
    """
    return FlightBookingService(conn)
