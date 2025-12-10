"""Tests for database lookup functionality."""

import pytest
from django.contrib.auth.models import User

from django_nested_seed.config.base import SeedConfig
from django_nested_seed.core.loader import SeedLoader
from django_nested_seed.core.exceptions import ReferenceError
from tests.testapp.models import Author, Book, Category, Publisher


@pytest.mark.django_db
class TestDatabaseLookups:
    """Test database lookup functionality using @ syntax."""

    def test_lookup_by_pk(self, tmp_path):
        """Test looking up existing record by primary key."""
        # Create an existing user in the database
        existing_user = User.objects.create(
            username="existing_user",
            email="existing@example.com"
        )

        # Create YAML that references the existing user by PK
        yaml_content = f"""
testapp:
  Author:
    - pen_name: "Test Author"
      bio: "A test author"
      user: "@pk:{existing_user.pk}"
"""
        yaml_file = tmp_path / "lookup_by_pk.yaml"
        yaml_file.write_text(yaml_content)

        config = SeedConfig.from_django_settings()
        loader = SeedLoader(config=config, verbose=False)
        loader.load([str(yaml_file)])

        # Verify author was created with reference to existing user
        assert Author.objects.count() == 1
        author = Author.objects.first()
        assert author.pen_name == "Test Author"
        assert author.user.pk == existing_user.pk
        assert author.user.username == "existing_user"

    def test_lookup_by_username(self, tmp_path):
        """Test looking up existing record by unique field (username)."""
        # Create an existing user
        User.objects.create(
            username="alice",
            email="alice@example.com",
            first_name="Alice"
        )

        # Create YAML that references the user by username
        yaml_content = """
testapp:
  Author:
    - pen_name: "Alice Wonder"
      bio: "Author bio"
      user: "@username:alice"
"""
        yaml_file = tmp_path / "lookup_by_username.yaml"
        yaml_file.write_text(yaml_content)

        config = SeedConfig.from_django_settings()
        loader = SeedLoader(config=config, verbose=False)
        loader.load([str(yaml_file)])

        # Verify author references the existing user
        assert Author.objects.count() == 1
        author = Author.objects.first()
        assert author.user.username == "alice"
        assert author.user.first_name == "Alice"

    def test_lookup_by_multiple_fields(self, tmp_path):
        """Test looking up record by multiple fields."""
        # Create an existing publisher
        Publisher.objects.create(
            name="O'Reilly Media",
            country="USA"
        )

        # Create YAML with multi-field lookup
        yaml_content = """
auth:
  User:
    - $ref: author_user
      username: "guido"
      email: "guido@example.com"

testapp:
  Author:
    - $ref: guido
      pen_name: "Guido"
      bio: "Python creator"
      user: "$author_user"

  Book:
    - title: "Learning Python"
      author: "$guido"
      publisher: "@{name:O'Reilly Media,country:USA}"
      status: "PUBLISHED"
"""
        yaml_file = tmp_path / "lookup_multi_field.yaml"
        yaml_file.write_text(yaml_content)

        config = SeedConfig.from_django_settings()
        loader = SeedLoader(config=config, verbose=False)
        loader.load([str(yaml_file)])

        # Verify book references the existing publisher
        assert Book.objects.count() == 1
        book = Book.objects.first()
        assert book.publisher.name == "O'Reilly Media"
        assert book.publisher.country == "USA"
        # Verify no new publisher was created
        assert Publisher.objects.count() == 1

    def test_lookup_in_m2m_field(self, tmp_path):
        """Test database lookup in ManyToMany field."""
        # Create existing categories in the database
        cat1 = Category.objects.create(name="Python", slug="python")
        cat2 = Category.objects.create(name="Web", slug="web")

        # Create YAML that references existing categories
        yaml_content = """
auth:
  User:
    - $ref: author_user
      username: "testauthor"
      email: "test@example.com"

testapp:
  Publisher:
    - $ref: pub1
      name: "Test Publisher"
      country: "USA"

  Author:
    - $ref: author1
      pen_name: "Test"
      bio: "Bio"
      user: "$author_user"

  Book:
    - title: "Django Book"
      author: "$author1"
      publisher: "$pub1"
      status: "PUBLISHED"
      categories:
        - "@slug:python"
        - "@slug:web"
"""
        yaml_file = tmp_path / "lookup_m2m.yaml"
        yaml_file.write_text(yaml_content)

        config = SeedConfig.from_django_settings()
        loader = SeedLoader(config=config, verbose=False)
        loader.load([str(yaml_file)])

        # Verify book has the existing categories
        assert Book.objects.count() == 1
        book = Book.objects.first()
        assert book.categories.count() == 2
        slugs = set(book.categories.values_list("slug", flat=True))
        assert slugs == {"python", "web"}
        # Verify no new categories were created
        assert Category.objects.count() == 2

    def test_mixed_references_and_lookups(self, tmp_path):
        """Test mixing $ref references with @lookup database lookups."""
        # Create existing category
        Category.objects.create(name="Existing Category", slug="existing")

        # Create YAML mixing both reference types
        yaml_content = """
auth:
  User:
    - $ref: user1
      username: "testuser"
      email: "test@example.com"

testapp:
  Category:
    - $ref: new_cat
      name: "New Category"
      slug: "new"

  Publisher:
    - $ref: pub1
      name: "Test Pub"
      country: "USA"

  Author:
    - $ref: author1
      pen_name: "Test"
      bio: "Bio"
      user: "$user1"

  Book:
    - title: "Mixed References"
      author: "$author1"
      publisher: "$pub1"
      status: "PUBLISHED"
      categories:
        - "$new_cat"
        - "@slug:existing"
"""
        yaml_file = tmp_path / "mixed_refs.yaml"
        yaml_file.write_text(yaml_content)

        config = SeedConfig.from_django_settings()
        loader = SeedLoader(config=config, verbose=False)
        loader.load([str(yaml_file)])

        # Verify book has both new and existing categories
        book = Book.objects.first()
        assert book.categories.count() == 2
        slugs = set(book.categories.values_list("slug", flat=True))
        assert slugs == {"new", "existing"}
        # Verify total categories (1 existing + 1 new)
        assert Category.objects.count() == 2

    def test_lookup_nonexistent_record_fails(self, tmp_path):
        """Test that looking up non-existent record raises clear error."""
        yaml_content = """
testapp:
  Author:
    - pen_name: "Test"
      bio: "Bio"
      user: "@username:nonexistent"
"""
        yaml_file = tmp_path / "nonexistent.yaml"
        yaml_file.write_text(yaml_content)

        config = SeedConfig.from_django_settings()
        loader = SeedLoader(config=config, verbose=False)

        with pytest.raises(ReferenceError) as exc_info:
            loader.load([str(yaml_file)])

        assert "Database lookup failed" in str(exc_info.value)
        assert "username=nonexistent" in str(exc_info.value)
        assert "does not exist" in str(exc_info.value)

    def test_lookup_multiple_results_fails(self, tmp_path):
        """Test that lookup returning multiple results raises error."""
        # Create multiple users with the same first name
        User.objects.create(username="user1", email="user1@example.com", first_name="John")
        User.objects.create(username="user2", email="user2@example.com", first_name="John")

        yaml_content = """
testapp:
  Author:
    - pen_name: "Test"
      bio: "Bio"
      user: "@first_name:John"
"""
        yaml_file = tmp_path / "multiple.yaml"
        yaml_file.write_text(yaml_content)

        config = SeedConfig.from_django_settings()
        loader = SeedLoader(config=config, verbose=False)

        with pytest.raises(ReferenceError) as exc_info:
            loader.load([str(yaml_file)])

        assert "Multiple" in str(exc_info.value)
        assert "first_name=John" in str(exc_info.value)

    def test_ref_still_works(self, tmp_path):
        """Test that $ref syntax still works after adding @ lookup support."""
        yaml_content = """
auth:
  User:
    - $ref: testuser
      username: "testuser"
      email: "test@example.com"

testapp:
  Author:
    - pen_name: "Test Author"
      bio: "Bio"
      user: "$testuser"
"""
        yaml_file = tmp_path / "ref_works.yaml"
        yaml_file.write_text(yaml_content)

        config = SeedConfig.from_django_settings()
        loader = SeedLoader(config=config, verbose=False)
        loader.load([str(yaml_file)])

        # Verify both objects were created
        assert User.objects.count() == 1
        assert Author.objects.count() == 1
        author = Author.objects.first()
        assert author.user.username == "testuser"

    def test_lookup_with_related_field_syntax(self, tmp_path):
        """Test database lookup with Django's related field syntax (double underscore)."""
        # Create user and author
        user = User.objects.create(username="authuser", email="authuser@example.com")
        Author.objects.create(user=user, pen_name="Existing Author", bio="Bio")

        yaml_content = """
testapp:
  Publisher:
    - $ref: pub1
      name: "Test Pub"
      country: "USA"

  Book:
    - title: "Book by Existing Author"
      author: "@user__username:authuser"
      publisher: "$pub1"
      status: "PUBLISHED"
"""
        yaml_file = tmp_path / "related_lookup.yaml"
        yaml_file.write_text(yaml_content)

        config = SeedConfig.from_django_settings()
        loader = SeedLoader(config=config, verbose=False)
        loader.load([str(yaml_file)])

        # Verify book references the existing author
        book = Book.objects.first()
        assert book.author.pen_name == "Existing Author"
        assert book.author.user.username == "authuser"
        # Verify no new author was created
        assert Author.objects.count() == 1

    def test_lookup_caching(self, tmp_path):
        """Test that database lookups are cached to avoid redundant queries."""
        # Create existing category
        Category.objects.create(name="Python", slug="python")

        # Create YAML that references the same category multiple times
        yaml_content = """
auth:
  User:
    - $ref: user1
      username: "author1"
      email: "author1@example.com"
    - $ref: user2
      username: "author2"
      email: "author2@example.com"

testapp:
  Publisher:
    - $ref: pub1
      name: "Test Pub"
      country: "USA"

  Author:
    - $ref: auth1
      pen_name: "Author 1"
      bio: "Bio"
      user: "$user1"
    - $ref: auth2
      pen_name: "Author 2"
      bio: "Bio"
      user: "$user2"

  Book:
    - title: "Book 1"
      author: "$auth1"
      publisher: "$pub1"
      status: "PUBLISHED"
      categories:
        - "@slug:python"
    - title: "Book 2"
      author: "$auth2"
      publisher: "$pub1"
      status: "PUBLISHED"
      categories:
        - "@slug:python"
"""
        yaml_file = tmp_path / "caching.yaml"
        yaml_file.write_text(yaml_content)

        config = SeedConfig.from_django_settings()
        loader = SeedLoader(config=config, verbose=False)
        loader.load([str(yaml_file)])

        # Verify both books reference the same category
        assert Book.objects.count() == 2
        book1 = Book.objects.get(title="Book 1")
        book2 = Book.objects.get(title="Book 2")
        assert book1.categories.first().slug == "python"
        assert book2.categories.first().slug == "python"
        # Verify only one category exists
        assert Category.objects.count() == 1
        # Verify cache has the lookup
        cache_key = "testapp.Category:{'slug': 'python'}"
        assert cache_key in loader.registry._db_lookup_cache
