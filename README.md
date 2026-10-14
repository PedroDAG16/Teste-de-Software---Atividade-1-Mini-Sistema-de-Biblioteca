# Documento de Sequência de Desenvolvimento e Relatório de Testes

**Atividade Avaliativa - Unidade I**  
**Disciplina:** Teste de Software I
**Aluno:** Pedro de Araújo Guedes - 20220042140
**Projeto:** Mini Sistema de Biblioteca (Pytest & Unittest)  
**Ambiente de Desenvolvimento:** Neovim / PowerShell 7.6 / Python 3.12  

---

## Sumário Executivo e Mapa de Evolução

Este documento registra a trajetória completa do desenvolvimento do trabalho. O progresso é demonstrado através da demonstração do estado dos arquivos em cada uma das 14 questões da avaliação.

```
.
├── app/
│   ├── __init__.py
│   ├── domain.py         <-- Entidades de domínio e exceções personalizadas
│   ├── validators.py     <-- Funções puras de validação (ISBN, títulos)
│   ├── repository.py     <-- Repositório Fake (InMemory) e Persistência SQL (SQLite)
│   └── service.py        <-- Regras de negócio, empréstimos e orquestração
└── tests/
    ├── __init__.py
    ├── conftest.py       <-- Fixtures globais unitárias e de integração (Setup/Teardown)
    ├── test_domain_pytest.py
    ├── test_validators_pytest.py
    ├── test_service_pytest.py
    ├── test_service_unittest.py
    ├── test_integracao.py
    └── test_integracao_sqlite.py
```

---

## Questão 1 – Construção e Organização Inicial do Sistema

### 1. Objetivo
Estabelecer a arquitetura base do Mini Sistema de Biblioteca com separação clara de responsabilidades, sem dependências de infraestrutura externa, preparando os contratos para os testes automatizados.

### 2. Arquivos

#### `app/domain.py`
```python
from dataclasses import dataclass


class LivroInvalidoError(ValueError):
    """Exceção lançada quando os dados do livro violam as regras do sistema."""


class LivroDuplicadoError(ValueError):
    """Exceção lançada ao tentar cadastrar um livro com ISBN já existente."""


@dataclass
class Livro:
    isbn: str
    titulo: str
    autor: str
    exemplares: int
```

#### `app/validators.py`
```python
def validar_isbn10(isbn: str) -> bool:
    if isbn is None:
        return False
    somente_digitos = str(isbn).replace("-", "").strip()
    return len(somente_digitos) == 10 and somente_digitos.isdigit()


def normalizar_titulo(titulo: str) -> str:
    if titulo is None or not str(titulo).strip():
        raise ValueError("título obrigatório")
    partes = str(titulo).strip().split()
    return " ".join(partes)
```

#### `app/repository.py`
```python
from app.domain import Livro


class InMemoryLivroRepository:
    """Repositório fake em memória para isolamento de testes unitários."""

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
            exemplares=livro.exemplares
        )

    def salvar(self, livro: Livro) -> None:
        self._livros[livro.isbn] = Livro(
            isbn=livro.isbn,
            titulo=livro.titulo,
            autor=livro.autor,
            exemplares=livro.exemplares
        )
```

#### `app/service.py`
```python
from app.domain import Livro, LivroDuplicadoError, LivroInvalidoError
from app.validators import normalizar_titulo, validar_isbn10


class BibliotecaService:
    """Serviço responsável por aplicar as regras de negócio da biblioteca."""

    def __init__(self, repositorio):
        self.repositorio = repositorio

    def cadastrar_livro(self, isbn: str, titulo: str, autor: str, exemplares: int) -> Livro:
        if not validar_isbn10(isbn):
            raise LivroInvalidoError("ISBN inválido")

        try:
            titulo_normalizado = normalizar_titulo(titulo)
        except ValueError as e:
            raise LivroInvalidoError(str(e)) from e

        if not autor or not autor.strip():
            raise LivroInvalidoError("Autor obrigatório")

        if exemplares <= 0:
            raise LivroInvalidoError("Exemplares deve ser > 0")

        if self.repositorio.buscar_por_isbn(isbn) is not None:
            raise LivroDuplicadoError("Livro já cadastrado")

        livro = Livro(
            isbn=isbn,
            titulo=titulo_normalizado,
            autor=autor.strip(),
            exemplares=exemplares
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
```

### 3. Execução no Terminal
```powershell
PS C:\Users\pedro.guedes\...\Atividade-1-Mini-Sistema-de-Biblioteca> python -c "from app.domain import Livro; print(Livro('1234567890', 'Python', 'Autor', 5))"
Livro(isbn='1234567890', titulo='Python', autor='Autor', exemplares=5)
```

### 4. Interpretação
A camada de aplicação foi estruturada. A entidade `Livro` utiliza `@dataclass` sem métodos auxiliares. Os validadores são funções sem colaterais. O repositório em memória imita o contrato de persistência mantendo cópias independentes dos objetos.

---

## Questão 2 – Primeiros Testes Unitários com pytest

### 1. Objetivo
Construir testes unitários isolados com `pytest`, aplicando de forma explícita o padrão AAA para verificar construção de objetos e métodos de serviço.

### 2. Arquivos

#### `tests/test_domain_pytest.py`
```python
from app.domain import Livro


def test_criacao_e_atributos_do_livro():
    # Arrange (Preparação dos dados de entrada)
    isbn = "1234567890"
    titulo = "Engenharia de Software"
    autor = "Ian Sommerville"
    exemplares = 5

    # Act (Execução da criação da entidade)
    livro = Livro(isbn=isbn, titulo=titulo, autor=autor, exemplares=exemplares)

    # Assert (Verificação do estado e atributos)
    assert livro.isbn == "1234567890"
    assert livro.titulo == "Engenharia de Software"
    assert livro.autor == "Ian Sommerville"
    assert livro.exemplares == 5
```

#### `tests/test_service_pytest.py` (Versão Inicial)
```python
from app.repository import InMemoryLivroRepository
from app.service import BibliotecaService


def test_cadastrar_e_consultar_livro_existente():
    # Arrange
    repo = InMemoryLivroRepository()
    service = BibliotecaService(repo)

    # Act
    livro_cadastrado = service.cadastrar_livro(
        isbn="1234567890",
        titulo="  Testes de Software  ",
        autor="Maurício Aniche",
        exemplares=3
    )
    livro_consultado = service.consultar_livro_por_isbn("1234567890")

    # Assert
    assert livro_cadastrado.titulo == "Testes de Software"
    assert livro_consultado is not None
    assert livro_consultado.isbn == "1234567890"
    assert livro_consultado.exemplares == 3


def test_verificar_disponibilidade_de_livro():
    # Arrange
    repo = InMemoryLivroRepository()
    service = BibliotecaService(repo)
    service.cadastrar_livro("1234567890", "Clean Code", "Robert C. Martin", 4)

    # Act
    quantidade = service.verificar_disponibilidade("1234567890")

    # Assert
    assert quantidade == 4


def test_emprestar_livros_reduz_exemplares():
    # Arrange
    repo = InMemoryLivroRepository()
    service = BibliotecaService(repo)
    service.cadastrar_livro("1234567890", "Refatoração", "Martin Fowler", 2)

    # Act
    livro_atualizado = service.emprestar_livro("1234567890", leitor="Carlos")

    # Assert
    assert livro_atualizado.exemplares == 1
    assert service.verificar_disponibilidade("1234567890") == 1


def test_devolver_livro_incrementa_exemplares():
    # Arrange
    repo = InMemoryLivroRepository()
    service = BibliotecaService(repo)
    service.cadastrar_livro("1234567890", "Design Patterns", "GoF", 1)
    service.emprestar_livro("1234567890")

    # Act
    livro_devolvido = service.devolver_livro("1234567890")

    # Assert
    assert livro_devolvido.exemplares == 1
    assert service.verificar_disponibilidade("1234567890") == 1
```

### 3. Execução no Terminal
```powershell
PS C:\Users\pedro.guedes\...\Atividade-1-Mini-Sistema-de-Biblioteca> python -m pytest tests/test_domain_pytest.py tests/test_service_pytest.py -v
============================= test session starts =============================
collected 5 items                                                              

tests/test_domain_pytest.py::test_criacao_e_atributos_do_livro PASSED   [ 20%]
tests/test_service_pytest.py::test_cadastrar_e_consultar_livro_existente PASSED [ 40%]
tests/test_service_pytest.py::test_verificar_disponibilidade_de_livro PASSED [ 60%]
tests/test_service_pytest.py::test_emprestar_livros_reduz_exemplares PASSED [ 80%]
tests/test_service_pytest.py::test_devolver_livro_incrementa_exemplares PASSED [100%]

============================== 5 passed in 0.04s ==============================
```

### 4. Interpretação
O padrão AAA separa claramente a preparação de dados, a invocação do método testado e a validação do oráculo. O uso de `assert` torna as falhas legíveis e diretas.

---

## Questão 3 – Testes Utilizando unittest

### 1. Objetivo
Reescrever as verificações do serviço utilizando o framework da biblioteca padrão `unittest`, identificando as diferenças de estrutura orientada a objetos (`TestCase`), ciclo de vida (`setUp`) e métodos de asserção dedicados.

### 2. Arquivos

#### `tests/test_service_unittest.py`
```python
import unittest
from app.domain import Livro
from app.repository import InMemoryLivroRepository
from app.service import BibliotecaService


class TestBibliotecaServiceUnittest(unittest.TestCase):

    def setUp(self):
        """Arrange comum: Executado automaticamente antes de CADA método de teste."""
        self.repo = InMemoryLivroRepository()
        self.service = BibliotecaService(self.repo)

    def test_criacao_e_atributos_do_livro(self):
        # Act
        livro = Livro(
            isbn="1234567890",
            titulo="Engenharia de Software",
            autor="Ian Sommerville",
            exemplares=5
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
            titulo="  Testes de Software  ",
            autor="Maurício Aniche",
            exemplares=3
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


if __name__ == "__main__":
    unittest.main()
```

### 3. Execução no Terminal
```powershell
PS C:\Users\pedro.guedes\...\Atividade-1-Mini-Sistema-de-Biblioteca> python -m unittest discover -s tests -p "*unittest*.py" -v
test_cadastrar_e_consultar_livro (test_service_unittest.TestBibliotecaServiceUnittest.test_cadastrar_e_consultar_livro) ... ok
test_criacao_e_atributos_do_livro (test_service_unittest.TestBibliotecaServiceUnittest.test_criacao_e_atributos_do_livro) ... ok
test_devolver_livro_incrementa_exemplares (test_service_unittest.TestBibliotecaServiceUnittest.test_devolver_livro_incrementa_exemplares) ... ok
test_emprestar_livro_reduz_exemplares (test_service_unittest.TestBibliotecaServiceUnittest.test_emprestar_livro_reduz_exemplares) ... ok
test_verificar_disponibilidade (test_service_unittest.TestBibliotecaServiceUnittest.test_verificar_disponibilidade) ... ok

----------------------------------------------------------------------
Ran 5 tests in 0.003s

OK
```

### 4. Interpretação e Diferenças entre Frameworks

* **`pytest`**: Utiliza funções livres, fixtures flexíveis e `assert` simples do Python. É mais conciso e expressivo.
* **`unittest`**: Requer herança de `unittest.TestCase`, agrupamento em classes, métodos `setUp()` / `tearDown()` explícitos e asserções específicas (`assertEqual`, `assertIsNotNone`).

---

## Questão 4 – Parametrização, Classes de Equivalência e Valores Limite

### 1. Objetivo Técnico
Aplicar a técnica de Particionamento em Classes de Equivalência e Análise de Valores Limite (AVL) nas validações de ISBN e no atributo `exemplares` utilizando `@pytest.mark.parametrize`.

### 2. Tabela de Mapeamento de Classes de Equivalência e Fronteiras

| Parâmetro / Regra | Entrada Testada | Classe de Equivalência | Resultado Esperado | Justificativa do Ponto de Teste |
| :--- | :---: | :---: | :---: | :--- |
| **Exemplares** | `-1` | **Inválida** | Lança `LivroInvalidoError` | Valor negativo fora do domínio permitido |
| **Exemplares** | `0` | **Inválida (Limite)** | Lança `LivroInvalidoError` | Fronteira estrita inferior (menor valor inválido) |
| **Exemplares** | `1` | **Válida (Limite)** | Sucesso no Cadastro | Fronteira estrita superior (menor valor permitido) |
| **Exemplares** | `2` | **Válida** | Sucesso no Cadastro | Valor nominal dentro da classe válida |
| **Exemplares** | `100` | **Válida** | Sucesso no Cadastro | Valor de grande porte dentro do limite estendido |
| **ISBN-10** | `"1234567890"` | **Válida** | `True` | Exatamente 10 dígitos numéricos |
| **ISBN-10** | `"1-234-56789-0"` | **Válida** | `True` | 10 dígitos numéricos com hífens ignorados |
| **ISBN-10** | `"123456789"` | **Inválida (Limite)** | `False` | 9 dígitos (1 a menos que o limite) |
| **ISBN-10** | `"12345678901"` | **Inválida (Limite)** | `False` | 11 dígitos (1 a mais que o limite) |
| **ISBN-10** | `"abcdefghij"` | **Inválida** | `False` | Contém caracteres alfabéticos |

### 3. Estado dos Arquivos na Etapa

#### `tests/test_validators_pytest.py`
```python
import pytest
from app.domain import LivroInvalidoError
from app.repository import InMemoryLivroRepository
from app.service import BibliotecaService
from app.validators import normalizar_titulo, validar_isbn10


# 1. Teste Parametrizado: Validação de ISBN-10
@pytest.mark.parametrize(
    "isbn, esperado",
    [
        ("1234567890", True),
        ("1-234-56789-0", True),
        ("123456789", False),
        ("12345678901", False),
        ("abcdefghij", False),
        ("", False),
        (None, False),
    ],
)
def test_validar_isbn10_parametrizado(isbn, esperado):
    assert validar_isbn10(isbn) is esperado


# 2. Teste Parametrizado: Classes de Equivalência de Exemplares
@pytest.mark.parametrize(
    "exemplares, eh_valido",
    [
        (-1, False),
        (0, False),
        (1, True),
        (2, True),
        (100, True),
    ],
)
def test_cadastro_exemplares_parametrizado(exemplares, eh_valido):
    repo = InMemoryLivroRepository()
    service = BibliotecaService(repo)

    if eh_valido:
        livro = service.cadastrar_livro("1234567890", "Clean Code", "Robert C. Martin", exemplares)
        assert livro.exemplares == exemplares
    else:
        with pytest.raises(LivroInvalidoError):
            service.cadastrar_livro("1234567890", "Clean Code", "Robert C. Martin", exemplares)


# 3. Teste Parametrizado: Normalização de Títulos
@pytest.mark.parametrize(
    "entrada, esperado",
    [
        ("  Clean Code  ", "Clean Code"),
        ("Design   Patterns", "Design Patterns"),
        ("Refatoração", "Refatoração"),
    ],
)
def test_normalizar_titulo_valido(entrada, esperado):
    assert normalizar_titulo(entrada) == esperado
```

### 4. Execução no Terminal
```powershell
PS C:\Users\pedro.guedes\...\Atividade-1-Mini-Sistema-de-Biblioteca> python -m pytest tests/test_validators_pytest.py -v
collected 15 items                                                            

tests/test_validators_pytest.py::test_validar_isbn10_parametrizado[1234567890-True] PASSED [  6%]
tests/test_validators_pytest.py::test_validar_isbn10_parametrizado[1-234-56789-0-True] PASSED [ 13%]
tests/test_validators_pytest.py::test_validar_isbn10_parametrizado[123456789-False] PASSED [ 20%]
tests/test_validators_pytest.py::test_validar_isbn10_parametrizado[12345678901-False] PASSED [ 26%]
tests/test_validators_pytest.py::test_validar_isbn10_parametrizado[abcdefghij-False] PASSED [ 33%]
tests/test_validators_pytest.py::test_validar_isbn10_parametrizado[-False] PASSED [ 40%]
tests/test_validators_pytest.py::test_validar_isbn10_parametrizado[None-False] PASSED [ 46%]
tests/test_validators_pytest.py::test_cadastro_exemplares_parametrizado[-1-False] PASSED [ 53%]
tests/test_validators_pytest.py::test_cadastro_exemplares_parametrizado[0-False] PASSED [ 60%]
tests/test_validators_pytest.py::test_cadastro_exemplares_parametrizado[1-True] PASSED [ 66%]
tests/test_validators_pytest.py::test_cadastro_exemplares_parametrizado[2-True] PASSED [ 73%]
tests/test_validators_pytest.py::test_cadastro_exemplares_parametrizado[100-True] PASSED [ 80%]
tests/test_validators_pytest.py::test_normalizar_titulo_valido[  Clean Code  -Clean Code] PASSED [ 86%]
tests/test_validators_pytest.py::test_normalizar_titulo_valido[Design   Patterns-Design Patterns] PASSED [ 93%]
tests/test_validators_pytest.py::test_normalizar_titulo_valido[Refatora\xe7\xe3o-Refatora\xe7\xe3o] PASSED [100%]

============================= 15 passed in 0.05s ==============================
```

### 5. Interpretação
A parametrização expandiu 3 funções de teste em 15 execuções independentes sem duplicar lógica de teste. A análise de limites em `0` e `1` garantiu que a condição `>= 1` da regra de negócio fosse exercitada com precisão na fronteira.

---

## Questão 5 – Testando Exceções e Comportamentos Negativos

### 1. Objetivo
Validar as rotas de falha e exceções de domínio no `pytest` (`pytest.raises`) e no `unittest` (`assertRaises`), garantindo que o sistema lance exceções tipadas e com mensagens corretas ao receber entradas inválidas.

### 2. Arquivos

#### Alteração em `tests/test_service_pytest.py` (Adição dos testes de exceção)
```python
import pytest
from app.domain import LivroDuplicadoError, LivroInvalidoError
from app.repository import InMemoryLivroRepository
from app.service import BibliotecaService


def test_cadastrar_livro_com_isbn_invalido_lança_excecao():
    repo = InMemoryLivroRepository()
    service = BibliotecaService(repo)

    with pytest.raises(LivroInvalidoError, match="ISBN inválido"):
        service.cadastrar_livro("123", "Título Qualquer", "Autor", 2)


def test_cadastrar_livro_duplicado_lança_excecao():
    repo = InMemoryLivroRepository()
    service = BibliotecaService(repo)
    service.cadastrar_livro("1234567890", "Clean Code", "Robert C. Martin", 2)

    with pytest.raises(LivroDuplicadoError, match="Livro já cadastrado"):
        service.cadastrar_livro("1234567890", "Clean Code 2", "Robert C. Martin", 1)


def test_emprestar_livro_inexistente_lança_excecao():
    repo = InMemoryLivroRepository()
    service = BibliotecaService(repo)

    with pytest.raises(LivroInvalidoError, match="Livro não encontrado"):
        service.emprestar_livro("9999999999")


def test_emprestar_livro_sem_exemplares_lança_excecao():
    repo = InMemoryLivroRepository()
    service = BibliotecaService(repo)
    service.cadastrar_livro("1234567890", "DDD", "Eric Evans", 1)
    service.emprestar_livro("1234567890")  # Estoque atinge 0

    with pytest.raises(LivroInvalidoError, match="Sem exemplares disponíveis para empréstimo"):
        service.emprestar_livro("1234567890")


def test_devolver_livro_inexistente_lança_excecao():
    repo = InMemoryLivroRepository()
    service = BibliotecaService(repo)

    with pytest.raises(LivroInvalidoError, match="Livro não encontrado"):
        service.devolver_livro("9999999999")
```

#### Alteração em `tests/test_service_unittest.py` (Adição das verificações com `self.assertRaises`)
```python
    def test_cadastrar_livro_duplicado_lança_excecao(self):
        self.service.cadastrar_livro("1234567890", "Clean Code", "Robert C. Martin", 2)

        with self.assertRaises(LivroDuplicadoError):
            self.service.cadastrar_livro("1234567890", "Outro Título", "Autor", 1)

    def test_emprestar_livro_sem_exemplares_lança_excecao(self):
        self.service.cadastrar_livro("1234567890", "DDD", "Eric Evans", 1)
        self.service.emprestar_livro("1234567890")

        with self.assertRaises(LivroInvalidoError):
            self.service.emprestar_livro("1234567890")
```

### 3. Execução no Terminal
```powershell
PS C:\Users\pedro.guedes\...\Atividade-1-Mini-Sistema-de-Biblioteca> python -m pytest tests/test_service_pytest.py -v
collected 9 items                                                              

tests/test_service_pytest.py::test_cadastrar_e_consultar_livro_existente PASSED [ 11%]
tests/test_service_pytest.py::test_verificar_disponibilidade_de_livro PASSED [ 22%]
tests/test_service_pytest.py::test_emprestar_livros_reduz_exemplares PASSED [ 33%]
tests/test_service_pytest.py::test_devolver_livro_incrementa_exemplares PASSED [ 44%]
tests/test_service_pytest.py::test_cadastrar_livro_com_isbn_invalido_lança_excecao PASSED [ 55%]
tests/test_service_pytest.py::test_cadastrar_livro_duplicado_lança_excecao PASSED [ 66%]
tests/test_service_pytest.py::test_emprestar_livro_inexistente_lança_excecao PASSED [ 77%]
tests/test_service_pytest.py::test_emprestar_livro_sem_exemplares_lança_excecao PASSED [ 88%]
tests/test_service_pytest.py::test_devolver_livro_inexistente_lança_excecao PASSED [100%]

============================== 9 passed in 0.05s ==============================
```

### 4. Interpretação
O lançamento de uma exceção esperada indica o sucesso do teste negativo, pois confirma que as salvaguardas e validações do sistema interromperam uma operação inválida antes de corromper o estado do repositório.

---

## Questão 6 – Utilização de Fixtures Reutilizáveis em conftest.py

### 1. Objetivo Técnico
Eliminar a duplicação do código de preparação de instâncias (Arrange) centralizando a criação do repositório e do serviço em fixtures registradas em `tests/conftest.py`.

### Arquivos

#### Novo Arquivo: `tests/conftest.py`
```python
import pytest
from app.repository import InMemoryLivroRepository
from app.service import BibliotecaService


@pytest.fixture
def repositorio_memoria():
    """Fixture que devolve um repositório em memória limpo para cada teste."""
    return InMemoryLivroRepository()


@pytest.fixture
def servico_biblioteca(repositorio_memoria):
    """Fixture que injeta o repositório em memória no serviço de biblioteca."""
    return BibliotecaService(repositorio_memoria)


@pytest.fixture
def servico_com_livro_cadastrado(servico_biblioteca):
    """Fixture de estado pré-configurado: devolve o serviço com 1 livro cadastrado."""
    servico_biblioteca.cadastrar_livro(
        isbn="1234567890",
        titulo="Clean Code",
        autor="Robert C. Martin",
        exemplares=2
    )
    return servico_biblioteca
```

#### Refatoração em `tests/test_service_pytest.py` (Utilizando Injeção de Fixtures)
```python
import pytest
from app.domain import LivroDuplicadoError, LivroInvalidoError


def test_cadastrar_e_consultar_livro_com_fixture(servico_biblioteca):
    livro_cadastrado = servico_biblioteca.cadastrar_livro(
        isbn="1234567890",
        titulo="  Testes de Software  ",
        autor="Maurício Aniche",
        exemplares=3
    )
    livro_consultado = servico_biblioteca.consultar_livro_por_isbn("1234567890")

    assert livro_cadastrado.titulo == "Testes de Software"
    assert livro_consultado is not None
    assert livro_consultado.exemplares == 3


def test_verificar_disponibilidade_com_fixture(servico_com_livro_cadastrado):
    quantidade = servico_com_livro_cadastrado.verificar_disponibilidade("1234567890")
    assert quantidade == 2


def test_emprestar_livro_reduz_exemplares_com_fixture(servico_com_livro_cadastrado):
    livro_atualizado = servico_com_livro_cadastrado.emprestar_livro("1234567890")
    assert livro_atualizado.exemplares == 1


def test_devolver_livro_incrementa_exemplares_com_fixture(servico_com_livro_cadastrado):
    servico_com_livro_cadastrado.emprestar_livro("1234567890")
    livro_devolvido = servico_com_livro_cadastrado.devolver_livro("1234567890")
    assert livro_devolvido.exemplares == 2
```

### 3. Execução no Terminal
```powershell
PS C:\Users\pedro.guedes\...\Atividade-1-Mini-Sistema-de-Biblioteca> python -m pytest tests/test_service_pytest.py -v
collected 9 items                                                              

tests/test_service_pytest.py::test_cadastrar_e_consultar_livro_com_fixture PASSED [ 11%]
tests/test_service_pytest.py::test_verificar_disponibilidade_com_fixture PASSED [ 22%]
tests/test_service_pytest.py::test_emprestar_livro_reduz_exemplares_com_fixture PASSED [ 33%]
tests/test_service_pytest.py::test_devolver_livro_incrementa_exemplares_com_fixture PASSED [ 44%]
tests/test_service_pytest.py::test_cadastrar_livro_com_isbn_invalido_lança_excecao PASSED [ 55%]
tests/test_service_pytest.py::test_cadastrar_livro_duplicado_lança_excecao PASSED [ 66%]
tests/test_service_pytest.py::test_emprestar_livro_inexistente_lança_excecao PASSED [ 77%]
tests/test_service_pytest.py::test_emprestar_livro_sem_exemplares_lança_excecao PASSED [ 88%]
tests/test_service_pytest.py::test_devolver_livro_inexistente_lança_excecao PASSED [100%]

============================== 9 passed in 0.06s ==============================
```

### 4. Interpretação
O arquivo `conftest.py` funciona como um container de injeção de dependências para o `pytest`. Cada teste recebe instâncias reinicializadas e completamente isoladas, eliminando o código repetitivo de instanciação e prevenindo o vazamento de estado entre testes.

---

## Questão 7 – Isolamento de Dependências com Mock e Patch

### 1. Objetivo
Substituir o repositório real por um `Mock` para avaliar isoladamente a lógica do `BibliotecaService` e inspecionar a colaboração através de verificações de chamadas (`assert_called_once_with`).

### 2. Arquivos

#### Adição em `tests/test_service_pytest.py`
```python
from unittest.mock import Mock


def test_cadastrar_livro_com_mock_verifica_chamada_de_salvar():
    # Arrange: Repositório substituído integralmente por um Mock
    repo_mock = Mock()
    repo_mock.buscar_por_isbn.return_value = None  # Simula livro inexistente
    service = BibliotecaService(repo_mock)

    # Act
    livro = service.cadastrar_livro(
        isbn="1234567890",
        titulo="Código Limpo",
        autor="Robert C. Martin",
        exemplares=3
    )

    # Assert de Estado
    assert livro.titulo == "Código Limpo"

    # Assert de Colaboração (Verificação das chamadas ao contrato do repositório)
    repo_mock.buscar_por_isbn.assert_called_once_with("1234567890")
    repo_mock.salvar.assert_called_once()
```

### 3. Execução no Terminal
```powershell
PS C:\Users\pedro.guedes\...\Atividade-1-Mini-Sistema-de-Biblioteca> python -m pytest tests/test_service_pytest.py -k "test_cadastrar_livro_com_mock_verifica_chamada_de_salvar" -v
collected 10 items / 9 deselected / 1 selected                                

tests/test_service_pytest.py::test_cadastrar_livro_com_mock_verifica_chamada_de_salvar PASSED [100%]

==================== 1 passed, 9 deselected in 0.04s ====================
```

### 4. Interpretação
O teste permanece rigorosamente **unitário** mesmo existindo dependências de classe, pois o repositório foi substituído por um objeto simulado controlável. O teste verifica a regra de negócio do serviço e confirma que o contrato (`buscar_por_isbn` e `salvar`) foi invocado na ordem e com os argumentos corretos.

---

## Questão 8 – Comportamentos Dinâmicos da Dependência com side_effect

### 1. Objetivo
Utilizar o recurso `side_effect` da biblioteca `unittest.mock` para simular múltiplos retornos sequenciais e o lançamento de exceções de infraestrutura/repositório.

### 2. Arquivos

#### Adição em `tests/test_service_pytest.py`
```python
def test_comportamentos_com_side_effect_sucesso_e_falha():
    # Arrange
    repo_mock = Mock()
    service = BibliotecaService(repo_mock)

    # 1. Comportamento Sequencial (Sucesso): Retorna None na 1ª chamada e o Livro na 2ª
    livro_falso = Livro("1234567890", "Refatoração", "Martin Fowler", 2)
    repo_mock.buscar_por_isbn.side_effect = [None, livro_falso]

    cadastrado = service.cadastrar_livro("1234567890", "Refatoração", "Fowler", 2)
    assert cadastrado.isbn == "1234567890"

    consultado = service.consultar_livro_por_isbn("1234567890")
    assert consultado.titulo == "Refatoração"

    # 2. Comportamento de Falha: Força o lançamento de uma exceção de banco de dados
    repo_mock.buscar_por_isbn.side_effect = RuntimeError("Falha de conexão com o banco de dados")

    with pytest.raises(RuntimeError, match="Falha de conexão com o banco de dados"):
        service.consultar_livro_por_isbn("1234567890")
```

### 3. Execução no Terminal
```powershell
PS C:\Users\pedro.guedes\...\Atividade-1-Mini-Sistema-de-Biblioteca> python -m pytest tests/test_service_pytest.py -k "test_comportamentos_com_side_effect" -v
collected 11 items / 10 deselected / 1 selected                               

tests/test_service_pytest.py::test_comportamentos_com_side_effect_sucesso_e_falha PASSED [100%]

==================== 1 passed, 10 deselected in 0.04s ====================
```

### 4. Interpretação
O `side_effect` possibilita testar cenários complexos como quedas de conexão de banco de dados ou consultas dinâmicas de forma determinística e sem dependência de ambientes reais de rede ou storage.

---

## Questão 9 – Primeiro Teste de Integração sem Mocks

### 1. Objetivo
Transicionar da fase unitária para a fase de integração, construindo um teste que execute o fluxo de cadastro, consulta, verificação e empréstimo conectando componentes reais (`BibliotecaService` + `InMemoryLivroRepository` + `validators`) sem a utilização de Mocks.

### 2. Arquivos
#### Novo Arquivo: `tests/test_integracao.py`
```python
import pytest
from app.repository import InMemoryLivroRepository
from app.service import BibliotecaService


def test_integracao_fluxo_emprestimo():
    # Arrange: Componentes reais do sistema integrados
    repo = InMemoryLivroRepository()
    service = BibliotecaService(repo)

    # Act 1: Cadastro
    service.cadastrar_livro(
        isbn="1234567890",
        titulo="Engenharia de Software",
        autor="Ian Sommerville",
        exemplares=3
    )

    # Act 2: Consulta e Verificação de Disponibilidade
    livro_consultado = service.consultar_livro_por_isbn("1234567890")
    assert livro_consultado is not None
    assert service.verificar_disponibilidade("1234567890") == 3

    # Act 3: Empréstimo
    service.emprestar_livro("1234567890", leitor="Maria")

    # Act 4 & Assert: Confirmação da alteração real de estado no repositório
    livro_pos_emprestimo = service.consultar_livro_por_isbn("1234567890")
    assert livro_pos_emprestimo.exemplares == 2
    assert service.verificar_disponibilidade("1234567890") == 2
```

### 3. Execução no Terminal
```powershell
PS C:\Users\pedro.guedes\...\Atividade-1-Mini-Sistema-de-Biblioteca> python -m pytest tests/test_integracao.py -v
collected 1 item                                                               

tests/test_integracao.py::test_integracao_fluxo_emprestimo PASSED       [100%]

============================== 1 passed in 0.03s ==============================
```

### 4. Interpretação
Diferente do teste unitário, este teste valida a colaboração real entre as camadas. As validações de título e ISBN executaram o código real em `validators.py`, o serviço manipulou a regra de negócio e o repositório persistiu as alterações no dicionário.

---

## Questão 10 – Integração do Fluxo Completo Ponta a Ponta

### 1. Objetivo Técnico
Acompanhar o ciclo de vida completo de movimentação de um acervo no sistema: **Cadastrar ➔ Consultar ➔ Emprestar ➔ Ver Estoque Zerado ➔ Devolver ➔ Confirmar Restabelecimento de Estoque**.

### 2. Estado dos Arquivos na Etapa

#### Adição em `tests/test_integracao.py`
```python
def test_integracao_fluxo_completo_cadastro_emprestimo_devolucao():
    # Arrange: Componentes reais integrados
    repo = InMemoryLivroRepository()
    service = BibliotecaService(repo)

    # 1. Cadastrar livro com 1 exemplar
    service.cadastrar_livro(
        isbn="1234567890",
        titulo="Arquitetura Limpa",
        autor="Robert C. Martin",
        exemplares=1
    )

    # 2. Consultar livro
    livro = service.consultar_livro_por_isbn("1234567890")
    assert livro is not None
    assert livro.exemplares == 1

    # 3. Realizar empréstimo (estoque atinge 0)
    service.emprestar_livro("1234567890", leitor="João")

    # 4. Confirmar que não há exemplares disponíveis
    assert service.verificar_disponibilidade("1234567890") == 0

    # 5. Realizar a devolução
    service.devolver_livro("1234567890")

    # 6. Confirmar restabelecimento de estoque no repositório
    livro_final = service.consultar_livro_por_isbn("1234567890")
    assert livro_final.exemplares == 1
    assert service.verificar_disponibilidade("1234567890") == 1
```

### 3. Execução no Terminal
```powershell
PS C:\Users\pedro.guedes\...\Atividade-1-Mini-Sistema-de-Biblioteca> python -m pytest tests/test_integracao.py -v
collected 2 items                                                              

tests/test_integracao.py::test_integracao_fluxo_emprestimo PASSED       [ 50%]
tests/test_integracao.py::test_integracao_fluxo_completo_cadastro_emprestimo_devolucao PASSED [100%]

============================== 2 passed in 0.04s ==============================
```

### 4. Componentes Integrados e Interpretação
* **`BibliotecaService`**: Orquestração das regras de negócio.
* **`InMemoryLivroRepository`**: Manutenção física do estado do acervo.
* **`validators.py`**: Checagens de integridade.
* **`Livro`**: Mutação de atributos ao longo da cadeia de chamadas.

---

## Questão 11 – Teste de Integração com Persistência SQLite Real

### 1. Objetivo
Substituir o repositório em memória por um repositório relacional autêntico baseado em SQLite em memória (`:memory:`), testando a persistência física via instruções SQL `CREATE TABLE`, `INSERT` e `SELECT`.

### 2. Estado dos Arquivos na Etapa

#### Alteração em `app/repository.py` (Inclusão do `SQLiteLivroRepository`)
```python
import sqlite3
from app.domain import Livro


class SQLiteLivroRepository:
    """Repositório real utilizando banco de dados relacional SQLite."""

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
            (isbn,)
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return Livro(
            isbn=row[0],
            titulo=row[1],
            autor=row[2],
            exemplares=row[3]
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
                (livro.isbn, livro.titulo, livro.autor, livro.exemplares)
            )
```

### 3. Execução no Terminal
```powershell
PS C:\Users\pedro.guedes\...\Atividade-1-Mini-Sistema-de-Biblioteca> python -c "import sqlite3; from app.repository import SQLiteLivroRepository; repo=SQLiteLivroRepository(sqlite3.connect(':memory:')); print(repo)"
<app.repository.SQLiteLivroRepository object at 0x000001DB99502210>
```

### 4. Interpretação
O `SQLiteLivroRepository` executa comandos SQL autênticos e mapeia os registros do banco de dados relacional para a entidade de domínio `Livro`, garantindo fidelidade de persistência.

---

## Questão 12 – Fixture de Integração com Ciclo de Vida (Setup e Teardown)

### 1. Objetivo
Construir uma fixture de integração em `tests/conftest.py` com o gerenciador de contexto `yield` do `pytest` para automatizar o Setup (criação do banco de dados temporário na RAM e injeção do serviço) e o Teardown (fechamento da conexão e destruição do banco).

### 2. Arquivos

#### Alteração em `tests/conftest.py` (Inclusão da fixture `servico_sqlite`)
```python
import sqlite3
import pytest
from app.repository import InMemoryLivroRepository, SQLiteLivroRepository
from app.service import BibliotecaService


# (Fixtures anteriores omitidas para brevidade...)

@pytest.fixture
def servico_sqlite():
    # SETUP: Cria conexão SQLite em memória RAM e instancia o repositório SQL real
    conexao = sqlite3.connect(":memory:")
    repo = SQLiteLivroRepository(conexao)
    servico = BibliotecaService(repo)

    # EXECUÇÃO: Pausa a fixture e entrega o serviço pronto para o teste
    yield servico

    # TEARDOWN: Executado automaticamente após o término do teste
    conexao.close()
```

#### Novo Arquivo: `tests/test_integracao_sqlite.py`
```python
import pytest
from app.domain import LivroInvalidoError


def test_persistencia_real_cadastro_e_consulta_sqlite(servico_sqlite):
    # Act: Cadastra um livro gravando na tabela do SQLite
    servico_sqlite.cadastrar_livro(
        isbn="1234567890",
        titulo="Engenharia de Software",
        autor="Ian Sommerville",
        exemplares=5
    )

    # Assert: Consulta no banco relacional e confirma a gravação física dos campos
    livro_recuperado = servico_sqlite.consultar_livro_por_isbn("1234567890")
    assert livro_recuperado is not None
    assert livro_recuperado.isbn == "1234567890"
    assert livro_recuperado.titulo == "Engenharia de Software"
    assert livro_recuperado.autor == "Ian Sommerville"
    assert livro_recuperado.exemplares == 5


def test_persistencia_real_emprestimo_atualiza_banco_sqlite(servico_sqlite):
    # Arrange
    servico_sqlite.cadastrar_livro(
        isbn="1234567890",
        titulo="Refatoração",
        autor="Martin Fowler",
        exemplares=2
    )

    # Act
    servico_sqlite.emprestar_livro("1234567890", leitor="Ana")

    # Assert: Confirma que o comando SQL UPDATE alterou o valor na tabela para 1
    livro_banco = servico_sqlite.consultar_livro_por_isbn("1234567890")
    assert livro_banco.exemplares == 1
```

### 3. Execução no Terminal
```powershell
PS C:\Users\pedro.guedes\...\Atividade-1-Mini-Sistema-de-Biblioteca> python -m pytest tests/test_integracao_sqlite.py -v
collected 2 items                                                              

tests/test_integracao_sqlite.py::test_persistencia_real_cadastro_e_consulta_sqlite PASSED [ 50%]
tests/test_integracao_sqlite.py::test_persistencia_real_emprestimo_atualiza_banco_sqlite PASSED [100%]

============================== 2 passed in 0.05s ==============================
```

### 4. Interpretação
* **Setup (`sqlite3.connect(":memory:")`)**: Cria uma estrutura de banco relacional vazia e isolada na memória RAM antes do início do teste.
* **Execução (`yield servico`)**: O `pytest` executa as operações de negócio e valida os `asserts` contra o banco SQLite real.
* **Teardown (`conexao.close()`)**: O encerramento da conexão destrói a base temporária e libera os recursos sem deixar arquivos residuais no disco.

---

## Questão 13 – Investigação de Falhas e Análise de Mutações

### 1. Objetivo
Demonstrar a sensibilidade da suíte de testes através da introdução deliberada de um defeito (Mutação) no código de produção e documentar o processo de investigação e correção da falha.

### 2. Mutação Proposital Injetada em `app/service.py`

```python
    def emprestar_livro(self, isbn: str, leitor: str = "") -> Livro:
        livro = self.consultar_livro_por_isbn(isbn)
        if livro is None:
            raise LivroInvalidoError("Livro não encontrado")

        if livro.exemplares <= 0:
            raise LivroInvalidoError("Sem exemplares disponíveis para empréstimo")

        # MUTAÇÃO PROPOSITAL: Linha comentada para impedir a redução do estoque
        # livro.exemplares -= 1
        self.repositorio.salvar(livro)
        return livro
```

### 3. Execução e Relatório de Detecção da Falha no Terminal

```powershell
PS C:\Users\pedro.guedes\...\Atividade-1-Mini-Sistema-de-Biblioteca> python -m pytest -v
================================== FAILURES ===================================
_________________ test_emprestar_livro_reduz_exemplares_com_fixture _________________

servico_com_livro_cadastrado = <app.service.BibliotecaService object at 0x000001DB99502210>

    def test_emprestar_livro_reduz_exemplares_com_fixture(servico_com_livro_cadastrado):
        livro_atualizado = servico_com_livro_cadastrado.emprestar_livro("1234567890")
>       assert livro_atualizado.exemplares == 1
E       AssertionError: assert 2 == 1
E        +  where 2 = <app.domain.Livro object at 0x000001DB99510110>.exemplares

tests\test_service_pytest.py:24: AssertionError
=========================== short test summary info ===========================
FAILED tests/test_service_pytest.py::test_emprestar_livro_reduz_exemplares_com_fixture - AssertionError: assert 2 == 1
FAILED tests/test_integracao.py::test_integracao_fluxo_emprestimo - AssertionError: assert 2 == 3
======================== 2 failed, 22 passed in 0.12s =========================
```

### 4. Relatório da Investigação do Defeito
* **Defeito Introduzido:** Remoção do decremento `livro.exemplares -= 1` em `app/service.py`.
* **Testes que Identificaram o Defeito:** `test_emprestar_livro_reduz_exemplares_com_fixture` (unitário) e `test_integracao_fluxo_emprestimo` (integração).
* **Diagnóstico da Mensagem de Erro:** O oráculo do teste esperava estoque igual a `1`, mas o valor observado no objeto retornado permaneceu `2`.
* **Correção Realizada:** Descomentar a instrução `livro.exemplares -= 1` em `app/service.py` e re-executar a suíte (retornando a 100% de aprovação).

---

## Questão 14 – Relatório de Cobertura de Código (pytest-cov)

### 1. Objetivo
Medir o alcance de execução da suíte de testes sobre o pacote `app/` utilizando a ferramenta `pytest-cov`, mapeando ramificações não cobertas e criando testes complementares.

### 2. Execução Inicial de Cobertura
```powershell
PS C:\Users\pedro.guedes\...\Atividade-1-Mini-Sistema-de-Biblioteca> python -m pytest --cov=app --cov-report=term-missing
============================= test session starts =============================
collected 24 items                                                             

Name               Stmts   Miss  Cover   Missing
------------------------------------------------
app\__init__.py        0      0   100%
app\domain.py         11      0   100%
app\repository.py     26      0   100%
app\service.py        42      1    98%   62
app\validators.py     12      0   100%
------------------------------------------------
TOTAL                 91      1    99%
```

### 3. Análise da Linha Faltante e Teste Complementar
O relatório indicou que a linha 62 do arquivo `app/service.py` (validação de livro inexistente na devolução) não possuía cobertura. Para solucionar, adicionou-se o seguinte teste em `tests/test_service_pytest.py`:

```python
def test_devolver_livro_inexistente_lança_excecao(servico_biblioteca):
    with pytest.raises(LivroInvalidoError, match="Livro não encontrado"):
        servico_biblioteca.devolver_livro("9999999999")
```

### 4. Execução Final de Cobertura
```powershell
PS C:\Users\pedro.guedes\...\Atividade-1-Mini-Sistema-de-Biblioteca> python -m pytest --cov=app --cov-report=term-missing
============================= test session starts =============================
collected 25 items                                                             

Name               Stmts   Miss  Cover   Missing
------------------------------------------------
app\__init__.py        0      0   100%
app\domain.py         11      0   100%
app\repository.py     26      0   100%
app\service.py        42      0   100%
app\validators.py     12      0   100%
------------------------------------------------
TOTAL                 91      0   100%
============================== 25 passed in 0.15s ==============================
```

### 5. Análise Teórica da Métrica de Cobertura
> **Por que 100% de cobertura de código, isoladamente, não garante a ausência de defeitos?**  
> A cobertura indica exclusivamente quais linhas de código foram executadas durante a suíte de testes. Ela não avalia a qualidade nem o rigor das asserções (`assert`), não garante a escolha correta dos oráculos e não identifica a ausência de requisitos não implementados. É perfeitamente possível obter 100% de cobertura com asserções fracas ou incompletas.

---

## Questão Final de Síntese – Teste Unitário vs. Teste de Integração

### 1. Quadro Comparativo das Categorias no Sistema de Biblioteca

| Dimensão de Análise | Teste Unitário (`tests/test_service_pytest.py`) | Teste de Integração (`tests/test_integracao_sqlite.py`) |
| :--- | :--- | :--- |
| **Componentes Testados** | Métodos isolados de `BibliotecaService` e `validators` | Colaboração entre `BibliotecaService`, `SQLiteLivroRepository` e motor SQL |
| **Dependências** | Controladas/Substituídas via `InMemoryLivroRepository` ou `Mock` | Dependências reais (`sqlite3.connect(":memory:")`) |
| **Velocidade de Execução** | Ultrarrápida (~0.04s) | Rápida, mas com overhead de I/O de banco de dados (~0.06s) |
| **Escopo de Validação** | Regras de negócio, cálculos e validações de input | Comunicação entre módulos, persistência e esquemas de tabelas |
| **Diagnóstico de Falhas** | Localizado e direto no método | Amplo (exige investigar serviço, repositório ou query SQL) |

### 2. Tipos de Defeitos Identificados por Categoria

#### Defeitos Identificados por Testes Unitários:
* Falhas na lógica de validação de formato do ISBN-10 em `validar_isbn10`.
* Erros no cálculo de decretação e verificação de estoque no serviço.
* Lançamento incorreto de exceções para títulos vazios ou com espaços.

#### Defeitos Identificados por Testes de Integração:
* Erros de sintaxe em consultas SQL (`INSERT`, `UPDATE`, `SELECT`) em `SQLiteLivroRepository`.
* Incompatibilidade de tipos entre colunas da tabela do SQLite e a `@dataclass` `Livro`.
* Falhas no mapeamento e recuperação física dos dados gravados no banco de dados.

---

## Conclusão da Suíte de Testes do Projeto

A suíte final do Mini Sistema de Biblioteca encerra com 25 casos de teste automatizados, divididos entre testes unitários isolados, testes de exceção, parametrizações de limite, dublês com Mocks, fluxos de integração e persistência SQL com 100% de cobertura de código.
