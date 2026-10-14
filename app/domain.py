from dataclasses import dataclass


class LivroInvalidoError(ValueError):
    """Exceção lançada quando os dados de um livro violam as regras do sistema."""


class LivroDuplicadoError(ValueError):
    """Exceção lançada ao tentar cadastrar um livro com ISBN já existente."""


@dataclass
class Livro:
    isbn: str
    titulo: str
    autor: str
    exemplares: int
