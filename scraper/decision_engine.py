"""
Motor de Decisão + Gerador de Combinações
Sorteio: 1× por semana, Sábado às 19h15
Orçamento: 1.000 ECV/mês

MODOS:
  MES_TOTOLOTO  — só Totoloto (30 ECV × 8 chaves × 4 semanas = 960 ECV)
  MES_COMPLETO  — Totoloto + Joker (100 ECV × 1 chave × 4 semanas = 400 ECV, ou 2 = 800 ECV)
"""

import random
from collections import Counter
from database.models import obter_historico_totoloto, obter_jackpot_atual

# ── Configuração ──────────────────────────────
CUSTO_TOTOLOTO      = 30
CUSTO_JOKER         = 70
CUSTO_CHAVE_COMPLETA= 100   # Totoloto + Joker

SORTEIOS_POR_MES    = 4     # 1× semana × 4 semanas
CHAVES_TOTOLOTO_MES = 8     # chaves por sorteio no modo Totoloto
ORCAMENTO_MENSAL    = 1_000

JACKPOT_MAXIMO      = 50_000_000
LIMIAR_JACKPOT      = 40_000_000

# Prémios Totoloto CV (Flow Down rule)
PREMIOS = {
    6: None,           # Jackpot (variável)
    5: 22_500_000,     # Flow down do máximo
    4: 10_000,
    3: 500,
    2: 0, 1: 0, 0: 0,
}

DESCRICAO_PREMIOS = {
    6: "🏆 JACKPOT — 1ª Categoria (6 acertos)",
    5: "🥈 2ª Categoria — 5 acertos (~22.500 contos)",
    4: "🥉 3ª Categoria — 4 acertos (~10 contos)",
    3: "✅ 4ª Categoria — 3 acertos (~500 ECV)",
    2: "❌ 2 acertos — sem prémio",
    1: "❌ 1 acerto — sem prémio",
    0: "❌ Sem acertos",
}


# ── Frequências ───────────────────────────────
def analisar_frequencias(historico):
    todos = []
    for s in historico:
        for c in ['n1','n2','n3','n4','n5','n6']:
            if s.get(c): todos.append(s[c])
    contagens = Counter(todos)
    for n in range(1, 46):
        if n not in contagens: contagens[n] = 0
    return dict(contagens)


def classificar_numeros(freq):
    ord_ = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    n = len(ord_)
    return {
        "quentes": [x for x,_ in ord_[:n//3]],
        "mornos":  [x for x,_ in ord_[n//3:2*n//3]],
        "frios":   [x for x,_ in ord_[2*n//3:]],
    }


# ── Gerador ───────────────────────────────────
def gerar_combinacao(classif, estrategia="equilibrada"):
    q, m, f = classif["quentes"], classif["mornos"], classif["frios"]
    if estrategia == "equilibrada":
        escolha = random.sample(q, min(3,len(q))) + random.sample(m, min(2,len(m))) + random.sample(f, min(1,len(f)))
    elif estrategia == "quentes":
        escolha = random.sample(q, min(4,len(q))) + random.sample(m, min(2,len(m)))
    else:
        escolha = random.sample(range(1,46), 6)
    escolha = list(set(escolha))
    while len(escolha) < 6:
        n = random.randint(1,45)
        if n not in escolha: escolha.append(n)
    return sorted(escolha[:6])


def gerar_multiplas_combinacoes(n=8, estrategia="equilibrada"):
    historico = obter_historico_totoloto()
    if not historico:
        return [sorted(random.sample(range(1,46), 6)) for _ in range(n)]
    freq   = analisar_frequencias(historico)
    classif= classificar_numeros(freq)
    combos, t = [], 0
    while len(combos) < n and t < 200:
        c = gerar_combinacao(classif, estrategia)
        if c not in combos: combos.append(c)
        t += 1
    return combos


# ── Motor de Decisão ──────────────────────────
def recomendar_estrategia(modo_mes="MES_TOTOLOTO"):
    """
    modo_mes: 'MES_TOTOLOTO' ou 'MES_COMPLETO'
    """
    jp_info  = obter_jackpot_atual("totoloto")
    jp_valor = jp_info["valor"] if jp_info else 0.0
    jackpot_alto = jp_valor >= LIMIAR_JACKPOT

    historico = obter_historico_totoloto()
    freq      = analisar_frequencias(historico) if historico else {}
    classif   = classificar_numeros(freq) if freq else {"quentes":[],"mornos":[],"frios":[]}

    if modo_mes == "MES_TOTOLOTO":
        # 8 chaves × 30 ECV × 4 sorteios = 960 ECV ≈ 1.000 ECV
        n_chaves   = CHAVES_TOTOLOTO_MES
        custo_sorteio = n_chaves * CUSTO_TOTOLOTO   # 240 ECV por sorteio
        custo_mes  = custo_sorteio * SORTEIOS_POR_MES  # 960 ECV
        modo       = "MÊS TOTOLOTO"
        justificacao = (
            f"🎯 Modo Totoloto exclusivo este mês!\n"
            f"Jogas {n_chaves} chaves por sorteio × {SORTEIOS_POR_MES} sorteios = "
            f"{n_chaves * SORTEIOS_POR_MES} chaves totais.\n"
            f"Custo: {custo_sorteio} ECV/sorteio × 4 = {custo_mes} ECV/mês.\n"
            f"Prémio máximo com 5 acertos: 22.500.000 ECV 🏅"
        )
    else:
        # MES_COMPLETO: Totoloto + Joker
        n_chaves = 2 if jackpot_alto else 1
        custo_sorteio = n_chaves * CUSTO_CHAVE_COMPLETA
        custo_mes  = custo_sorteio * SORTEIOS_POR_MES
        modo       = "MÊS COMPLETO" + (" 🔥" if jackpot_alto else "")
        justificacao = (
            f"{'🔥 Jackpot alto! ' if jackpot_alto else '📅 '}Modo Totoloto + Joker.\n"
            f"{n_chaves} chave(s) completa(s) por sorteio × 4 = {custo_mes} ECV/mês."
        )

    combinacoes = gerar_multiplas_combinacoes(n_chaves, "equilibrada")

    return {
        "modo":            modo,
        "modo_mes":        modo_mes,
        "jackpot_atual":   jp_valor,
        "jackpot_alto":    jackpot_alto,
        "justificacao":    justificacao,
        "combinacoes":     combinacoes,
        "n_chaves":        n_chaves,
        "orcamento_usar":  custo_sorteio,
        "custo_mes":       custo_mes,
        "sorteios_por_mes":SORTEIOS_POR_MES,
        "custo_por_chave": CUSTO_TOTOLOTO if modo_mes=="MES_TOTOLOTO" else CUSTO_CHAVE_COMPLETA,
        "numeros_quentes": classif["quentes"][:10],
        "numeros_frios":   classif["frios"][:10],
        "total_sorteios_analisados": len(historico),
        "premios":         {str(k): v for k,v in PREMIOS.items() if v},
        "descricao_premios": DESCRICAO_PREMIOS,
    }


def analisar_proximo_mes(historico_apostas=None):
    """
    Analisa se o próximo mês deve ser MES_TOTOLOTO ou MES_COMPLETO.
    Critérios: jackpot atual, tendência, resultados passados.
    """
    jp_info  = obter_jackpot_atual("totoloto")
    jp_valor = jp_info["valor"] if jp_info else 0.0

    if jp_valor >= LIMIAR_JACKPOT:
        recomendacao = "MES_COMPLETO"
        razao = f"Jackpot em {jp_valor/1_000_000:.1f}M ECV — vale jogar Totoloto + Joker para maximizar hipóteses."
    else:
        recomendacao = "MES_TOTOLOTO"
        razao = f"Jackpot em {jp_valor/1_000_000:.1f}M ECV. Recomendo manter Totoloto exclusivo — melhor custo-benefício com 8 chaves/sorteio."

    return {"recomendacao": recomendacao, "razao": razao, "jackpot": jp_valor}
