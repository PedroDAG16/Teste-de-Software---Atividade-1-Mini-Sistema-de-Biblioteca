import sqlite3

from app.domain import Livro


class InMemoryLivroRepository:
    """Repositório em memória para armazenamento e consulta de livros."""

    def __init__(self):
        self._livros: dict[str, Livro] = {}

    def buscar_por_isbn(self, isbn: str) -> Livro | None:
        livro = self._livros.get(isbn)
        if livro is None:
            return None
        return Livro(
            isbn=livro.isbn,
            titulo=livro.titulo,
            autor=livro.autor,
            exemplares=livro.exemplares,
        )

    def salvar(self, livro: Livro) -> None:
        self._livros[livro.isbn] = Livro(
            isbn=livro.isbn,
            titulo=livro.titulo,
            autor=livro.autor,
            exemplares=livro.exemplares,
        )


class SQLiteLivroRepository:
    """Repositório real utilizando banco de dados SQLite."""

    def __init__(self, conexao: sqlite3.Connection):
        self.conexao = conexao
        self._criar_tabela()

    def _criar_tabela(self) -> None:
        with self.conexao:
            self.conexao.execute("""
                CREATE TABLE IF NOT EXISTS livros (
                    isbn TEXT PRIMARY KEY,
                    titulo TEXT NOT NULL,
                    autor TEXT NOT NULL,
                    exemplares INTEGER NOT NULL
                )
            """)

    def buscar_por_isbn(self, isbn: str) -> Livro | None:
        cursor = self.conexao.cursor()
        cursor.execute(
            "SELECT isbn, titulo, autor, exemplares FROM livros WHERE isbn = ?",
            (isbn,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return Livro(
            isbn=row,
            titulo=row,
            autor=row,
            exemplares=row,
        )

    def salvar(self, livro: Livro) -> None:
        with self.conexao:
            self.conexao.execute(
                """
                INSERT INTO livros (isbn, titulo, autor, exemplares)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(isbn) DO UPDATE SET
                    titulo = excluded.titulo,
                    autor = excluded.autor,
                    exemplares = excluded.exemplares
                """,
                (livro.isbn, livro.titulo, livro.autor, livro.exemplares),
            )
