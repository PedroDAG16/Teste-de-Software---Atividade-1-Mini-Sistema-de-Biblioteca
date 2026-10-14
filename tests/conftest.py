import sqlite3

import pytest

from app.repository import InMemoryLivroRepository, SQLiteLivroRepository
from app.service import BibliotecaService


@pytest.fixture
def repositorio_memoria():
    return InMemoryLivroRepository()


@pytest.fixture
def servico_biblioteca(repositorio_memoria):
    return BibliotecaService(repositorio_memoria)


@pytest.fixture
def servico_com_livro_cadastrado(servico_biblioteca):
    servico_biblioteca.cadastrar_livro(
        isbn="1234567890",
        titulo="Clean Code",
        autor="Robert C. Martin",
        exemplares=2,
    )
    return servico_biblioteca


# ----------------------------------------------------------------------
# FIXTURE DA QUESTÃO 12: Fixture de Integração com SQLite e Teardown
# ----------------------------------------------------------------------
@pytest.fixture
def servico_sqlite():
    # SETUP: Inicializa a conexão SQLite em memória RAM e os componentes reais
    conexao = sqlite3.connect(":memory:")
    repo = SQLiteLivroRepository(conexao)
    servico = BibliotecaService(repo)

    # EXECUÇÃO: Entrega o serviço pronto para o teste executar
    yield servico

    # TEARDOWN: Executado automaticamente após o término do teste para fechar a conexão
    conexao.close()
