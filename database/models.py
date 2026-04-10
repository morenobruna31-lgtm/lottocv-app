"""
Base de Dados — Suporta SQLite (local) e PostgreSQL (Railway/cloud)
Detecta automaticamente via DATABASE_URL
"""
import os
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "")

# ── Decide qual BD usar ────────────────────────
USE_POSTGRES = DATABASE_URL.startswith("postgresql") or DATABASE_URL.startswith("postgres")

if USE_POSTGRES:
    import psycopg2
    import psycopg2.extras
    def get_connection():
        url = DATABASE_URL.replace("postgres://", "postgresql://", 1)
        conn = psycopg2.connect(url)
        return conn
    PH = "%s"   # placeholder PostgreSQL
else:
    import sqlite3
    DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'lotto_cv.db')
    def get_connection():
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    PH = "?"    # placeholder SQLite


def _row_to_dict(row):
    if row is None:
        return None
    if USE_POSTGRES:
        return dict(row)
    return dict(row)


def _fetchall(cur):
    rows = cur.fetchall()
    if USE_POSTGRES:
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in rows]
    return [dict(r) for r in rows]


def _fetchone(cur):
    row = cur.fetchone()
    if row is None:
        return None
    if USE_POSTGRES:
        cols = [d[0] for d in cur.description]
        return dict(zip(cols, row))
    return dict(row)


def _auto(t):
    """NOW() for postgres, datetime('now') for sqlite"""
    return "NOW()" if USE_POSTGRES else "datetime('now')"


# ── Init ──────────────────────────────────────
def init_db():
    conn = get_connection()
    cur  = conn.cursor()

    if USE_POSTGRES:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS totoloto (
                id          SERIAL PRIMARY KEY,
                concurso    TEXT UNIQUE,
                data        TEXT,
                n1 INT, n2 INT, n3 INT, n4 INT, n5 INT, n6 INT,
                complementar INT,
                jackpot     REAL DEFAULT 0,
                vencedores  INT  DEFAULT 0,
                criado_em   TIMESTAMP DEFAULT NOW()
            )""")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS joker (
                id          SERIAL PRIMARY KEY,
                concurso    TEXT UNIQUE,
                data        TEXT,
                numero      TEXT,
                jackpot     REAL DEFAULT 0,
                vencedores  INT  DEFAULT 0,
                criado_em   TIMESTAMP DEFAULT NOW()
            )""")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS jackpot_atual (
                id          SERIAL PRIMARY KEY,
                jogo        TEXT,
                valor       REAL,
                concurso    TEXT,
                data_sorteio TEXT,
                atualizado_em TIMESTAMP DEFAULT NOW()
            )""")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS scraper_log (
                id          SERIAL PRIMARY KEY,
                status      TEXT,
                mensagem    TEXT,
                registos_novos INT DEFAULT 0,
                executado_em TIMESTAMP DEFAULT NOW()
            )""")
    else:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS totoloto (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                concurso TEXT UNIQUE, data TEXT,
                n1 INT, n2 INT, n3 INT, n4 INT, n5 INT, n6 INT,
                complementar INT, jackpot REAL DEFAULT 0, vencedores INT DEFAULT 0,
                criado_em TEXT DEFAULT (datetime('now'))
            )""")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS joker (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                concurso TEXT UNIQUE, data TEXT,
                numero TEXT, jackpot REAL DEFAULT 0, vencedores INT DEFAULT 0,
                criado_em TEXT DEFAULT (datetime('now'))
            )""")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS jackpot_atual (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                jogo TEXT, valor REAL, concurso TEXT, data_sorteio TEXT,
                atualizado_em TEXT DEFAULT (datetime('now'))
            )""")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS scraper_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                status TEXT, mensagem TEXT, registos_novos INT DEFAULT 0,
                executado_em TEXT DEFAULT (datetime('now'))
            )""")

    conn.commit()
    cur.close()
    conn.close()
    print(f"[DB] Inicializada ({'PostgreSQL' if USE_POSTGRES else 'SQLite'})")


def init_apostas():
    conn = get_connection()
    cur  = conn.cursor()
    if USE_POSTGRES:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS apostas (
                id SERIAL PRIMARY KEY,
                concurso TEXT, jogo TEXT DEFAULT 'totoloto',
                n1 INT, n2 INT, n3 INT, n4 INT, n5 INT, n6 INT,
                custo REAL DEFAULT 100,
                acertos INT DEFAULT -1, ganho REAL DEFAULT 0,
                verificado INT DEFAULT 0, nota TEXT DEFAULT '',
                jogado_em TIMESTAMP DEFAULT NOW()
            )""")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS orcamento (
                id SERIAL PRIMARY KEY,
                mes TEXT, total REAL DEFAULT 1000, gasto REAL DEFAULT 0,
                atualizado TIMESTAMP DEFAULT NOW()
            )""")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS gastos (
                id SERIAL PRIMARY KEY,
                mes TEXT, valor REAL, descricao TEXT,
                data TIMESTAMP DEFAULT NOW()
            )""")
    else:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS apostas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                concurso TEXT, jogo TEXT DEFAULT 'totoloto',
                n1 INT, n2 INT, n3 INT, n4 INT, n5 INT, n6 INT,
                custo REAL DEFAULT 100, acertos INT DEFAULT -1,
                ganho REAL DEFAULT 0, verificado INT DEFAULT 0,
                nota TEXT DEFAULT '', jogado_em TEXT DEFAULT (datetime('now'))
            )""")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS orcamento (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mes TEXT, total REAL DEFAULT 1000, gasto REAL DEFAULT 0,
                atualizado TEXT DEFAULT (datetime('now'))
            )""")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS gastos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mes TEXT, valor REAL, descricao TEXT,
                data TEXT DEFAULT (datetime('now'))
            )""")
    conn.commit()
    cur.close()
    conn.close()


def init_orcamento():
    init_apostas()  # já cria as tabelas de orçamento


# ── CRUD Totoloto ─────────────────────────────
def salvar_totoloto(d: dict) -> bool:
    conn = get_connection()
    cur  = conn.cursor()
    try:
        if USE_POSTGRES:
            sql = """INSERT INTO totoloto (concurso,data,n1,n2,n3,n4,n5,n6,complementar,jackpot,vencedores)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (concurso) DO NOTHING"""
        else:
            sql = """INSERT OR IGNORE INTO totoloto (concurso,data,n1,n2,n3,n4,n5,n6,complementar,jackpot,vencedores)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)"""
        cur.execute(sql, (d['concurso'],d['data'],d['n1'],d['n2'],d['n3'],
              d['n4'],d['n5'],d['n6'],d.get('complementar'),
              d.get('jackpot',0),d.get('vencedores',0)))
        conn.commit()
        changed = cur.rowcount > 0
        return changed
    finally:
        cur.close(); conn.close()


def salvar_joker(d: dict) -> bool:
    conn = get_connection()
    cur  = conn.cursor()
    try:
        if USE_POSTGRES:
            sql = "INSERT INTO joker (concurso,data,numero,jackpot,vencedores) VALUES (%s,%s,%s,%s,%s) ON CONFLICT (concurso) DO NOTHING"
        else:
            sql = "INSERT OR IGNORE INTO joker (concurso,data,numero,jackpot,vencedores) VALUES (?,?,?,?,?)"
        cur.execute(sql, (d['concurso'],d['data'],d['numero'],
              d.get('jackpot',0),d.get('vencedores',0)))
        conn.commit()
        changed = cur.rowcount > 0
        return changed
    finally:
        cur.close(); conn.close()


def atualizar_jackpot(jogo: str, valor: float, concurso: str, data_sorteio: str):
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute(f"DELETE FROM jackpot_atual WHERE jogo={PH}", (jogo,))
    cur.execute(f"""
        INSERT INTO jackpot_atual (jogo,valor,concurso,data_sorteio)
        VALUES ({PH},{PH},{PH},{PH})
    """, (jogo, valor, concurso, data_sorteio))
    conn.commit()
    cur.close(); conn.close()


def registar_log(status, mensagem, registos_novos=0):
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute(f"""
        INSERT INTO scraper_log (status,mensagem,registos_novos)
        VALUES ({PH},{PH},{PH})
    """, (status, mensagem, registos_novos))
    conn.commit()
    cur.close(); conn.close()


def obter_historico_totoloto(limite=200):
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute(f"SELECT * FROM totoloto ORDER BY data DESC LIMIT {PH}", (limite,))
    rows = _fetchall(cur)
    cur.close(); conn.close()
    return rows


def obter_jackpot_atual(jogo='totoloto'):
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute(f"SELECT * FROM jackpot_atual WHERE jogo={PH}", (jogo,))
    row = _fetchone(cur)
    cur.close(); conn.close()
    return row


# ── Apostas ───────────────────────────────────
def salvar_aposta(d: dict) -> int:
    conn = get_connection()
    cur  = conn.cursor()
    if USE_POSTGRES:
        cur.execute(f"""
            INSERT INTO apostas (concurso,jogo,n1,n2,n3,n4,n5,n6,custo,nota)
            VALUES ({PH},{PH},{PH},{PH},{PH},{PH},{PH},{PH},{PH},{PH})
            RETURNING id
        """, (d['concurso'],d['jogo'],d['n1'],d['n2'],d['n3'],
              d['n4'],d['n5'],d['n6'],d.get('custo',100),d.get('nota','')))
        new_id = cur.fetchone()[0]
    else:
        cur.execute(f"""
            INSERT INTO apostas (concurso,jogo,n1,n2,n3,n4,n5,n6,custo,nota)
            VALUES ({PH},{PH},{PH},{PH},{PH},{PH},{PH},{PH},{PH},{PH})
        """, (d['concurso'],d['jogo'],d['n1'],d['n2'],d['n3'],
              d['n4'],d['n5'],d['n6'],d.get('custo',100),d.get('nota','')))
        new_id = cur.lastrowid
    conn.commit()
    cur.close(); conn.close()
    return new_id


def obter_apostas(limite=20):
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute(f"SELECT * FROM apostas ORDER BY jogado_em DESC LIMIT {PH}", (limite,))
    rows = _fetchall(cur)
    cur.close(); conn.close()
    # Convert timestamps to string
    for r in rows:
        if 'jogado_em' in r and not isinstance(r['jogado_em'], str):
            r['jogado_em'] = str(r['jogado_em'])
    return rows


def obter_apostas_por_concurso(concurso: str):
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute(f"SELECT * FROM apostas WHERE concurso={PH} AND verificado=0", (concurso,))
    rows = _fetchall(cur)
    cur.close(); conn.close()
    return rows


def atualizar_resultado_aposta(aposta_id: int, acertos: int, ganho: float):
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute(f"UPDATE apostas SET acertos={PH}, ganho={PH}, verificado=1 WHERE id={PH}",
                (acertos, ganho, aposta_id))
    conn.commit()
    cur.close(); conn.close()


# ── Orçamento ─────────────────────────────────
def obter_orcamento_mes(mes: str) -> dict:
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute(f"SELECT * FROM orcamento WHERE mes={PH}", (mes,))
    row = _fetchone(cur)
    if not row:
        cur.execute(f"INSERT INTO orcamento (mes,total,gasto) VALUES ({PH},1000,0)", (mes,))
        conn.commit()
        cur.execute(f"SELECT * FROM orcamento WHERE mes={PH}", (mes,))
        row = _fetchone(cur)
    cur.execute(f"SELECT * FROM gastos WHERE mes={PH} ORDER BY data DESC", (mes,))
    gastos = _fetchall(cur)
    cur.close(); conn.close()
    # Convert timestamps
    for g in gastos:
        if 'data' in g and not isinstance(g['data'], str):
            g['data'] = str(g['data'])
    row['gastos_lista'] = gastos
    row['restante'] = row['total'] - row['gasto']
    return row


def registar_gasto(mes: str, valor: float, descricao: str = "") -> dict:
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute(f"SELECT id FROM orcamento WHERE mes={PH}", (mes,))
    if not cur.fetchone():
        cur.execute(f"INSERT INTO orcamento (mes,total,gasto) VALUES ({PH},1000,0)", (mes,))
    cur.execute(f"INSERT INTO gastos (mes,valor,descricao) VALUES ({PH},{PH},{PH})",
                (mes, valor, descricao))
    cur.execute(f"UPDATE orcamento SET gasto=gasto+{PH} WHERE mes={PH}", (valor, mes))
    conn.commit()
    cur.close(); conn.close()
    return obter_orcamento_mes(mes)


def desfazer_ultimo_gasto(mes: str) -> dict:
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute(f"SELECT * FROM gastos WHERE mes={PH} ORDER BY data DESC LIMIT 1", (mes,))
    row = _fetchone(cur)
    if row:
        cur.execute(f"DELETE FROM gastos WHERE id={PH}", (row['id'],))
        cur.execute(f"UPDATE orcamento SET gasto=gasto-{PH} WHERE mes={PH}", (row['valor'], mes))
        conn.commit()
    cur.close(); conn.close()
    return obter_orcamento_mes(mes)


if __name__ == '__main__':
    init_db()
    init_apostas()
