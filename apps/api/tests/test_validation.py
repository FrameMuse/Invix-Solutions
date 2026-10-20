import pytest

from app.services.products import ProductError, clean_title, image_extension, image_key


def test_title_is_trimmed() -> None:
    assert clean_title("  Кружка  ") == "Кружка"


def test_empty_title_is_rejected() -> None:
    with pytest.raises(ProductError):
        clean_title("   ")


def test_same_image_gets_same_key() -> None:
    extension = image_extension("image/jpeg")
    assert extension == "jpg"
    assert image_key(b"same", extension) == image_key(b"same", extension)
    assert image_key(b"same", extension) != image_key(b"other", extension)
