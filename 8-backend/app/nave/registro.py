"""SQLite operacional da nave. Só inclusão: nenhuma função aqui altera ou apaga.

A trilha de auditoria encadeia cada registro no hash do anterior (ADR-008).
"""
import hashlib
import json
import sqlite3
import threading
from datetime import datetime, timezone

from ..config import BANCO

_ESQUEMA = """
CREATE TABLE IF NOT EXISTS leituras (id INTEGER PRIMARY KEY, tripulante_id TEXT, dispositivo_id TEXT, canal TEXT,
  valor REAL, unidade TEXT, qualidade_sinal TEXT, gerada_em TEXT, recebida_em TEXT);
CREATE TABLE IF NOT EXISTS eventos (seq INTEGER PRIMARY KEY, evento_id TEXT, tipo TEXT, tripulante_id TEXT,
  estado TEXT, quando TEXT, corpo TEXT);
CREATE TABLE IF NOT EXISTS sugestoes (id INTEGER PRIMARY KEY, evento_id TEXT, texto TEXT, evidencias TEXT,
  confianca REAL, alternativa TEXT, versao_modelo TEXT, criada_em TEXT);
CREATE TABLE IF NOT EXISTS decisoes (id INTEGER PRIMARY KEY, evento_id TEXT, humano_id TEXT, acao TEXT, dose TEXT,
  assinatura TEXT, decidida_em TEXT, detalhe TEXT);
CREATE TABLE IF NOT EXISTS consentimentos (id INTEGER PRIMARY KEY, tripulante_id TEXT, tipo_dado TEXT,
  destinatario TEXT, acao TEXT, quando TEXT);
CREATE TABLE IF NOT EXISTS pacotes (seq INTEGER PRIMARY KEY, pacote_id TEXT, direcao TEXT, prioridade INTEGER,
  estado TEXT, rotulo TEXT, quando TEXT);
CREATE TABLE IF NOT EXISTS rotulos (id INTEGER PRIMARY KEY, peca TEXT, tripulante_id TEXT, rotulo TEXT,
  humano_id TEXT, origem TEXT, versao_modelo TEXT, dados TEXT, criado_em TEXT);
CREATE TABLE IF NOT EXISTS cosmo_trilha (seq INTEGER PRIMARY KEY, trilha_id TEXT, superficie TEXT, origem TEXT,
  evento_id TEXT, quando TEXT, corpo TEXT);
CREATE TABLE IF NOT EXISTS auditoria (seq INTEGER PRIMARY KEY, entidade TEXT, entidade_id TEXT, de_estado TEXT,
  para_estado TEXT, ator TEXT, quando TEXT, detalhe TEXT, hash_anterior TEXT, hash TEXT);
"""

_trava = threading.Lock()
_con = None


def agora_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def conectar(caminho=None, limpar_operacional=False):
    """Abre o banco. Os rótulos humanos e a auditoria ficam entre uma execução e
    outra; leituras, eventos e pacotes da sessão anterior podem ser descartados."""
    global _con
    _con = sqlite3.connect(str(caminho or BANCO), check_same_thread=False)
    _con.executescript(_ESQUEMA)
    if limpar_operacional:
        for t in ("leituras", "eventos", "sugestoes", "decisoes", "consentimentos", "pacotes"):
            _con.execute(f"DELETE FROM {t}")  # nova sessão de simulação; a auditoria fica
        _con.commit()
    return _con


def incluir(tabela: str, **campos) -> int:
    with _trava:
        cols = ", ".join(campos)
        cur = _con.execute(f"INSERT INTO {tabela} ({cols}) VALUES ({', '.join('?' * len(campos))})",
                           [json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v for v in campos.values()])
        _con.commit()
        return cur.lastrowid


def incluir_varias(tabela: str, colunas: list, linhas: list):
    with _trava:
        _con.executemany(f"INSERT INTO {tabela} ({', '.join(colunas)}) VALUES ({', '.join('?' * len(colunas))})", linhas)
        _con.commit()


def listar(sql: str, params=()) -> list:
    with _trava:
        cur = _con.execute(sql, params)
        nomes = [c[0] for c in cur.description]
        return [dict(zip(nomes, l)) for l in cur.fetchall()]


# ------------------------------------------------------------------ auditoria
def _hash(anterior: str, corpo: dict) -> str:
    return hashlib.sha256((anterior + json.dumps(corpo, sort_keys=True, ensure_ascii=False)).encode()).hexdigest()


def auditar(entidade: str, entidade_id: str, de_estado, para_estado, ator: str, detalhe: dict | None = None, quando=None):
    """Inclui um registro com o hash do anterior. `ator` é sempre nomeado:
    um humano, a Cosmo (sugestão) ou o motor (regra determinística)."""
    with _trava:
        ult = _con.execute("SELECT hash FROM auditoria ORDER BY seq DESC LIMIT 1").fetchone()
        anterior = ult[0] if ult else "genesis"
        corpo = dict(entidade=entidade, entidade_id=str(entidade_id), de_estado=de_estado, para_estado=para_estado,
                     ator=ator, quando=quando or agora_iso(), detalhe=detalhe or {})
        h = _hash(anterior, corpo)
        _con.execute("INSERT INTO auditoria (entidade, entidade_id, de_estado, para_estado, ator, quando, detalhe, hash_anterior, hash)"
                     " VALUES (?,?,?,?,?,?,?,?,?)",
                     (corpo["entidade"], corpo["entidade_id"], de_estado, para_estado, ator, corpo["quando"],
                      json.dumps(corpo["detalhe"], sort_keys=True, ensure_ascii=False), anterior, h))
        _con.commit()
        return h


def verificar_cadeia() -> dict:
    """Recalcula a cadeia inteira. Qualquer registro alterado quebra o hash dos seguintes."""
    anterior, n = "genesis", 0
    for r in listar("SELECT * FROM auditoria ORDER BY seq"):
        corpo = dict(entidade=r["entidade"], entidade_id=r["entidade_id"], de_estado=r["de_estado"],
                     para_estado=r["para_estado"], ator=r["ator"], quando=r["quando"], detalhe=json.loads(r["detalhe"]))
        if r["hash_anterior"] != anterior or r["hash"] != _hash(anterior, corpo):
            return dict(integra=False, registros=n, quebrou_em=r["seq"])
        anterior, n = r["hash"], n + 1
    return dict(integra=True, registros=n, ultimo_hash=anterior)
