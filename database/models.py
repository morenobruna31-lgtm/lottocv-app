"""
Base de Dados - Modelos e configuracao
Usa PostgreSQL no Railway (DATABASE_URL), SQLite localmente
"""

import os
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL", "")
USE_POSTGRES = DATABASE_URL.startswith("postgres")

if USE_POSTGRES:
    import pg8000
else:
    import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'lotto_cv.db')


def get_connection():
    if USE_POSTGRES:
        from urllib.parse import urlparse
        u = urlparse(DATABASE_URL)
        return pg8000.connect(
            host=u.hostname,
            port=u.port or 5432,
            database=u.path.lstrip("/"),
            user=u.username,
            password=u.password,
            ssl_context=True
        )
    else:
        import sqlite3
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn


def _fetchall(cur):
    if USE_POSTGRES:
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]
    return [dict(r) for r in cur.fetchall()]


def _fetchone(cur):
    if USE_POSTGRES:
        row = cur.fetchone()
        if row is None:
            return None
        cols = [d[0] for d in cur.description]
        return dict(zip(cols, row))
    row = cur.fetchone()
    return dict(row) if row else None


def init_db():
    conn = get_connection()
    cur = conn.cursor()
    if USE_POSTGRES:
        cur.execute("""CREATE TABLE IF NOT EXISTS totoloto (id SERIAL PRIMARY KEY, concurso TEXT UNIQUE, data TEXT, n1 INTEGER, n2 INTEGER, n3 INTEGER, n4 INTEGER, n5 INTEGER, n6 INTEGER, complementar INTEGER, jackpot REAL, vencedores INTEGER, criado_em TEXT DEFAULT NOW()::TEXT)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS joker (id SERIAL PRIMARY KEY, concurso TEXT UNIQUE, data TEXT, numero TEXT, jackpot REAL, vencedores INTEGER, criado_em TEXT DEFAULT NOW()::TEXT)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS jackpot_atual (id SERIAL PRIMARY KEY, jogo TEXT, valor REAL, concurso TEXT, data_sorteio TEXT, atualizado_em TEXT DEFAULT NOW()::TEXT)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS scraper_log (id SERIAL PRIMARY KEY, status TEXT, mensagem TEXT, registos_novos INTEGER DEFAULT 0, executado_em TEXT DEFAULT NOW()::TEXT)""")
    else:
        cur.execute("""CREATE TABLE IF NOT EXISTS totoloto (id INTEGER PRIMARY KEY AUTOINCREMENT, concurso TEXT UNIQUE, data TEXT, n1 INTEGER, n2 INTEGER, n3 INTEGER, n4 INTEGER, n5 INTEGER, n6 INTEGER, complementar INTEGER, jackpot REAL, vencedores INTEGER, criado_em TEXT DEFAULT (datetime('now')))""")
        cur.execute("""CREATE TABLE IF NOT EXISTS joker (id INTEGER PRIMARY KEY AUTOINCREMENT, concurso TEXT UNIQUE, data TEXT, numero TEXT, jackpot REAL, vencedores INTEGER, criado_em TEXT DEFAULT (datetime('now')))""")
        cur.execute("""CREATE TABLE IF NOT EXISTS jackpot_atual (id INTEGER PRIMARY KEY AUTOINCREMENT, jogo TEXT, valor REAL, concurso TEXT, data_sorteio TEXT, atualizado_em TEXT DEFAULT (datetime('now')))""")
        cur.execute("""CREATE TABLE IF NOT EXISTS scraper_log (id INTEGER PRIMARY KEY AUTOINCREMENT, status TEXT, mensagem TEXT, registos_novos INTEGER DEFAULT 0, executado_em TEXT DEFAULT (datetime('now')))""")
    conn.commit()
    conn.close()
    print("[DB] Base de dados inicializada com sucesso.")


def salvar_totoloto(dados: dict) -> bool:
    conn = get_connection()
    try:
        cur = conn.cursor()
        if USE_POSTGRES:
            cur.execute("""INSERT INTO totoloto (concurso,data,n1,n2,n3,n4,n5,n6,complementar,jackpot,vencedores) VALUES (%(concurso)s,%(data)s,%(n1)s,%(n2)s,%(n3)s,%(n4)s,%(n5)s,%(n6)s,%(complementar)s,%(jackpot)s,%(vencedores)s) ON CONFLICT (concurso) DO NOTHING""", dados)
        else:
            cur.execute("""INSERT OR IGNORE INTO totoloto (concurso,data,n1,n2,n3,n4,n5,n6,complementar,jackpot,vencedores) VALUES (:concurso,:data,:n1,:n2,:n3,:n4,:n5,:n6,:complementar,:jackpot,:vencedores)""", dados)
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def salvar_joker(dados: dict) -> bool:
    conn = get_connection()
    try:
        cur = conn.cursor()
        if USE_POSTGRES:
            cur.execute("""INSERT INTO joker (concurso,data,numero,jackpot,vencedores) VALUES (%(concurso)s,%(data)s,%(numero)s,%(jackpot)s,%(vencedores)s) ON CONFLICT (concurso) DO NOTHING""", dados)
        else:
            cur.execute("""INSERT OR IGNORE INTO joker (concurso,data,numero,jackpot,vencedores) VALUES (:concurso,:data,:numero,:jackpot,:vencedores)""", dados)
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def atualizar_jackpot(jogo: str, valor: float, concurso: str, data_sorteio: str):
    conn = get_connection()
    cur = conn.cursor()
    if USE_POSTGRES:
        cur.execute("DELETE FROM jackpot_atual WHERE jogo = %s", (jogo,))
        cur.execute("INSERT INTO jackpot_atual (jogo,valor,concurso,data_sorteio) VALUES (%s,%s,%s,%s)", (jogo,valor,concurso,data_sorteio))
    else:
        cur.execute("DELETE FROM jackpot_atual WHERE jogo = ?", (jogo,))
        cur.execute("INSERT INTO jackpot_atual (jogo,valor,concurso,data_sorteio) VALUES (?,?,?,?)", (jogo,valor,concurso,data_sorteio))
    conn.commit()
    conn.close()


def registar_log(status: str, mensagem: str, registos_novos: int = 0):
    conn = get_connection()
    cur = conn.cursor()
    if USE_POSTGRES:
        cur.execute("INSERT INTO scraper_log (status,mensagem,registos_novos) VALUES (%s,%s,%s)", (status,mensagem,registos_novos))
    else:
        cur.execute("INSERT INTO scraper_log (status,mensagem,registos_novos) VALUES (?,?,?)", (status,mensagem,registos_novos))
    conn.commit()
    conn.close()


def obter_historico_totoloto(limite: int = 200) -> list:
    conn = get_connection()
    cur = conn.cursor()
    if USE_POSTGRES:
        cur.execute("SELECT * FROM totoloto ORDER BY data DESC LIMIT %s", (limite,))
    else:
        cur.execute("SELECT * FROM totoloto ORDER BY data DESC LIMIT ?", (limite,))
    rows = _fetchall(cur)
    conn.close()
    return rows


def obter_jackpot_atual(jogo: str = 'totoloto'):
    conn = get_connection()
    cur = conn.cursor()
    if USE_POSTGRES:
        cur.execute("SELECT * FROM jackpot_atual WHERE jogo = %s", (jogo,))
    else:
        cur.execute("SELECT * FROM jackpot_atual WHERE jogo = ?", (jogo,))
    row = _fetchone(cur)
    conn.close()
    return row


def get_connection_raw():
    return get_connection()


if __name__ == '__main__':
    init_db()


def init_apostas():
    conn = get_connection()
    cur = conn.cursor()
    if USE_POSTGRES:
        cur.execute("""CREATE TABLE IF NOT EXISTS apostas (id SERIAL PRIMARY KEY, concurso TEXT, jogo TEXT DEFAULT 'totoloto', n1 INTEGER, n2 INTEGER, n3 INTEGER, n4 INTEGER, n5 INTEGER, n6 INTEGER, custo REAL DEFAULT 100.0, acertos INTEGER DEFAULT -1, ganho REAL DEFAULT 0, verificado INTEGER DEFAULT 0, nota TEXT DEFAULT '', jogado_em TEXT DEFAULT NOW()::TEXT)""")
    else:
        cur.execute("""CREATE TABLE IF NOT EXISTS apostas (id INTEGER PRIMARY KEY AUTOINCREMENT, concurso TEXT, jogo TEXT DEFAULT 'totoloto', n1 INTEGER, n2 INTEGER, n3 INTEGER, n4 INTEGER, n5 INTEGER, n6 INTEGER, custo REAL DEFAULT 100.0, acertos INTEGER DEFAULT -1, ganho REAL DEFAULT 0, verificado INTEGER DEFAULT 0, nota TEXT DEFAULT '', jogado_em TEXT DEFAULT (datetime('now')))""")
    conn.commit()
    conn.close()


def salvar_aposta(dados: dict) -> int:
    conn = get_connection()
    cur = conn.cursor()
    if USE_POSTGRES:
        cur.execute("""INSERT INTO apostas (concurso,jogo,n1,n2,n3,n4,n5,n6,custo,nota) VALUES (%(concurso)s,%(jogo)s,%(n1)s,%(n2)s,%(n3)s,%(n4)s,%(n5)s,%(n6)s,%(custo)s,%(nota)s) RETURNING id""", dados)
        new_id = cur.fetchone()[0]
    else:
        cur.execute("""INSERT INTO apostas (concurso,jogo,n1,n2,n3,n4,n5,n6,custo,nota) VALUES (:concurso,:jogo,:n1,:n2,:n3,:n4,:n5,:n6,:custo,:nota)""", dados)
        new_id = cur.lastrowid
    conn.commit()
    conn.close()
    return new_id


def obter_apostas(limite: int = 20) -> list:
    conn = get_connection()
    cur = conn.cursor()
    if USE_POSTGRES:
        cur.execute("SELECT * FROM apostas ORDER BY jogado_em DESC LIMIT %s", (limite,))
    else:
        cur.execute("SELECT * FROM apostas ORDER BY jogado_em DESC LIMIT ?", (limite,))
    rows = _fetchall(cur)
    conn.close()
    return rows


def obter_apostas_por_concurso(concurso: str) -> list:
    conn = get_connection()
    cur = conn.cursor()
    if USE_POSTGRES:
        cur.execute("SELECT * FROM apostas WHERE concurso = %s AND verificado = 0", (concurso,))
    else:
        cur.execute("SELECT * FROM apostas WHERE concurso = ? AND verificado = 0", (concurso,))
    rows = _fetchall(cur)
    conn.close()
    return rows


def atualizar_resultado_aposta(aposta_id: int, acertos: int, ganho: float):
    conn = get_connection()
    cur = conn.cursor()
    if USE_POSTGRES:
        cur.execute("UPDATE apostas SET acertos=%s,ganho=%s,verificado=1 WHERE id=%s", (acertos,ganho,aposta_id))
    else:
        cur.execute("UPDATE apostas SET acertos=?,ganho=?,verificado=1 WHERE id=?", (acertos,ganho,aposta_id))
    conn.commit()
    conn.close()


def init_orcamento():
    conn = get_connection()
    cur = conn.cursor()
    if USE_POSTGRES:
        cur.execute("""CREATE TABLE IF NOT EXISTS orcamento (id SERIAL PRIMARY KEY, mes TEXT, total REAL DEFAULT 1000.0, gasto REAL DEFAULT 0.0, atualizado TEXT DEFAULT NOW()::TEXT)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS gastos (id SERIAL PRIMARY KEY, mes TEXT, valor REAL, descricao TEXT, data TEXT DEFAULT NOW()::TEXT)""")
    else:
        cur.execute("""CREATE TABLE IF NOT EXISTS orcamento (id INTEGER PRIMARY KEY AUTOINCREMENT, mes TEXT, total REAL DEFAULT 1000.0, gasto REAL DEFAULT 0.0, atualizado TEXT DEFAULT (datetime('now')))""")
        cur.execute("""CREATE TABLE IF NOT EXISTS gastos (id INTEGER PRIMARY KEY AUTOINCREMENT, mes TEXT, valor REAL, descricao TEXT, data TEXT DEFAULT (datetime('now')))""")
    conn.commit()
    conn.close()


def obter_orcamento_mes(mes: str) -> dict:
    conn = get_connection()
    cur = conn.cursor()
    if USE_POSTGRES:
        cur.execute("SELECT * FROM orcamento WHERE mes = %s", (mes,))
        row = _fetchone(cur)
        if not row:
            cur.execute("INSERT INTO orcamento (mes,total,gasto) VALUES (%s,1000.0,0.0)", (mes,))
            conn.commit()
            cur.execute("SELECT * FROM orcamento WHERE mes = %s", (mes,))
            row = _fetchone(cur)
        cur.execute("SELECT * FROM gastos WHERE mes = %s ORDER BY data DESC", (mes,))
        gastos = _fetchall(cur)
    else:
        cur.execute("SELECT * FROM orcamento WHERE mes = ?", (mes,))
        row = _fetchone(cur)
        if not row:
            cur.execute("INSERT INTO orcamento (mes,total,gasto) VALUES (?,1000.0,0.0)", (mes,))
            conn.commit()
            cur.execute("SELECT * FROM orcamento WHERE mes = ?", (mes,))
            row = _fetchone(cur)
        cur.execute("SELECT * FROM gastos WHERE mes = ? ORDER BY data DESC", (mes,))
        gastos = _fetchall(cur)
    conn.close()
    row['gastos_lista'] = gastos
    row['restante'] = row['total'] - row['gasto']
    return row


def registar_gasto(mes: str, valor: float, descricao: str = "") -> dict:
    conn = get_connection()
    cur = conn.cursor()
    if USE_POSTGRES:
        cur.execute("SELECT id FROM orcamento WHERE mes = %s", (mes,))
        if not cur.fetchone():
            cur.execute("INSERT INTO orcamento (mes,total,gasto) VALUES (%s,1000.0,0.0)", (mes,))
        cur.execute("INSERT INTO gastos (mes,valor,descricao) VALUES (%s,%s,%s)", (mes,valor,descricao))
        cur.execute("UPDATE orcamento SET gasto=gasto+%s WHERE mes=%s", (valor,mes))
    else:
        cur.execute("SELECT id FROM orcamento WHERE mes = ?", (mes,))
        if not cur.fetchone():
            cur.execute("INSERT INTO orcamento (mes,total,gasto) VALUES (?,1000.0,0.0)", (mes,))
        cur.execute("INSERT INTO gastos (mes,valor,descricao) VALUES (?,?,?)", (mes,valor,descricao))
        cur.execute("UPDATE orcamento SET gasto=gasto+? WHERE mes=?", (valor,mes))
    conn.commit()
    conn.close()
    return obter_orcamento_mes(mes)


def desfazer_ultimo_gasto(mes: str) -> dict:
    conn = get_connection()
    cur = conn.cursor()
    if USE_POSTGRES:
        cur.execute("SELECT * FROM gastos WHERE mes = %s ORDER BY data DESC LIMIT 1", (mes,))
        row = _fetchone(cur)
        if row:
            cur.execute("DELETE FROM gastos WHERE id = %s", (row['id'],))
            cur.execute("UPDATE orcamento SET gasto=gasto-%s WHERE mes=%s", (row['valor'],mes))
            conn.commit()
    else:
        cur.execute("SELECT * FROM gastos WHERE mes = ? ORDER BY data DESC LIMIT 1", (mes,))
        row = _fetchone(cur)
        if row:
            cur.execute("DELETE FROM gastos WHERE id = ?", (row['id'],))
            cur.execute("UPDATE orcamento SET gasto=gasto-? WHERE mes=?", (row['valor'],mes))
            conn.commit()
    conn.close()
    return obter_orcamento_mes(mes)






