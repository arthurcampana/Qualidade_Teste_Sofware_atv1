"""
validation.py
Módulo responsável por aplicar as regras de elegibilidade da operação:
  - Status de manutenção da aeronave deve ser LIBERADO.
  - Não pode existir conflito de horário para a aeronave solicitada.
"""

import sqlite3

from database import buscar_aeronave, verificar_conflito_horario


class AeronaveEmManutencaoError(Exception):
    """Levantada quando a aeronave não está liberada para voo."""


class ConflitoDeHorarioError(Exception):
    """Levantada quando já existe um voo agendado no mesmo horário."""


class AeronaveNaoEncontradaError(Exception):
    """Levantada quando a aeronave não existe no banco de dados."""


class FlightValidator:
    """Aplica as regras de elegibilidade antes de confirmar um agendamento."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def validar(self,
                aeronave_id: str,
                horario_inicio: str,
                horario_fim: str) -> None:
        """
        Executa todas as validações necessárias.
        Lança exceção específica se alguma regra for violada.
        """
        # Regra 1 – aeronave deve existir
        aeronave = buscar_aeronave(self.conn, aeronave_id)
        if aeronave is None:
            raise AeronaveNaoEncontradaError(
                f"Aeronave '{aeronave_id}' não encontrada no banco de dados."
            )

        # Regra 2 – status de manutenção deve ser LIBERADO
        if aeronave["status_manutencao"] != "LIBERADO":
            raise AeronaveEmManutencaoError(
                f"Aeronave '{aeronave_id}' está com status "
                f"'{aeronave['status_manutencao']}' e não pode ser agendada."
            )

        # Regra 3 – não pode haver conflito de horário
        if verificar_conflito_horario(self.conn, aeronave_id, horario_inicio, horario_fim):
            raise ConflitoDeHorarioError(
                f"Aeronave '{aeronave_id}' já possui voo agendado neste intervalo "
                f"({horario_inicio} – {horario_fim})."
            )
