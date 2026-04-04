"""
Base de Dados — Modelos e configuração
Usa SQLite localmente, facilmente migrável para PostgreSQL na cloud
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'lotto_cv.db')


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Cria todas as tabelas se não existirem."""
    conn = get_connection()
    cur = conn.cursor()

    # Tabela de sorteios do Totoloto
    cur.execute("""
        CREATE TABLE IF NOT EXISTS totoloto (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            concurso    TEXT UNIQUE,
            data        TEXT,
            n1 INTEGER, n2 INTEGER, n3 INTEGER,
            n4 INTEGER, n5 INTEGER, n6 INTEGER,
            complementar INTEGER,
            jackpot     REAL,
            vencedores  INTEGER,
            criado_em   TEXT DEFAULT (datetime('now'))
        )
    """)

    # Tabela de sorteios do Joker
    cur.execute("""
        CREATE TABLE IF NOT EXISTS joker (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            concurso    TEXT UNIQUE,
            data        TEXT,
            numero      TEXT,
            jackpot     REAL,
            vencedores  INTEGER,
            criado_em   TEXT DEFAULT (datetime('now'))
        )
    """)

    # Tabela do jackpot atual (atualizada a cada scraping)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS jackpot_atual (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            jogo        TEXT,
            valor       REAL,
            concurso    TEXT,
            data_sorteio TEXT,
            atualizado_em TEXT DEFAULT (datetime('now'))
        )
    """)

    # Tabela de log de execuções do scraper
    cur.execute("""
        CREATE TABLE IF NOT EXISTS scraper_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            status      TEXT,
            mensagem    TEXT,
            registos_novos INTEGER DEFAULT 0,
            executado_em TEXT DEFAULT (datetime('now'))
        )
    """)

    conn.commit()
    conn.close()
    print("[DB] Base de dados inicializada com sucesso.")


def salvar_totoloto(dados: dict) -> bool:
    """Insere um sorteio do Totoloto. Ignora duplicados."""
    conn = get_connection()
    try:
        conn.execute("""
            INSERT OR IGNORE INTO totoloto
                (concurso, data, n1, n2, n3, n4, n5, n6, complementar, jackpot, vencedores)
            VALUES
                (:concurso, :data, :n1, :n2, :n3, :n4, :n5, :n6, :complementar, :jackpot, :vencedores)
        """, dados)
        conn.commit()
        return conn.total_changes > 0
    finally:
        conn.close()


def salvar_joker(dados: dict) -> bool:
    """Insere um sorteio do Joker. Ignora duplicados."""
    conn = get_connection()
    try:
        conn.execute("""
            INSERT OR IGNORE INTO joker
                (concurso, data, numero, jackpot, vencedores)
            VALUES
                (:concurso, :data, :numero, :jackpot, :vencedores)
        """, dados)
        conn.commit()
        return conn.total_changes > 0
    finally:
        conn.close()


def atualizar_jackpot(jogo: str, valor: float, concurso: str, data_sorteio: str):
    """Guarda o valor atual do jackpot (apaga o anterior do mesmo jogo)."""
    conn = get_connection()
    conn.execute("DELETE FROM jackpot_atual WHERE jogo = ?", (jogo,))
    conn.execute("""
        INSERT INTO jackpot_atual (jogo, valor, concurso, data_sorteio)
        VALUES (?, ?, ?, ?)
    """, (jogo, valor, concurso, data_sorteio))
    conn.commit()
    conn.close()


def registar_log(status: str, mensagem: str, registos_novos: int = 0):
    conn = get_connection()
    conn.execute("""
        INSERT INTO scraper_log (status, mensagem, registos_novos)
        VALUES (?, ?, ?)
    """, (status, mensagem, registos_novos))
    conn.commit()
    conn.close()


def obter_historico_totoloto(limite: int = 200) -> list:
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM totoloto ORDER BY data DESC LIMIT ?
    """, (limite,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def obter_jackpot_atual(jogo: str = 'totoloto') -> dict | None:
    conn = get_connection()
    row = conn.execute("""
        SELECT * FROM jackpot_atual WHERE jogo = ?
    """, (jogo,)).fetchone()
    conn.close()
    return dict(row) if row else None


if __name__ == '__main__':
    init_db()


# ──────────────────────────────────────────────
# Tabela de Apostas Jogadas
# ──────────────────────────────────────────────
def init_apostas():
    """Cria tabela de apostas se não existir."""
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS apostas (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            concurso     TEXT,
            jogo         TEXT DEFAULT 'totoloto',
            n1 INTEGER, n2 INTEGER, n3 INTEGER,
            n4 INTEGER, n5 INTEGER, n6 INTEGER,
            custo        REAL DEFAULT 100.0,
            acertos      INTEGER DEFAULT -1,
            ganho        REAL DEFAULT 0,
            verificado   INTEGER DEFAULT 0,
            nota         TEXT DEFAULT '',
            jogado_em    TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    conn.close()


def salvar_aposta(dados: dict) -> int:
    """Guarda uma aposta jogada. Devolve o id."""
    conn = get_connection()
    cur = conn.execute("""
        INSERT INTO apostas (concurso, jogo, n1, n2, n3, n4, n5, n6, custo, nota)
        VALUES (:concurso, :jogo, :n1, :n2, :n3, :n4, :n5, :n6, :custo, :nota)
    """, dados)
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id


def obter_apostas(limite: int = 20) -> list:
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM apostas ORDER BY jogado_em DESC LIMIT ?
    """, (limite,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def obter_apostas_por_concurso(concurso: str) -> list:
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM apostas WHERE concurso = ? AND verificado = 0
    """, (concurso,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def atualizar_resultado_aposta(aposta_id: int, acertos: int, ganho: float):
    conn = get_connection()
    conn.execute("""
        UPDATE apostas SET acertos=?, ganho=?, verificado=1 WHERE id=?
    """, (acertos, ganho, aposta_id))
    conn.commit()
    conn.close()


# ──────────────────────────────────────────────
# Tracker de Orçamento
# ──────────────────────────────────────────────
def init_orcamento():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS orcamento (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            mes        TEXT,
            total      REAL DEFAULT 1000.0,
            gasto      REAL DEFAULT 0.0,
            atualizado TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS gastos (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            mes       TEXT,
            valor     REAL,
            descricao TEXT,
            data      TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    conn.close()


def obter_orcamento_mes(mes: str) -> dict:
    """Devolve o estado do orçamento para o mês dado (ex: '2026-03')."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM orcamento WHERE mes = ?", (mes,)).fetchone()
    if not row:
        conn.execute("INSERT INTO orcamento (mes, total, gasto) VALUES (?, 1000.0, 0.0)", (mes,))
        conn.commit()
        row = conn.execute("SELECT * FROM orcamento WHERE mes = ?", (mes,)).fetchone()
    gastos = conn.execute("SELECT * FROM gastos WHERE mes = ? ORDER BY data DESC", (mes,)).fetchall()
    conn.close()
    d = dict(row)
    d['gastos_lista'] = [dict(g) for g in gastos]
    d['restante'] = d['total'] - d['gasto']
    return d


def registar_gasto(mes: str, valor: float, descricao: str = "") -> dict:
    """Regista um gasto e atualiza o total."""
    conn = get_connection()
    # Garante que o mês existe
    if not conn.execute("SELECT id FROM orcamento WHERE mes = ?", (mes,)).fetchone():
        conn.execute("INSERT INTO orcamento (mes, total, gasto) VALUES (?, 1000.0, 0.0)", (mes,))
    conn.execute("INSERT INTO gastos (mes, valor, descricao) VALUES (?, ?, ?)", (mes, valor, descricao))
    conn.execute("UPDATE orcamento SET gasto = gasto + ?, atualizado = datetime('now') WHERE mes = ?", (valor, mes))
    conn.commit()
    conn.close()
    return obter_orcamento_mes(mes)


def desfazer_ultimo_gasto(mes: str) -> dict:
    """Remove o último gasto registado."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM gastos WHERE mes = ? ORDER BY data DESC LIMIT 1", (mes,)).fetchone()
    if row:
        conn.execute("DELETE FROM gastos WHERE id = ?", (row['id'],))
        conn.execute("UPDATE orcamento SET gasto = gasto - ? WHERE mes = ?", (row['valor'], mes))
        conn.commit()
    conn.close()
    return obter_orcamento_mes(mes)
