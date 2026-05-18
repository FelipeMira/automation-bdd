#!/usr/bin/env python3
"""
agent.py — Agente conversacional de gravação BDD.

Converse naturalmente para controlar a gravação de cenários .feature.
O agente traduz linguagem natural em steps Gherkin e gera arquivos .feature.

Uso:
    python agent.py
"""

import io
import os
import sys
from contextlib import redirect_stdout

import anthropic

sys.path.insert(0, os.path.dirname(__file__))
from utils.recorder import STATE_FILE, STEPS_FILE, cmd_start, cmd_status, cmd_step, cmd_stop

client = anthropic.Anthropic()

TOOLS = [
    {
        "name": "start_recording",
        "description": (
            "Inicia uma nova gravação BDD com o nome fornecido. "
            "Use quando o usuário quiser começar a gravar um novo cenário."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": (
                        "Nome da automação em snake_case, sem espaços "
                        "(ex: pesquisar_batata, login_usuario, abrir_safari)"
                    ),
                }
            },
            "required": ["name"],
        },
    },
    {
        "name": "add_step",
        "description": (
            "Adiciona um passo à gravação ativa. "
            "Converta a ação descrita pelo usuário em uma descrição clara de step Gherkin. "
            "Use o keyword mais adequado: "
            "Given para pré-condições/estado inicial, "
            "When para ações do usuário, "
            "Then para verificações/resultados esperados, "
            "And para continuar o passo anterior."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "keyword": {
                    "type": "string",
                    "enum": ["Given", "When", "Then", "And"],
                    "description": "Tipo do passo Gherkin",
                },
                "description": {
                    "type": "string",
                    "description": (
                        "Descrição do passo em linguagem natural clara, "
                        "como seria escrito em um arquivo .feature "
                        "(ex: 'o usuário abre o Safari', 'o campo de busca é exibido')"
                    ),
                },
            },
            "required": ["keyword", "description"],
        },
    },
    {
        "name": "stop_recording",
        "description": (
            "Finaliza a gravação ativa e salva o arquivo .feature em features/automation_scripts/. "
            "Use quando o usuário indicar que terminou de gravar."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_status",
        "description": (
            "Mostra o status da gravação atual: nome do cenário e passos gravados até agora. "
            "Use quando o usuário quiser saber o que foi gravado."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
]

SYSTEM_PROMPT = """Você é um assistente especializado em automação BDD (Behavior-Driven Development) com Behave e Gherkin.

Você ajuda a gravar cenários de teste convertendo descrições em linguagem natural para steps Gherkin.

## Ferramentas disponíveis
- start_recording: Inicia uma gravação com um nome
- add_step: Adiciona um passo (Given / When / Then / And)
- stop_recording: Finaliza e salva o arquivo .feature
- get_status: Mostra os passos gravados até agora

## Regras de uso das ferramentas

**start_recording:** Use sempre que o usuário quiser começar a gravar um novo cenário.
- Derive o nome a partir do que o usuário disser (ex: "gravar login" → "login")
- Se o usuário não der um nome claro, pergunte antes de chamar

**add_step:** Use para cada ação ou verificação que o usuário descrever.
- Mapeie o keyword assim:
  - Given → pré-condições, estado inicial do app/dispositivo
  - When → ações do usuário (tocar, digitar, navegar)
  - Then → verificações, resultados esperados
  - And → continuação do tipo de passo anterior
- Escreva a descrição como texto conciso de step Gherkin (sem verbosidade)
- Você pode adicionar vários passos em sequência se o usuário descrever várias ações de uma vez

**stop_recording:** Use quando o usuário disser que terminou, quer finalizar ou parar a gravação.

**get_status:** Use quando o usuário perguntar o que foi gravado ou quiser revisar.

## Comportamento geral
- Responda sempre em português
- Confirme cada ação realizada de forma breve
- Se o usuário descrever múltiplas ações de uma vez, adicione todos os passos antes de responder
- Sugira o passo seguinte quando fizer sentido
- Seja proativo: se perceber que o usuário está descrevendo passos mas a gravação não está ativa, pergunte se quer iniciar
"""


def execute_tool(name: str, tool_input: dict) -> str:
    """Executa a ferramenta do recorder e captura a saída."""
    captured = io.StringIO()
    try:
        with redirect_stdout(captured):
            if name == "start_recording":
                cmd_start(tool_input["name"])
            elif name == "add_step":
                cmd_step(tool_input["keyword"], tool_input["description"])
            elif name == "stop_recording":
                cmd_stop()
            elif name == "get_status":
                cmd_status()
        return captured.getvalue() or "Feito."
    except SystemExit as e:
        output = captured.getvalue()
        if e.code != 0:
            return output or f"Erro ao executar {name}."
        return output or "Feito."
    except Exception as e:
        return f"Erro inesperado em {name}: {e}"


def run_agent():
    """Loop principal do agente conversacional."""
    print("\n╔══════════════════════════════════════════╗")
    print("║   Agente de Gravação BDD — Automation    ║")
    print("╠══════════════════════════════════════════╣")
    print("║  Descreva o que quer automatizar e eu    ║")
    print("║  gravo os cenários .feature por você.    ║")
    print("║                                          ║")
    print("║  Digite 'sair' para encerrar.            ║")
    print("╚══════════════════════════════════════════╝\n")

    # Verifica se já existe gravação ativa e informa o usuário
    if STATE_FILE.exists():
        name = STATE_FILE.read_text().strip()
        steps = STEPS_FILE.read_text().strip().splitlines() if STEPS_FILE.exists() else []
        print(f"⚠️  Gravação ativa encontrada: \"{name}\" ({len(steps)} passo(s))\n")

    messages = []

    while True:
        try:
            user_input = input("Você: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nEncerrando agente. Até mais!")
            break

        if not user_input:
            continue

        if user_input.lower() in ("sair", "exit", "quit", "q"):
            print("\nAté mais!")
            break

        messages.append({"role": "user", "content": user_input})

        # Agentic loop: continua enquanto houver tool calls
        while True:
            response = client.messages.create(
                model="claude-opus-4-6",
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=messages,
            )

            # Separa text blocks de tool_use blocks
            text_parts = []
            tool_calls = []
            for block in response.content:
                if block.type == "text":
                    text_parts.append(block.text)
                elif block.type == "tool_use":
                    tool_calls.append(block)

            # Exibe resposta textual do agente
            if text_parts:
                print(f"\nAgente: {''.join(text_parts)}\n")

            # Adiciona resposta do assistente ao histórico
            messages.append({"role": "assistant", "content": response.content})

            # Se não há tool calls, encerra o loop interno
            if response.stop_reason == "end_turn" or not tool_calls:
                break

            # Executa as ferramentas e coleta resultados
            tool_results = []
            for tool in tool_calls:
                result = execute_tool(tool.name, tool.input)
                if result.strip():
                    print(result)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool.id,
                    "content": result,
                })

            # Devolve os resultados para o agente continuar
            messages.append({"role": "user", "content": tool_results})


if __name__ == "__main__":
    run_agent()
