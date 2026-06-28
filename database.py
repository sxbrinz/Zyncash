"""
database.py
------------
Responsável por toda a comunicação com o banco de dados SQLite.
Aqui ficam: criação das tabelas, cadastro de usuário, login,
operações de inserir/listar/editar/excluir lançamentos financeiros,
e o registro de sugestões enviadas pelos usuários.
"""

import sqlite3
import hashlib
from datetime import datetime

DB_NAME = "zyncash.db"


def conectar():
    """Abre uma conexão com o banco de dados SQLite."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # permite acessar colunas pelo nome
    return conn


def criar_tabelas():
    """Cria as tabelas do banco caso ainda não existam."""
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha_hash TEXT NOT NULL,
            criado_em TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lancamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            data TEXT NOT NULL,
            descricao TEXT NOT NULL,
            categoria TEXT NOT NULL,
            tipo TEXT NOT NULL CHECK (tipo IN ('entrada', 'saida')),
            valor REAL NOT NULL,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sugestoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER,
            usuario_nome TEXT,
            mensagem TEXT NOT NULL,
            criado_em TEXT NOT NULL,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
    """)

    conn.commit()
    conn.close()


def hash_senha(senha: str) -> str:
    """Gera um hash seguro (SHA-256) da senha. Nunca guardamos senha em texto puro."""
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()


def criar_usuario(nome: str, email: str, senha: str) -> tuple[bool, str]:
    """Cadastra um novo usuário. Retorna (sucesso, mensagem)."""
    conn = conectar()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO usuarios (nome, email, senha_hash, criado_em) VALUES (?, ?, ?, ?)",
            (nome, email.lower().strip(), hash_senha(senha), datetime.now().isoformat()),
        )
        conn.commit()
        return True, "Cadastro realizado com sucesso!"
    except sqlite3.IntegrityError:
        return False, "Esse e-mail já está cadastrado."
    finally:
        conn.close()


def autenticar_usuario(email: str, senha: str):
    """Verifica se email/senha correspondem a um usuário cadastrado."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM usuarios WHERE email = ? AND senha_hash = ?",
        (email.lower().strip(), hash_senha(senha)),
    )
    usuario = cursor.fetchone()
    conn.close()
    return usuario


def inserir_lancamento(usuario_id: int, data: str, descricao: str, categoria: str, tipo: str, valor: float):
    """Insere um novo lançamento (entrada ou saída) para o usuário."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO lancamentos (usuario_id, data, descricao, categoria, tipo, valor)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (usuario_id, data, descricao, categoria, tipo, abs(valor)),
    )
    conn.commit()
    conn.close()


def atualizar_lancamento(lancamento_id: int, usuario_id: int, data: str, descricao: str,
                          categoria: str, tipo: str, valor: float):
    """Atualiza um lançamento já existente, garantindo que pertence ao usuário."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """UPDATE lancamentos
           SET data = ?, descricao = ?, categoria = ?, tipo = ?, valor = ?
           WHERE id = ? AND usuario_id = ?""",
        (data, descricao, categoria, tipo, abs(valor), lancamento_id, usuario_id),
    )
    conn.commit()
    conn.close()


def listar_lancamentos(usuario_id: int):
    """Retorna todos os lançamentos de um usuário, do mais recente para o mais antigo."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM lancamentos WHERE usuario_id = ? ORDER BY data DESC, id DESC",
        (usuario_id,),
    )
    resultado = cursor.fetchall()
    conn.close()
    return resultado


def buscar_lancamento(lancamento_id: int, usuario_id: int):
    """Busca um único lançamento pelo id, garantindo que pertence ao usuário."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM lancamentos WHERE id = ? AND usuario_id = ?",
        (lancamento_id, usuario_id),
    )
    resultado = cursor.fetchone()
    conn.close()
    return resultado


def excluir_lancamento(lancamento_id: int, usuario_id: int):
    """Exclui um lançamento, garantindo que pertence ao usuário que está pedindo a exclusão."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM lancamentos WHERE id = ? AND usuario_id = ?",
        (lancamento_id, usuario_id),
    )
    conn.commit()
    conn.close()


def salvar_sugestao(usuario_id: int, usuario_nome: str, mensagem: str):
    """Salva uma sugestão enviada por um usuário, para consulta posterior pela administradora."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO sugestoes (usuario_id, usuario_nome, mensagem, criado_em)
           VALUES (?, ?, ?, ?)""",
        (usuario_id, usuario_nome, mensagem, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def listar_sugestoes():
    """Retorna todas as sugestões recebidas, da mais recente para a mais antiga."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sugestoes ORDER BY criado_em DESC")
    resultado = cursor.fetchall()
    conn.close()
    return resultado
