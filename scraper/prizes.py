"""
Tabela de prémios e verificação de acertos — Totoloto CV
Preços: Totoloto 30 ECV + Joker 70 ECV = 100 ECV por chave completa
"""

# Preços corrigidos
CUSTO_TOTOLOTO = 30    # ECV por chave Totoloto
CUSTO_JOKER    = 70    # ECV por chave Joker
CUSTO_CHAVE    = 100   # ECV total (Totoloto + Joker juntos)

ORCAMENTO_SEMANAL = 100   # 1 chave completa por semana
ORCAMENTO_MENSAL  = 400   # ~4 semanas por mês

JACKPOT_MAXIMO  = 50_000_000   # 50.000 contos ECV
LIMIAR_JACKPOT  = 40_000_000   # limiar para modo concentrado

# Tabela de prémios Totoloto CV (valores aproximados em ECV)
# Fonte: estrutura típica de lotaria 6/45
PREMIOS_TOTOLOTO = {
    6: None,       # Jackpot — valor variável
    5: 500_000,    # ~500 contos
    4: 10_000,     # ~10 contos
    3: 500,        # ~500 ECV
    2: 0,          # sem prémio
    1: 0,
    0: 0,
}

DESCRICAO_PREMIOS = {
    6: "🏆 JACKPOT — 1ª Categoria",
    5: "🥈 2ª Categoria — 5 acertos",
    4: "🥉 3ª Categoria — 4 acertos",
    3: "✅ 4ª Categoria — 3 acertos",
    2: "❌ 2 acertos — sem prémio",
    1: "❌ 1 acerto — sem prémio",
    0: "❌ Sem acertos",
}


def calcular_acertos(numeros_jogados: list[int], numeros_sorteados: list[int]) -> int:
    """Conta quantos números coincidiram."""
    return len(set(numeros_jogados) & set(numeros_sorteados))


def calcular_ganho(acertos: int, jackpot_atual: float = 0) -> float:
    """Devolve o ganho em ECV para o número de acertos dado."""
    if acertos == 6:
        return jackpot_atual if jackpot_atual > 0 else JACKPOT_MAXIMO
    return PREMIOS_TOTOLOTO.get(acertos, 0)


def verificar_aposta(numeros_jogados: list[int], sorteio: dict, jackpot: float = 0) -> dict:
    """
    Verifica uma aposta contra um sorteio.
    Devolve: { acertos, ganho, descricao, numeros_certos, numeros_errados }
    """
    sorteados = [sorteio.get(f'n{i}') for i in range(1, 7) if sorteio.get(f'n{i}')]
    acertos   = calcular_acertos(numeros_jogados, sorteados)
    ganho     = calcular_ganho(acertos, jackpot)

    certos  = [n for n in numeros_jogados if n in sorteados]
    errados = [n for n in numeros_jogados if n not in sorteados]

    return {
        "acertos":        acertos,
        "ganho":          ganho,
        "lucro":          ganho - CUSTO_TOTOLOTO,
        "descricao":      DESCRICAO_PREMIOS.get(acertos, ""),
        "numeros_certos": sorted(certos),
        "numeros_errados":sorted(errados),
        "numeros_sorteados": sorted(sorteados),
        "ganhou":         ganho > 0,
    }
