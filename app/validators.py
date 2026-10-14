def validar_isbn10(isbn: str) -> bool:
    """Valida se o ISBN possui exatamente 10 dígitos numéricos (ignorando traços)."""

    if isbn is None:
        return False
    somente_digitos = isbn.replace("-", "")
    return len(somente_digitos) == 10 and somente_digitos.isdigit()


def normalizar_titulo(titulo: str) -> str:
    """Remove espaços extras das extremidades e entre palavras do título."""

    if titulo is None:
        raise ValueError("título obrigatório")
    partes = titulo.strip().split()
    if not partes:
        raise ValueError("título obrigatório")
    return " ".join(partes)
