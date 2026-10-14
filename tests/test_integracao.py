from app.repository import InMemoryLivroRepository
from app.service import BibliotecaService


# ----------------------------------------------------------------------
# QUESTÃO 9: Primeiro Teste de Integração (Fluxo de Empréstimo sem Mocks)
# ----------------------------------------------------------------------
def test_integracao_fluxo_emprestimo():
    # Arrange: Instanciação dos componentes reais da aplicação (sem mocks)
    repo = InMemoryLivroRepository()
    service = BibliotecaService(repo)

    # Act 1: Cadastrar o livro
    service.cadastrar_livro(
        isbn="1234567890",
        titulo="Engenharia de Software",
        autor="Ian Sommerville",
        exemplares=3,
    )

    # Act 2: Pesquisar o livro cadastrado e confirmar a disponibilidade inicial
    livro_consultado = service.consultar_livro_por_isbn("1234567890")
    assert livro_consultado is not None
    assert service.verificar_disponibilidade("1234567890") == 3

    # Act 3: Realizar o empréstimo de 1 exemplar
    service.emprestar_livro("1234567890", leitor="Maria")

    # Act 4 & Assert: Consultar novamente e confirmar a redução no repositório real
    livro_pos_emprestimo = service.consultar_livro_por_isbn("1234567890")
    assert livro_pos_emprestimo.exemplares == 2
    assert service.verificar_disponibilidade("1234567890") == 2


# ----------------------------------------------------------------------
# QUESTÃO 10: Integração do Fluxo Completo (Cadastro -> Empréstimo -> Devolução)
# ----------------------------------------------------------------------
def test_integracao_fluxo_completo_cadastro_emprestimo_devolucao():
    # Arrange: Componentes reais sem substituição por dublês
    repo = InMemoryLivroRepository()
    service = BibliotecaService(repo)

    # 1. Cadastrar livro com 1 exemplar
    service.cadastrar_livro(
        isbn="1234567890",
        titulo="Arquitetura Limpa",
        autor="Robert C. Martin",
        exemplares=1,
    )

    # 2. Consultar livro
    livro = service.consultar_livro_por_isbn("1234567890")
    assert livro is not None
    assert livro.exemplares == 1

    # 3. Realizar empréstimo (o estoque deve ir para 0)
    service.emprestar_livro("1234567890", leitor="João")

    # 4. Consultar novamente para confirmar que não há mais exemplares disponíveis
    assert service.verificar_disponibilidade("1234567890") == 0

    # 5. Realizar a devolução
    service.devolver_livro("1234567890")

    # 6. Consultar novamente e verificar o restabelecimento do estoque
    livro_final = service.consultar_livro_por_isbn("1234567890")
    assert livro_final.exemplares == 1
    assert service.verificar_disponibilidade("1234567890") == 1
