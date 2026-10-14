import pytest

from app.domain import LivroInvalidoError
from app.repository import InMemoryLivroRepository
from app.service import BibliotecaService
from app.validators import normalizar_titulo, validar_isbn10


# ----------------------------------------------------------------------
# 1. Teste Parametrizado: Validação de ISBN-10 (Limites e Formatos)
# ----------------------------------------------------------------------
@pytest.mark.parametrize(
    "isbn, esperado",
    [
        ("1234567890", True),  # Válido: exatamente 10 dígitos numéricos
        ("1-234-56789-0", True),  # Válido: 10 dígitos ignorando traços
        ("123456789", False),  # Inválido: 9 dígitos (abaixo do limite)
        ("12345678901", False),  # Inválido: 11 dígitos (acima do limite)
        ("abcdefghij", False),  # Inválido: contêm caracteres alfabéticos
        ("", False),  # Inválido: string vazia
        (None, False),  # Inválido: valor nulo
    ],
)
def test_validar_isbn10_parametrizado(isbn, esperado):
    assert validar_isbn10(isbn) is esperado


# ----------------------------------------------------------------------
# 2. Teste Parametrizado: Classes de Equivalência de Exemplares
# ----------------------------------------------------------------------
@pytest.mark.parametrize(
    "exemplares, eh_valido",
    [
        (-1, False),  # Inválida (Valor negativo)
        (0, False),  # Inválida (Valor-limite)
        (1, True),  # Válida (Valor-limite mínimo permitido)
        (2, True),  # Válida (Valor nominal)
        (100, True),  # Válida (Caso geral)
    ],
)
def test_cadastro_exemplares_parametrizado(exemplares, eh_valido):
    # Arrange
    repo = InMemoryLivroRepository()
    service = BibliotecaService(repo)

    # Act & Assert
    if eh_valido:
        livro = service.cadastrar_livro(
            "1234567890", "Clean Code", "Robert C. Martin", exemplares
        )
        assert livro.exemplares == exemplares
    else:
        with pytest.raises(LivroInvalidoError):
            service.cadastrar_livro(
                "1234567890", "Clean Code", "Robert C. Martin", exemplares
            )


# ----------------------------------------------------------------------
# 3. Teste Parametrizado: Normalização e Validação de Título
# ----------------------------------------------------------------------
@pytest.mark.parametrize(
    "entrada, esperado",
    [
        (" Clean Code ", "Clean Code"),  # Remove espaços das pontas
        ("Design   Patterns", "Design Patterns"),  # Reduz múltiplos espaços internos
        ("Refatoração", "Refatoração"),  # Título sem espaços extras permanece igual
    ],
)
def test_normalizar_titulo_valido(entrada, esperado):
    assert normalizar_titulo(entrada) == esperado


def test_normalizar_titulo_vazio_lança_excecao():
    with pytest.raises(ValueError, match="título obrigatório"):
        normalizar_titulo(" ")
