from app.domain import Livro, LivroDuplicadoError, LivroInvalidoError
from app.validators import normalizar_titulo, validar_isbn10


class BibliotecaService:
    """Serviço responsável pelas operações e regras de negócio da biblioteca."""

    def __init__(self, repositorio):
        self.repositorio = repositorio

    def cadastrar_livro(
        self, isbn: str, titulo: str, autor: str, exemplares: int
    ) -> Livro:
        if not validar_isbn10(isbn):
            raise LivroInvalidoError("ISBN inválido")

        try:
            titulo_normalizado = normalizar_titulo(titulo)
        except ValueError as e:
            raise LivroInvalidoError(str(e)) from e

        if not autor or not autor.strip():
            raise LivroInvalidoError("autor obrigatório")

        if exemplares <= 0:
            raise LivroInvalidoError("exemplares deve ser > 0")

        if self.repositorio.buscar_por_isbn(isbn) is not None:
            raise LivroDuplicadoError("Livro já cadastrado")

        livro = Livro(
            isbn=isbn,
            titulo=titulo_normalizado,
            autor=autor.strip(),
            exemplares=exemplares,
        )
        self.repositorio.salvar(livro)
        return livro

    def consultar_livro_por_isbn(self, isbn: str) -> Livro | None:
        return self.repositorio.buscar_por_isbn(isbn)

    def verificar_disponibilidade(self, isbn: str) -> int:
        livro = self.consultar_livro_por_isbn(isbn)
        if livro is None:
            raise LivroInvalidoError("Livro não encontrado")
        return livro.exemplares

    def emprestar_livro(self, isbn: str, leitor: str = "") -> Livro:
        livro = self.consultar_livro_por_isbn(isbn)
        if livro is None:
            raise LivroInvalidoError("Livro não encontrado")

        if livro.exemplares <= 0:
            raise LivroInvalidoError("Sem exemplares disponíveis para empréstimo")

        livro.exemplares -= 1
        self.repositorio.salvar(livro)
        return livro

    def devolver_livro(self, isbn: str) -> Livro:
        livro = self.consultar_livro_por_isbn(isbn)
        if livro is None:
            raise LivroInvalidoError("Livro não encontrado")

        livro.exemplares += 1
        self.repositorio.salvar(livro)
        return livro
