from unittest.mock import Mock

import pytest

from app.domain import Livro
from app.service import BibliotecaService


def test_cadastrar_e_consultar_livro_com_fixture(servico_biblioteca):
    # Act (O Arrange foi feito automaticamente pela fixture servico_biblioteca)
    livro_cadastrado = servico_biblioteca.cadastrar_livro(
        isbn="1234567890",
        titulo=" Testes de Software ",
        autor="Maurício Aniche",
        exemplares=3,
    )
    livro_consultado = servico_biblioteca.consultar_livro_por_isbn("1234567890")

    # Assert
    assert livro_cadastrado.titulo == "Testes de Software"
    assert livro_consultado is not None
    assert livro_consultado.exemplares == 3


def test_verificar_disponibilidade_com_fixture(servico_com_livro_cadastrado):
    # Act (O livro 'Clean Code' com 2 exemplares já foi cadastrado pela fixture)
    quantidade = servico_com_livro_cadastrado.verificar_disponibilidade("1234567890")

    # Assert
    assert quantidade == 2


def test_emprestar_livro_reduz_exemplares_com_fixture(
    servico_com_livro_cadastrado,
):
    # Act
    livro_atualizado = servico_com_livro_cadastrado.emprestar_livro("1234567890")

    # Assert
    assert livro_atualizado.exemplares == 1


def test_devolver_livro_incrementa_exemplares_com_fixture(
    servico_com_livro_cadastrado,
):
    # Arrange complementar
    servico_com_livro_cadastrado.emprestar_livro("1234567890")

    # Act
    livro_devolvido = servico_com_livro_cadastrado.devolver_livro("1234567890")

    # Assert
    assert livro_devolvido.exemplares == 2


# ----------------------------------------------------------------------
# QUESTÃO 7: Teste Unitário Isolado com Mock (Verificação de Chamadas)
# ----------------------------------------------------------------------


def test_cadastrar_livro_com_mock_verifica_chamada_de_salvar():
    # Arrange (Injeção de dependência simulada)
    repo_mock = Mock()
    repo_mock.buscar_por_isbn.return_value = (
        None  # Configura return_value (simula livro inexistente)
    )
    service = BibliotecaService(repo_mock)

    # Act
    livro = service.cadastrar_livro(
        isbn="1234567890",
        titulo="Código Limpo",
        autor="Robert C. Martin",
        exemplares=3,
    )

    # Assert
    assert livro.titulo == "Código Limpo"

    # Verificação de colaboração (o serviço chamou os métodos do repositório corretamente?)
    repo_mock.buscar_por_isbn.assert_called_once_with("1234567890")
    repo_mock.salvar.assert_called_once()


# ----------------------------------------------------------------------
# QUESTÃO 8: Simulação de Sucesso e Falha do Repositório com side_effect
# ----------------------------------------------------------------------


def test_comportamentos_com_side_effect_sucesso_e_falha():
    # Arrange
    repo_mock = Mock()
    service = BibliotecaService(repo_mock)

    # 1. Cenário Normal: side_effect com retornos sequenciais
    livro_falso = Livro("1234567890", "Refatoração", "Martin Fowler", 2)
    repo_mock.buscar_por_isbn.side_effect = [None, livro_falso]

    # Primeira chamada (cadastro): buscar_por_isbn retorna None -> cadastro aprovado
    cadastrado = service.cadastrar_livro("1234567890", "Refatoração", "Fowler", 2)
    assert cadastrado.isbn == "1234567890"

    # Segunda chamada (consulta): buscar_por_isbn retorna o objeto livro_falso
    consultado = service.consultar_livro_por_isbn("1234567890")
    assert consultado.titulo == "Refatoração"

    # 2. Cenário de Falha: side_effect lançando exceção simulada no repositório
    repo_mock.buscar_por_isbn.side_effect = RuntimeError(
        "Falha de conexão com o banco de dados"
    )

    # Act & Assert: Verifica se a falha de infraestrutura é propagada
    with pytest.raises(RuntimeError, match="Falha de conexão com o banco de dados"):
        service.consultar_livro_por_isbn("1234567890")
