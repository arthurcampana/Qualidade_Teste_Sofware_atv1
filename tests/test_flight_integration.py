"""
test_flight_integration.py
Suíte de Testes de Integração — Sistema de Agendamento de Voos AeroLog.

Cenários cobertos:
  1. Caminho Feliz - Agendamento Válido
  2. Conflito de Horário da Aeronave
  3. Aeronave em Manutenção Preventiva/Corretiva
  4. Consistência do Banco com Fixtures/Rollback
"""

import pytest

from booking_service import FlightBookingService
from database import (
    inserir_aeronave,
    contar_agendamentos,
    get_connection,
    create_tables,
)
from validation import (
    AeronaveEmManutencaoError,
    ConflitoDeHorarioError,
    AeronaveNaoEncontradaError,
)


# ---------------------------------------------------------------------------
# Cenário 1 — Caminho Feliz: Agendamento Válido
# ---------------------------------------------------------------------------

class TestCenario1AgendamentoValido:
    """
    Ação:    Solicitar agendamento com helicóptero LIBERADO e horário livre.
    Validação: Confirmação retornada e registro persistido com status AGENDADO.
    """

    def test_agendamento_retorna_dados_corretos(self, service):
        resultado = service.agendar_voo(
            aeronave_id="PS-HLG",
            destino="Plataforma P-36",
            horario_inicio="2026-09-29 08:00",
            horario_fim="2026-09-29 10:00",
        )

        assert resultado["aeronave_id"] == "PS-HLG"
        assert resultado["destino"] == "Plataforma P-36"
        assert resultado["horario_inicio"] == "2026-09-29 08:00"
        assert resultado["horario_fim"] == "2026-09-29 10:00"

    def test_agendamento_persiste_com_status_agendado(self, service, conn):
        service.agendar_voo(
            aeronave_id="PS-HLG",
            destino="Plataforma P-36",
            horario_inicio="2026-09-29 08:00",
            horario_fim="2026-09-29 10:00",
        )

        total = contar_agendamentos(conn)
        assert total == 1

    def test_status_do_registro_e_agendado(self, service):
        resultado = service.agendar_voo(
            aeronave_id="PS-HLG",
            destino="Base Macaé",
            horario_inicio="2026-09-29 14:00",
            horario_fim="2026-09-29 16:00",
        )

        assert resultado["status"] == "AGENDADO"


# ---------------------------------------------------------------------------
# Cenário 2 — Conflito de Horário da Aeronave
# ---------------------------------------------------------------------------

class TestCenario2ConflitoDeHorario:
    """
    Ação:    Tentar agendar a mesma aeronave em horário já ocupado.
    Validação: ConflitoDeHorarioError levantada; segundo registro não inserido.
    """

    def test_levanta_excecao_de_conflito(self, service):
        service.agendar_voo(
            aeronave_id="PS-HLG",
            destino="Plataforma P-36",
            horario_inicio="2026-09-29 08:00",
            horario_fim="2026-09-29 10:00",
        )

        with pytest.raises(ConflitoDeHorarioError):
            service.agendar_voo(
                aeronave_id="PS-HLG",
                destino="Base Campos",
                horario_inicio="2026-09-29 09:00",  # sobreposição
                horario_fim="2026-09-29 11:00",
            )

    def test_segundo_agendamento_nao_inserido_no_banco(self, service, conn):
        service.agendar_voo(
            aeronave_id="PS-HLG",
            destino="Plataforma P-36",
            horario_inicio="2026-09-29 08:00",
            horario_fim="2026-09-29 10:00",
        )

        with pytest.raises(ConflitoDeHorarioError):
            service.agendar_voo(
                aeronave_id="PS-HLG",
                destino="Base Campos",
                horario_inicio="2026-09-29 08:30",
                horario_fim="2026-09-29 09:30",
            )

        # Apenas 1 registro deve existir — o segundo foi recusado
        assert contar_agendamentos(conn) == 1

    def test_conflito_exato_de_horario(self, service):
        """Horários idênticos também devem gerar conflito."""
        service.agendar_voo(
            aeronave_id="PS-HLG",
            destino="Plataforma P-36",
            horario_inicio="2026-09-29 08:00",
            horario_fim="2026-09-29 10:00",
        )

        with pytest.raises(ConflitoDeHorarioError):
            service.agendar_voo(
                aeronave_id="PS-HLG",
                destino="Duplicata",
                horario_inicio="2026-09-29 08:00",
                horario_fim="2026-09-29 10:00",
            )

    def test_horario_adjacente_nao_gera_conflito(self, service, conn):
        """Voo que começa exatamente quando o anterior termina não é conflito."""
        service.agendar_voo(
            aeronave_id="PS-HLG",
            destino="Plataforma P-36",
            horario_inicio="2026-09-29 08:00",
            horario_fim="2026-09-29 10:00",
        )

        # Este deve ser aceito — inicia quando o anterior termina
        resultado = service.agendar_voo(
            aeronave_id="PS-HLG",
            destino="Base Macaé",
            horario_inicio="2026-09-29 10:00",
            horario_fim="2026-09-29 12:00",
        )

        assert resultado["status"] == "AGENDADO"
        assert contar_agendamentos(conn) == 2


# ---------------------------------------------------------------------------
# Cenário 3 — Aeronave em Manutenção Preventiva/Corretiva
# ---------------------------------------------------------------------------

class TestCenario3AeronaveEmManutencao:
    """
    Ação:    Tentar agendar aeronave com status EM_INSPECAO.
    Validação: AeronaveEmManutencaoError levantada; banco sem alterações.
    """

    def test_levanta_excecao_de_manutencao(self, service):
        with pytest.raises(AeronaveEmManutencaoError):
            service.agendar_voo(
                aeronave_id="PS-OFB",
                destino="Plataforma P-19",
                horario_inicio="2026-09-29 08:00",
                horario_fim="2026-09-29 10:00",
            )

    def test_nenhum_registro_inserido_no_banco(self, service, conn):
        with pytest.raises(AeronaveEmManutencaoError):
            service.agendar_voo(
                aeronave_id="PS-OFB",
                destino="Plataforma P-19",
                horario_inicio="2026-09-29 08:00",
                horario_fim="2026-09-29 10:00",
            )

        assert contar_agendamentos(conn) == 0

    def test_mensagem_de_erro_menciona_aeronave(self, service):
        with pytest.raises(AeronaveEmManutencaoError, match="PS-OFB"):
            service.agendar_voo(
                aeronave_id="PS-OFB",
                destino="Plataforma P-19",
                horario_inicio="2026-09-29 08:00",
                horario_fim="2026-09-29 10:00",
            )


# ---------------------------------------------------------------------------
# Cenário 4 — Consistência do Banco com Fixtures / Rollback
# ---------------------------------------------------------------------------

class TestCenario4IsolamentoDoBanco:
    """
    Ação:    Executar múltiplos testes em sequência com banco temporário.
    Validação: Cada teste começa com banco limpo — isolamento total garantido.
    """

    def test_banco_inicia_sem_agendamentos(self, conn):
        """O banco de cada teste deve começar zerado."""
        assert contar_agendamentos(conn) == 0

    def test_agendamento_do_teste_anterior_nao_persiste(self, service, conn):
        """
        Simula o que seria o 'teste seguinte': mesmo após outro teste
        criar agendamentos, este inicia com banco limpo.
        """
        # Cria agendamento neste teste
        service.agendar_voo(
            aeronave_id="PS-HLG",
            destino="Plataforma P-36",
            horario_inicio="2026-09-30 06:00",
            horario_fim="2026-09-30 08:00",
        )
        assert contar_agendamentos(conn) == 1

        # Outro fixture conn geraria banco zerado — aqui verificamos
        # que o dado existe apenas neste escopo
        assert contar_agendamentos(conn) == 1  # ainda no mesmo escopo

    def test_bancos_de_fixtures_distintas_sao_independentes(self):
        """
        Cria duas conexões em memória independentes e verifica que
        operações em uma não afetam a outra.
        """
        conn_a = get_connection(":memory:")
        create_tables(conn_a)
        inserir_aeronave(conn_a, "PS-A01", "Bell 412", 13, "LIBERADO")

        conn_b = get_connection(":memory:")
        create_tables(conn_b)
        inserir_aeronave(conn_b, "PS-B01", "Bell 412", 13, "LIBERADO")

        svc_a = FlightBookingService(conn_a)
        svc_b = FlightBookingService(conn_b)

        svc_a.agendar_voo("PS-A01", "Destino A", "2026-09-29 08:00", "2026-09-29 10:00")

        # conn_b não deve enxergar o agendamento de conn_a
        assert contar_agendamentos(conn_a) == 1
        assert contar_agendamentos(conn_b) == 0

        conn_a.close()
        conn_b.close()

    def test_aeronave_inexistente_levanta_excecao(self, service, conn):
        """Tentativa com aeronave não cadastrada não deve poluir o banco."""
        with pytest.raises(AeronaveNaoEncontradaError):
            service.agendar_voo(
                aeronave_id="PS-FANTASMA",
                destino="Lugar Nenhum",
                horario_inicio="2026-09-29 08:00",
                horario_fim="2026-09-29 10:00",
            )

        assert contar_agendamentos(conn) == 0
