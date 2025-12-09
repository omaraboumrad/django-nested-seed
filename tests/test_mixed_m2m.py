"""Tests for mixed M2M (references and inline definitions)."""

import pytest
from django.contrib.auth.models import User

from django_nested_seed.config.base import SeedConfig
from django_nested_seed.core.loader import SeedLoader
from tests.testapp.models import Category, Book, Publisher, Author


@pytest.mark.django_db
class TestMixedM2M:
    """Test M2M fields with mixed references and inline definitions."""

    def test_m2m_with_references_and_inline(self, tmp_path):
        """Test M2M field containing both references and inline object definitions."""
        yaml_content = """
auth:
  User:
    - $ref: admin
      username: "admin"
      email: "admin@example.com"

testapp:
  Category:
    - $ref: python
      name: "Python"
      slug: "python"

  Publisher:
    - $ref: packt
      name: "Packt Publishing"
      country: "UK"

  Author:
    - $ref: john
      user: "auth.User.admin"
      pen_name: "John Doe"
      bio: "Python expert"

  Book:
    - $ref: django_book
      title: "Django Guide"
      author: "testapp.Author.john"
      publisher: "testapp.Publisher.packt"
      status: "PUBLISHED"
      published_at: "2025-01-01"
      categories:
        - "testapp.Category.python"  # Reference to existing category
        - name: "Django"  # Inline category definition
          slug: "django"
        - name: "Web Development"  # Another inline category
          slug: "web-dev"
"""
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text(yaml_content)

        config = SeedConfig()
        loader = SeedLoader(config=config, verbose=False)
        loader.load([str(yaml_file)])

        # Verify all objects created
        assert User.objects.count() == 1
        assert Category.objects.count() == 3  # python + 2 inline
        assert Book.objects.count() == 1

        # Verify the book
        book = Book.objects.get(title="Django Guide")
        assert book.categories.count() == 3

        # Verify all category names
        category_names = set(book.categories.values_list("name", flat=True))
        assert category_names == {"Python", "Django", "Web Development"}

        # Verify the inline categories exist independently
        django_cat = Category.objects.get(slug="django")
        assert django_cat.name == "Django"

        web_cat = Category.objects.get(slug="web-dev")
        assert web_cat.name == "Web Development"

    def test_m2m_all_inline(self, tmp_path):
        """Test M2M field with only inline definitions."""
        yaml_content = """
auth:
  User:
    - $ref: admin
      username: "admin"
      email: "admin@example.com"

testapp:
  Publisher:
    - $ref: packt
      name: "Packt Publishing"
      country: "UK"

  Author:
    - $ref: john
      user: "auth.User.admin"
      pen_name: "John Doe"
      bio: "Python expert"

  Book:
    - $ref: django_book
      title: "Django Guide"
      author: "testapp.Author.john"
      publisher: "testapp.Publisher.packt"
      status: "PUBLISHED"
      published_at: "2025-01-01"
      categories:
        - name: "Python"
          slug: "python"
        - name: "Django"
          slug: "django"
"""
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text(yaml_content)

        config = SeedConfig()
        loader = SeedLoader(config=config, verbose=False)
        loader.load([str(yaml_file)])

        # Verify
        assert Category.objects.count() == 2
        book = Book.objects.get(title="Django Guide")
        assert book.categories.count() == 2
        category_names = set(book.categories.values_list("name", flat=True))
        assert category_names == {"Python", "Django"}

    def test_m2m_all_references(self, tmp_path):
        """Test M2M field with only references (backward compatibility)."""
        yaml_content = """
auth:
  User:
    - $ref: admin
      username: "admin"
      email: "admin@example.com"

testapp:
  Category:
    - $ref: python
      name: "Python"
      slug: "python"
    - $ref: django
      name: "Django"
      slug: "django"

  Publisher:
    - $ref: packt
      name: "Packt Publishing"
      country: "UK"

  Author:
    - $ref: john
      user: "auth.User.admin"
      pen_name: "John Doe"
      bio: "Python expert"

  Book:
    - $ref: django_book
      title: "Django Guide"
      author: "testapp.Author.john"
      publisher: "testapp.Publisher.packt"
      status: "PUBLISHED"
      published_at: "2025-01-01"
      categories:
        - "testapp.Category.python"
        - "testapp.Category.django"
"""
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text(yaml_content)

        config = SeedConfig()
        loader = SeedLoader(config=config, verbose=False)
        loader.load([str(yaml_file)])

        # Verify
        assert Category.objects.count() == 2
        book = Book.objects.get(title="Django Guide")
        assert book.categories.count() == 2
