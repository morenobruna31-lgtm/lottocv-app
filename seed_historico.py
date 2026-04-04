"""
seed_historico.py — Popula a BD com histórico simulado realista
Baseado nos padrões reais do Totoloto CV (6/45)
Corre: python seed_historico.py
"""
import sys, os, random
sys.path.insert(0, os.path.dirname(__file__))

from database.models import init_db, init_apostas, init_orcamento, salvar_totoloto, salvar_joker, atualizar_jackpot

# Sorteios reais conhecidos (da API)
SORTEIOS_REAIS = [
    {"concurso": "13/2026", "data": "2026-03-28", "nums": [10,12,21,25,29,40], "joker": "447200"},
]

# Histórico simulado realista — 2 anos de sorteios semanais (~100 sorteios)
# Números com frequências baseadas em padrões reais de lotarias 6/45
FREQUENCIAS_BASE = {
    1:8, 2:5, 3:7, 4:6, 5:9, 6:4, 7:8, 8:6, 9:5, 10:7,
    11:9, 12:6, 13:5, 14:11, 15:7, 16:12, 17:9, 18:6, 19:7, 20:8,
    21:6, 22:5, 23:8, 24:6, 25:7, 26:8, 27:6, 28:10, 29:7, 30:5,
    31:4, 32:7, 33:8, 34:6, 35:9, 36:5, 37:4, 38:7, 39:6, 40:8,
    41:10, 42:6, 43:9, 44:11, 45:7,
}

def gerar_sorteio_ponderado():
    """Gera 6 números com base em frequências realistas."""
    pool = list(range(1, 46))
    pesos = [FREQUENCIAS_BASE[n] for n in pool]
    escolhidos = []
    while len(escolhidos) < 6:
        total = sum(pesos[i] for i, n in enumerate(pool) if n not in escolhidos)
        r = random.random() * total
        acum = 0
        for i, n in enumerate(pool):
            if n in escolhidos:
                continue
            acum += pesos[i]
            if acum >= r:
                escolhidos.append(n)
                break
    return sorted(escolhidos)

def gerar_joker():
    return ''.join([str(random.randint(0,9)) for _ in range(6)])

def main():
    random.seed(42)
    init_db()
    init_apostas()
    init_orcamento()
    print("A popular a base de dados com histórico...")

    # Inserir sorteios reais
    for s in SORTEIOS_REAIS:
        n = s["nums"]
        salvar_totoloto({
            "concurso": s["concurso"], "data": s["data"],
            "n1":n[0],"n2":n[1],"n3":n[2],"n4":n[3],"n5":n[4],"n6":n[5],
            "complementar": None, "jackpot": 0.0, "vencedores": 0
        })
        salvar_joker({
            "concurso": s["concurso"], "data": s["data"],
            "numero": s["joker"], "jackpot": 0.0, "vencedores": 0
        })

    # Gerar ~100 sorteios históricos (2024-2025)
    import datetime
    data_inicio = datetime.date(2024, 1, 6)  # Primeiro sábado de 2024
    jackpot = 5_000_000
    novos = 0

    for semana in range(103):  # ~2 anos
        data = data_inicio + datetime.timedelta(weeks=semana)
        if data >= datetime.date(2026, 3, 28):
            break  # Não sobrescreve dados reais

        concurso = f"{semana+1}/2024" if semana < 52 else f"{semana-51}/2025"
        nums = gerar_sorteio_ponderado()

        # Simula jackpot a crescer e resetar
        jackpot += random.randint(500_000, 2_000_000)
        if jackpot > 50_000_000:
            jackpot = 5_000_000  # Reset após alguém ganhar
        vencedores = 1 if jackpot > 45_000_000 else 0

        ok = salvar_totoloto({
            "concurso": concurso,
            "data": str(data),
            "n1":nums[0],"n2":nums[1],"n3":nums[2],
            "n4":nums[3],"n5":nums[4],"n6":nums[5],
            "complementar": random.randint(1,45),
            "jackpot": float(jackpot),
            "vencedores": vencedores
        })
        salvar_joker({
            "concurso": concurso, "data": str(data),
            "numero": gerar_joker(),
            "jackpot": float(jackpot * 0.15),
            "vencedores": 0
        })
        if ok: novos += 1

    # Atualiza jackpot atual
    atualizar_jackpot("totoloto", 38_500_000, "13/2026", "2026-03-28")
    atualizar_jackpot("joker",     8_200_000, "13/2026", "2026-03-28")

    print(f"✅ {novos} sorteios históricos inseridos!")
    print(f"✅ Jackpot atualizado: 38.500 contos")
    print(f"✅ Base de dados pronta — abre http://localhost:8000")

if __name__ == "__main__":
    main()
