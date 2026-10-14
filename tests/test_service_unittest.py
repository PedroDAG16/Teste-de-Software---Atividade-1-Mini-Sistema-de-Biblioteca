import unittest

from app.domain import Livro, LivroDuplicadoError, LivroInvalidoError
from app.repository import InMemoryLivroRepository
from app.service import BibliotecaService


class TestBibliotecaServiceUnittest(unittest.TestCase):
    def setUp(self):
        """Arrange comum: Executado antes de CADA teste para garantir isolamento."""
        self.repo = InMemoryLivroRepository()
        self.service = BibliotecaService(self.repo)

    def test_criacao_e_atributos_do_livro(self):
        # Act
        livro = Livro(
            isbn="1234567890",
            titulo="Engenharia de Software",
            autor="Ian Sommerville",
            exemplares=5,
        )

        # Assert
        self.assertEqual(livro.isbn, "1234567890")
        self.assertEqual(livro.titulo, "Engenharia de Software")
        self.assertEqual(livro.autor, "Ian Sommerville")
        self.assertEqual(livro.exemplares, 5)

    def test_cadastrar_e_consultar_livro(self):
        # Act
        livro_cadastrado = self.service.cadastrar_livro(
            isbn="1234567890",
            titulo=" Testes de Software ",
            autor="Maurício Aniche",
            exemplares=3,
        )
        livro_consultado = self.service.consultar_livro_por_isbn("1234567890")

        # Assert
        self.assertEqual(livro_cadastrado.titulo, "Testes de Software")
        self.assertIsNotNone(livro_consultado)
        self.assertEqual(livro_consultado.isbn, "1234567890")
        self.assertEqual(livro_consultado.exemplares, 3)

    def test_verificar_disponibilidade(self):
        # Arrange específico
        self.service.cadastrar_livro("1234567890", "Clean Code", "Robert C. Martin", 4)

        # Act
        quantidade = self.service.verificar_disponibilidade("1234567890")

        # Assert
        self.assertEqual(quantidade, 4)

    def test_emprestar_livro_reduz_exemplares(self):
        # Arrange específico
        self.service.cadastrar_livro("1234567890", "Refatoração", "Martin Fowler", 2)

        # Act
        livro_atualizado = self.service.emprestar_livro("1234567890", leitor="Carlos")

        # Assert
        self.assertEqual(livro_atualizado.exemplares, 1)
        self.assertEqual(self.service.verificar_disponibilidade("1234567890"), 1)

    def test_devolver_livro_incrementa_exemplares(self):
        # Arrange específico
        self.service.cadastrar_livro("1234567890", "Design Patterns", "GoF", 1)
        self.service.emprestar_livro("1234567890")

        # Act
        livro_devolvido = self.service.devolver_livro("1234567890")

        # Assert
        self.assertEqual(livro_devolvido.exemplares, 1)
        self.assertEqual(self.service.verificar_disponibilidade("1234567890"), 1)

    def test_cadastrar_livro_duplicado_lança_excecao(self):
        # Arrange
        self.service.cadastrar_livro("1234567890", "Clean Code", "Robert C. Martin", 2)

        # Act & Assert
        with self.assertRaises(LivroDuplicadoError):
            self.service.cadastrar_livro("1234567890", "Outro Título", "Autor", 1)

    def test_emprestar_livro_sem_exemplares_lança_excecao(self):
        # Arrange
        self.service.cadastrar_livro("1234567890", "DDD", "Eric Evans", 1)
        self.service.emprestar_livro("1234567890")

        # Act & Assert
        with self.assertRaises(LivroInvalidoError):
            self.service.emprestar_livro("1234567890")


if __name__ == "__main__":
    unittest.main()
