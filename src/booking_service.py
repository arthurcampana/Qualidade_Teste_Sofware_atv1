"""
booking_service.py
Classe principal que orquestra a chamada de validação e efetua o
registro definitivo do agendamento no banco de dados.
"""

import sqlite3

from database import inserir_agendamento, buscar_agendamento_por_id
from validation import FlightValidator


class FlightBookingService:
    """
    Serviço de agendamento de voos de helicóptero.

    Fluxo:
      1. Instancia FlightValidator com a conexão ativa.
      2. Chama validar() — lança exceção se alguma regra for violada.
      3. Se tudo passar, persiste o agendamento no banco com status AGENDADO.
      4. Retorna o dicionário com os dados do agendamento criado.
    """

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn
        self.validator = FlightValidator(conn)

    def agendar_voo(self,
                    aeronave_id: str,
                    destino: str,
                    horario_inicio: str,
                    horario_fim: str) -> dict:
        """
        Tenta agendar um voo.

        Parâmetros
        ----------
        aeronave_id    : identificador da aeronave (ex: 'PS-HLG').
        destino        : destino do voo (ex: 'Plataforma P-36').
        horario_inicio : início do voo no formato 'YYYY-MM-DD HH:MM'.
        horario_fim    : término do voo no formato 'YYYY-MM-DD HH:MM'.

        Retorno
        -------
        dict com id, aeronave_id, destino, horario_inicio, horario_fim e status.

        Exceções
        --------
        AeronaveNaoEncontradaError  – aeronave inexistente no banco.
        AeronaveEmManutencaoError   – aeronave indisponível para voo.
        ConflitoDeHorarioError      – conflito de horário detectado.
        """
        # Valida todas as regras antes de persistir
        self.validator.validar(aeronave_id, horario_inicio, horario_fim)

        # Persiste somente após aprovação nas regras
        agendamento_id = inserir_agendamento(
            self.conn, aeronave_id, destino, horario_inicio, horario_fim
        )

        row = buscar_agendamento_por_id(self.conn, agendamento_id)
        return dict(row)
