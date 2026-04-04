"""
setup_telegram.py — Guia interativo de configuração do Bot Telegram
Corre este script uma vez para configurar tudo.
"""

import os
import sys
import json
import time
import requests
from pathlib import Path

ENV_FILE = Path(__file__).parent / ".env"


def print_step(n, text):
    print(f"\n{'─'*50}")
    print(f"  Passo {n}: {text}")
    print(f"{'─'*50}")


def test_token(token: str) -> dict | None:
    r = requests.get(
        f"https://api.telegram.org/bot{token}/getMe",
        timeout=10
    )
    data = r.json()
    return data.get("result") if data.get("ok") else None


def get_chat_id(token: str) -> str | None:
    """Obtém o chat_id da primeira mensagem recebida pelo bot."""
    r = requests.get(
        f"https://api.telegram.org/bot{token}/getUpdates",
        timeout=10
    )
    updates = r.json().get("result", [])
    if updates:
        return str(updates[-1]["message"]["chat"]["id"])
    return None


def update_env(key: str, value: str):
    """Atualiza ou adiciona uma variável no .env"""
    content = ENV_FILE.read_text() if ENV_FILE.exists() else ""
    lines = content.splitlines()
    updated = False
    for i, line in enumerate(lines):
        if line.startswith(f"{key}="):
            lines[i] = f"{key}={value}"
            updated = True
            break
    if not updated:
        lines.append(f"{key}={value}")
    ENV_FILE.write_text("\n".join(lines) + "\n")


def main():
    print("\n" + "═"*50)
    print("  🤖 LOTTOCV BOT — CONFIGURAÇÃO TELEGRAM")
    print("═"*50)

    # ─── Passo 1: Token ───────────────────────
    print_step(1, "Criar o Bot no Telegram")
    print("""
  1. Abre o Telegram e procura por @BotFather
  2. Envia o comando: /newbot
  3. Escolhe um nome (ex: LottoCV)
  4. Escolhe um username (ex: lottocv_meu_bot)
  5. Copia o TOKEN que o BotFather te enviar
    """)
    token = input("  📋 Cola aqui o TOKEN do bot: ").strip()
    if not token or ":" not in token:
        print("  ❌ Token inválido. Tenta novamente.")
        sys.exit(1)

    print("\n  ⏳ A verificar token...")
    bot_info = test_token(token)
    if not bot_info:
        print("  ❌ Token inválido ou sem conexão à internet.")
        sys.exit(1)

    print(f"  ✅ Bot encontrado: @{bot_info['username']} ({bot_info['first_name']})")
    update_env("TELEGRAM_BOT_TOKEN", token)

    # ─── Passo 2: Chat ID ─────────────────────
    print_step(2, "Obter o teu Chat ID")
    print(f"""
  1. Abre o Telegram
  2. Procura pelo teu bot: @{bot_info['username']}
  3. Envia qualquer mensagem (ex: /start)
  4. Volta aqui e prime ENTER
    """)
    input("  ⏎ Prima ENTER depois de enviar a mensagem...")

    print("  ⏳ A obter o chat_id...")
    chat_id = get_chat_id(token)
    if chat_id:
        print(f"  ✅ Chat ID detectado: {chat_id}")
        update_env("TELEGRAM_CHAT_ID", chat_id)
    else:
        chat_id = input("  ⚠️  Não detetado. Cola o Chat ID manualmente: ").strip()
        update_env("TELEGRAM_CHAT_ID", chat_id)

    # ─── Passo 3: Limiar do jackpot ───────────
    print_step(3, "Definir limiar de alertas")
    print("""
  O bot enviará um alerta quando o jackpot atingir este valor.
  Valor padrão: 40.000 contos (40.000.000 ECV)
    """)
    limiar = input("  💰 Limiar em contos [40000]: ").strip() or "40000"
    try:
        limiar_ecv = int(limiar.replace(".", "").replace(",", "")) * 1000
        update_env("JACKPOT_CRITICO", str(limiar_ecv))
        print(f"  ✅ Limiar definido: {int(limiar):,} contos")
    except ValueError:
        print("  ⚠️  Valor inválido. Usando 40.000 contos.")
        update_env("JACKPOT_CRITICO", "40000000")

    # ─── Teste final ──────────────────────────
    print_step(4, "Teste de envio")
    print("  ⏳ A enviar mensagem de teste...")
    r = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": (
                "🎰 *LottoCV Bot configurado com sucesso!*\n\n"
                "Usa /start para começar.\n\n"
                "_Joga com responsabilidade._"
            ),
            "parse_mode": "Markdown"
        },
        timeout=10
    )
    if r.json().get("ok"):
        print("  ✅ Mensagem enviada! Verifica o Telegram.")
    else:
        print(f"  ❌ Erro no envio: {r.text}")

    # ─── Instruções finais ────────────────────
    print(f"""
{'═'*50}
  ✅ CONFIGURAÇÃO CONCLUÍDA!
{'═'*50}

  Para iniciar o bot, corre:

    python main.py bot

  Para iniciar o bot + scheduler integrado:

    python main.py tudo

  O ficheiro .env foi atualizado com as tuas credenciais.
{'═'*50}
    """)


if __name__ == "__main__":
    main()
