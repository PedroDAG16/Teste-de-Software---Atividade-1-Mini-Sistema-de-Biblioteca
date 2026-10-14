from app.domain import Livro


def test_criacao_e_atributos_do_livro():
    # Arrange (Preparação dos dados)
    isbn = "1234567890"
    titulo = "Engenharia de Software"
    autor = "Ian Sommerville"
    exemplares = 5

    # Act (Criação de Instância de Domínio)
    livro = Livro(isbn=isbn, titulo=titulo, autor=autor, exemplares=exemplares)

    # Assert (Verificação dos atributos)
    assert livro.isbn == "1234567890"
    assert livro.titulo == "Engenharia de Software"
    assert livro.autor == "Ian Sommerville"
    assert livro.exemplares == 5
