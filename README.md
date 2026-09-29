# AeroLog Helicópteros — Testes de Integração

Projeto de **Testes de Integração** desenvolvido para a disciplina de Qualidade e Teste de Software (UniSENAI).

O sistema simula o módulo de agendamento de voos de helicóptero da empresa **AeroLog Helicópteros**, testando a integração real entre:

- `database.py` — gerenciamento do banco SQLite
- `validation.py` — regras de elegibilidade da aeronave
- `booking_service.py` — orquestração do agendamento

---

## Estrutura do Projeto

```
projeto-teste-integracao-helicoptero/
├── src/
│   ├── database.py          # Módulo de banco de dados (SQLite)
│   ├── validation.py        # Regras de elegibilidade da aeronave
│   └── booking_service.py   # Serviço de agendamento de voos
├── tests/
│   ├── conftest.py          # Fixtures do pytest (banco isolado por teste)
│   └── test_flight_integration.py  # Suíte com 4 cenários de integração
├── .gitignore
├── README.md
└── requirements.txt
```

---

## Pré-requisitos

- Python 3.8+
- pip

---

## Instalação

```bash
# Clone o repositório
git clone <url-do-repositorio>
cd Qualidade_Teste_Sofware_atv1

# (Opcional) Crie e ative um ambiente virtual
python -m venv .venv
.venv\Scripts\activate   # Windows
source .venv/bin/activate # Linux/macOS

# Instale as dependências
pip install -r requirements.txt
```

---

## Execução dos Testes

### Rodar todos os testes com saída detalhada

```bash
pytest tests/ -v
```

### Rodar com relatório de cobertura

```bash
pytest tests/ -v --cov=src --cov-report=term-missing
```

### Gerar relatório HTML de cobertura

```bash
pytest tests/ -v --cov=src --cov-report=html
# Abre htmlcov/index.html no navegador
```

---

## Cenários de Teste

| # | Cenário | Resultado Esperado |
|---|---------|-------------------|
| 1 | **Caminho Feliz — Agendamento Válido** | Agendamento confirmado, status `AGENDADO` no banco |
| 2 | **Conflito de Horário da Aeronave** | `ConflitoDeHorarioError` levantada; banco inalterado |
| 3 | **Aeronave em Manutenção (EM_INSPECAO)** | `AeronaveEmManutencaoError` levantada; banco inalterado |
| 4 | **Consistência / Isolamento com Fixtures** | Cada teste inicia com banco limpo; sem interferência |

---

## Regras de Negócio Implementadas

1. **Disponibilidade**: Um helicóptero não pode ter dois voos no mesmo intervalo de horário.
2. **Status de Manutenção**: Apenas aeronaves com status `LIBERADO` podem ser agendadas.
3. **Confirmação**: Após aprovação, o agendamento é salvo com status `AGENDADO`. Falhas não persistem no banco.
