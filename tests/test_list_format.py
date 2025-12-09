"""Tests for list format with auto-generated keys and $ref."""

import pytest
from django.contrib.auth.models import User

from django_nested_seed.config.base import SeedConfig
from django_nested_seed.core.loader import SeedLoader
from tests.testapp.models import Category, Publisher, Author, Book


@pytest.mark.django_db
class TestListFormat:
    """Test list format with auto-generated keys and explicit $ref."""

    def test_simple_list_format_auto_keys(self, tmp_path):
        """Test basic list format without $ref (auto-generated keys)."""
        yaml_content = """
testapp:
  Category:
    - name: "Python"
      slug: "python"
    - name: "Django"
      slug: "django"
    - name: "Web Development"
      slug: "web-dev"
"""
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text(yaml_content)

        config = SeedConfig()
        loader = SeedLoader(config=config, verbose=True)
        loader.load([str(yaml_file)])

        # Verify all objects created
        assert Category.objects.count() == 3

        # Verify data
        assert Category.objects.filter(name="Python", slug="python").exists()
        assert Category.objects.filter(name="Django", slug="django").exists()
        assert Category.objects.filter(name="Web Development", slug="web-dev").exists()

    def test_list_format_with_explicit_refs(self, tmp_path):
        """Test list format with $ref for objects that need to be referenced."""
        yaml_content = """
auth:
  User:
    - $ref: john
      username: "john"
      email: "john@example.com"

testapp:
  Category:
    - $ref: python
      name: "Python"
      slug: "python"

  Publisher:
    - $ref: oreilly
      name: "O'Reilly Media"
      country: "USA"

  Author:
    - $ref: john_author
      user: "auth.User.john"
      pen_name: "John Doe"
      bio: "Python expert"

  Book:
    - title: "Python Guide"
      author: "testapp.Author.john_author"
      publisher: "testapp.Publisher.oreilly"
      status: "PUBLISHED"
      categories:
        - "testapp.Category.python"
"""
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text(yaml_content)

        config = SeedConfig()
        loader = SeedLoader(config=config, verbose=True)
        loader.load([str(yaml_file)])

        # Verify all objects created
        assert User.objects.count() == 1
        assert Category.objects.count() == 1
        assert Publisher.objects.count() == 1
        assert Author.objects.count() == 1
        assert Book.objects.count() == 1

        # Verify relationships
        book = Book.objects.first()
        assert book.title == "Python Guide"
        assert book.author.pen_name == "John Doe"
        assert book.publisher.name == "O'Reilly Media"
        assert book.categories.count() == 1
        assert book.categories.first().name == "Python"

    def test_mixed_ref_and_auto_keys(self, tmp_path):
        """Test mixing objects with $ref and objects with auto-generated keys."""
        yaml_content = """
auth:
  User:
    - $ref: john  # Explicit $ref
      username: "john"
      email: "john@example.com"

testapp:
  Category:  # Mix of auto-generated and explicit keys
    - name: "Python"
      slug: "python"
    - name: "Django"
      slug: "django"

  Publisher:
    - $ref: oreilly  # Explicit $ref
      name: "O'Reilly Media"
      country: "USA"

  Author:
    - $ref: john_author  # Explicit $ref
      user: "auth.User.john"
      pen_name: "John Doe"
      bio: "Python expert"

  Book:
    - title: "Python Guide"
      author: "testapp.Author.john_author"
      publisher: "testapp.Publisher.oreilly"
      status: "PUBLISHED"
      categories:
        - "testapp.Category.category_0"  # Reference auto-generated key
        - "testapp.Category.category_1"
"""
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text(yaml_content)

        config = SeedConfig()
        loader = SeedLoader(config=config, verbose=False)
        loader.load([str(yaml_file)])

        # Verify counts
        assert User.objects.count() == 1
        assert Category.objects.count() == 2
        assert Publisher.objects.count() == 1
        assert Author.objects.count() == 1
        assert Book.objects.count() == 1

        # Verify relationships work across formats
        book = Book.objects.first()
        assert book.author.user.username == "john"
        assert book.categories.count() == 2

    def test_list_format_verbose_output(self, tmp_path, capsys):
        """Test that verbose output shows auto-generated keys."""
        yaml_content = """
testapp:
  Category:
    - name: "Python"
      slug: "python"
"""
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text(yaml_content)

        config = SeedConfig()
        loader = SeedLoader(config=config, verbose=True)
        loader.load([str(yaml_file)])

        captured = capsys.readouterr()
        # Should show the auto-generated key in output
        assert "[testapp.Category.category_0]" in captured.out

    def test_custom_reference_key(self, tmp_path):
        """Test using a custom reference key instead of $ref."""
        yaml_content = """
auth:
  User:
    - id: john
      username: "john"
      email: "john@example.com"

testapp:
  Category:
    - id: python
      name: "Python"
      slug: "python"

  Publisher:
    - id: oreilly
      name: "O'Reilly Media"
      country: "USA"

  Author:
    - id: john_author
      user: "auth.User.john"
      pen_name: "John Doe"
      bio: "Python expert"

  Book:
    - title: "Python Guide"
      author: "testapp.Author.john_author"
      publisher: "testapp.Publisher.oreilly"
      status: "PUBLISHED"
      categories:
        - "testapp.Category.python"
"""
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text(yaml_content)

        # Use custom reference key 'id' instead of '$ref'
        config = SeedConfig(reference_key="id")
        loader = SeedLoader(config=config, verbose=False)
        loader.load([str(yaml_file)])

        # Verify all objects created
        assert User.objects.count() == 1
        assert Category.objects.count() == 1
        assert Publisher.objects.count() == 1
        assert Author.objects.count() == 1
        assert Book.objects.count() == 1

        # Verify relationships work with custom reference key
        book = Book.objects.first()
        assert book.title == "Python Guide"
        assert book.author.pen_name == "John Doe"
        assert book.publisher.name == "O'Reilly Media"
        assert book.categories.count() == 1
        assert book.categories.first().name == "Python"
