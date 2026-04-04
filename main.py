"""
LottoCV — Ponto de entrada principal
Uso:
    python main.py scrape      → corre scraping agora
    python main.py recomendar  → mostra recomendação de aposta
    python main.py scheduler   → inicia agendador automático
    python main.py init        → inicializa base de dados
"""

import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)


def cmd_init():
    from database.models import init_db
    init_db()
    print("✅ Base de dados inicializada.")


def cmd_scrape():
    from scraper.scraper import executar_scraping
    resultado = executar_scraping()
    print("\n📊 Resultado:")
    print(f"  Jackpot Totoloto : {resultado['jackpot_totoloto']:,.0f} ECV")
    print(f"  Jackpot Joker    : {resultado['jackpot_joker']:,.0f} ECV")
    print(f"  Novos Totoloto   : {resultado['novos_totoloto']}")
    print(f"  Novos Joker      : {resultado['novos_joker']}")


def cmd_recomendar():
    from scraper.decision_engine import recomendar_estrategia
    rec = recomendar_estrategia()

    print(f"\n{'='*50}")
    print(f"  🎰 RECOMENDAÇÃO — TOTOLOTO CV")
    print(f"{'='*50}")
    print(f"  💰 Jackpot atual : {rec['jackpot_atual']:,.0f} ECV")
    print(f"  📊 Modo          : {rec['modo']}")
    print(f"  💳 Orçamento     : {rec['orcamento_usar']} ECV")
    print(f"\n  {rec['justificacao']}")
    print(f"\n  🔥 Números quentes: {rec['numeros_quentes']}")
    print(f"  ❄️  Números frios:  {rec['numeros_frios']}")
    print(f"\n  🎲 Combinações sugeridas:")
    for i, combo in enumerate(rec['combinacoes'], 1):
        numeros = "  ".join(f"{n:02d}" for n in combo)
        print(f"     Chave {i}: [ {numeros} ]")
    print(f"\n  📈 Baseado em {rec['total_sorteios_analisados']} sorteios históricos")
    print(f"{'='*50}\n")


def cmd_scheduler():
    from scheduler.scheduler import iniciar_scheduler
    iniciar_scheduler()


def cmd_bot():
    """Inicia só o bot Telegram (sem scheduler)."""
    from telegram_bot.bot import run_bot
    run_bot()


def cmd_setup_telegram():
    """Guia interativo para configurar o bot Telegram."""
    from telegram_bot.setup_telegram import main
    main()


def cmd_tudo():
    """Inicia o bot + scheduler integrado (modo produção)."""
    from telegram_bot.alert_scheduler import iniciar
    iniciar(modo="integrado")


COMANDOS = {
    "init":           cmd_init,
    "scrape":         cmd_scrape,
    "recomendar":     cmd_recomendar,
    "scheduler":      cmd_scheduler,
    "bot":            cmd_bot,
    "setup-telegram": cmd_setup_telegram,
    "tudo":           cmd_tudo,
}

if __name__ == '__main__':
    if len(sys.argv) < 2 or sys.argv[1] not in COMANDOS:
        print("Uso: python main.py [init | scrape | recomendar | scheduler | bot | setup-telegram | tudo]")
        sys.exit(1)

    COMANDOS[sys.argv[1]]()
