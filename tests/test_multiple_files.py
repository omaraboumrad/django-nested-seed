"""Tests for loading multiple YAML files with cross-file references."""

import pytest
from django.contrib.auth.models import User

from django_nested_seed.config.base import SeedConfig
from django_nested_seed.core.loader import SeedLoader
from tests.testapp.models import Category, Publisher, Author, Book


@pytest.mark.django_db
class TestMultipleFiles:
    """Test loading multiple YAML files and maintaining references across them."""

    def test_load_multiple_files_with_cross_references(self, tmp_path):
        """Test that references from earlier files are available to later files."""
        # First file: Define base entities (Users and Categories)
        file1_content = """
auth:
  User:
    - $ref: alice
      username: "alice"
      email: "alice@example.com"
      first_name: "Alice"
      last_name: "Johnson"
    - $ref: bob
      username: "bob"
      email: "bob@example.com"
      first_name: "Bob"
      last_name: "Smith"

testapp:
  Category:
    - $ref: python
      name: "Python"
      slug: "python"
    - $ref: django
      name: "Django"
      slug: "django"
    - $ref: web
      name: "Web Development"
      slug: "web-dev"
"""
        file1 = tmp_path / "01_base.yaml"
        file1.write_text(file1_content)

        # Second file: Define Publishers and Authors using references from file1
        file2_content = """
testapp:
  Publisher:
    - $ref: oreilly
      name: "O'Reilly Media"
      country: "USA"
    - $ref: manning
      name: "Manning Publications"
      country: "USA"

  Author:
    - $ref: alice_author
      user: "$alice"  # Reference from file1
      pen_name: "Alice J."
      bio: "Python expert and author"
    - $ref: bob_author
      user: "$bob"  # Reference from file1
      pen_name: "Bob S."
      bio: "Web development specialist"
"""
        file2 = tmp_path / "02_publishers_authors.yaml"
        file2.write_text(file2_content)

        # Third file: Define Books using references from both file1 and file2
        file3_content = """
testapp:
  Book:
    - title: "Python Fundamentals"
      author: "$alice_author"  # Reference from file2
      publisher: "$oreilly"    # Reference from file2
      status: "PUBLISHED"
      published_at: "2024-01-15"
      categories:
        - "$python"            # Reference from file1

    - title: "Django for Beginners"
      author: "$alice_author"  # Reference from file2
      publisher: "$manning"    # Reference from file2
      status: "PUBLISHED"
      published_at: "2024-03-20"
      categories:
        - "$python"            # Reference from file1
        - "$django"            # Reference from file1
        - "$web"               # Reference from file1

    - title: "Web Development Guide"
      author: "$bob_author"    # Reference from file2
      publisher: "$oreilly"    # Reference from file2
      status: "DRAFT"
      categories:
        - "$web"               # Reference from file1
"""
        file3 = tmp_path / "03_books.yaml"
        file3.write_text(file3_content)

        # Load all files in order
        config = SeedConfig.from_django_settings()
        loader = SeedLoader(config=config, verbose=False)
        loader.load([str(file1), str(file2), str(file3)])

        # Verify all entities were created
        assert User.objects.count() == 2
        assert Category.objects.count() == 3
        assert Publisher.objects.count() == 2
        assert Author.objects.count() == 2
        assert Book.objects.count() == 3

        # Verify Users from file1
        alice = User.objects.get(username="alice")
        assert alice.email == "alice@example.com"
        assert alice.first_name == "Alice"

        bob = User.objects.get(username="bob")
        assert bob.email == "bob@example.com"
        assert bob.first_name == "Bob"

        # Verify Categories from file1
        python_cat = Category.objects.get(slug="python")
        django_cat = Category.objects.get(slug="django")
        web_cat = Category.objects.get(slug="web-dev")

        # Verify Publishers from file2
        oreilly = Publisher.objects.get(name="O'Reilly Media")
        manning = Publisher.objects.get(name="Manning Publications")

        # Verify Authors from file2 (using references from file1)
        alice_author = Author.objects.get(pen_name="Alice J.")
        assert alice_author.user == alice
        assert alice_author.bio == "Python expert and author"

        bob_author = Author.objects.get(pen_name="Bob S.")
        assert bob_author.user == bob
        assert bob_author.bio == "Web development specialist"

        # Verify Books from file3 (using references from file1 and file2)
        python_book = Book.objects.get(title="Python Fundamentals")
        assert python_book.author == alice_author
        assert python_book.publisher == oreilly
        assert python_book.status == "PUBLISHED"
        assert python_book.categories.count() == 1
        assert python_cat in python_book.categories.all()

        django_book = Book.objects.get(title="Django for Beginners")
        assert django_book.author == alice_author
        assert django_book.publisher == manning
        assert django_book.status == "PUBLISHED"
        assert django_book.categories.count() == 3
        assert python_cat in django_book.categories.all()
        assert django_cat in django_book.categories.all()
        assert web_cat in django_book.categories.all()

        web_book = Book.objects.get(title="Web Development Guide")
        assert web_book.author == bob_author
        assert web_book.publisher == oreilly
        assert web_book.status == "DRAFT"
        assert web_book.categories.count() == 1
        assert web_cat in web_book.categories.all()

        # Verify registry has all references
        assert loader.registry.has("auth.User.alice")
        assert loader.registry.has("auth.User.bob")
        assert loader.registry.has("testapp.Category.python")
        assert loader.registry.has("testapp.Category.django")
        assert loader.registry.has("testapp.Publisher.oreilly")
        assert loader.registry.has("testapp.Publisher.manning")
        assert loader.registry.has("testapp.Author.alice_author")
        assert loader.registry.has("testapp.Author.bob_author")

    def test_multiple_files_with_nested_and_cross_references(self, tmp_path):
        """Test mixing nested objects with cross-file references."""
        # First file: Base users
        file1_content = """
auth:
  User:
    - $ref: user1
      username: "user1"
      email: "user1@example.com"
"""
        file1 = tmp_path / "users.yaml"
        file1.write_text(file1_content)

        # Second file: Authors with nested relationships AND cross-file references
        file2_content = """
testapp:
  Author:
    - $ref: author1
      user: "$user1"  # Cross-file reference
      pen_name: "Author One"
      bio: "First author"
      books:
        - title: "Book by Author 1"
          status: "PUBLISHED"
          publisher:  # Nested publisher
            name: "Nested Publisher"
            country: "USA"
          categories:
            - name: "Nested Category"
              slug: "nested-cat"
"""
        file2 = tmp_path / "authors.yaml"
        file2.write_text(file2_content)

        # Load both files
        config = SeedConfig.from_django_settings()
        loader = SeedLoader(config=config, verbose=False)
        loader.load([str(file1), str(file2)])

        # Verify everything was created correctly
        assert User.objects.count() == 1
        assert Author.objects.count() == 1
        assert Book.objects.count() == 1
        assert Publisher.objects.count() == 1
        assert Category.objects.count() == 1

        user = User.objects.get(username="user1")
        author = Author.objects.get(pen_name="Author One")
        assert author.user == user

        book = Book.objects.get(title="Book by Author 1")
        assert book.author == author
        assert book.publisher.name == "Nested Publisher"
        assert book.categories.count() == 1
        assert book.categories.first().slug == "nested-cat"

    def test_auto_generated_refs_across_files(self, tmp_path):
        """Test that auto-generated references work across multiple files."""
        # First file: Categories without explicit $ref
        file1_content = """
testapp:
  Category:
    - name: "First Category"
      slug: "cat-1"
    - name: "Second Category"
      slug: "cat-2"
"""
        file1 = tmp_path / "categories.yaml"
        file1.write_text(file1_content)

        # Second file: Publishers (different model) to test cross-file registry
        file2_content = """
testapp:
  Publisher:
    - name: "Test Publisher"
      country: "USA"
"""
        file2 = tmp_path / "publishers.yaml"
        file2.write_text(file2_content)

        # Load both files
        config = SeedConfig.from_django_settings()
        loader = SeedLoader(config=config, verbose=False)
        loader.load([str(file1), str(file2)])

        # Verify all objects created
        assert Category.objects.count() == 2
        assert Publisher.objects.count() == 1

        # Verify auto-generated keys are in registry
        assert loader.registry.has("testapp.Category.category_0")
        assert loader.registry.has("testapp.Category.category_1")
        assert loader.registry.has("testapp.Publisher.publisher_0")

    def test_topological_sorting_across_files(self, tmp_path):
        """Test that topological sorting works across files when loaded together."""
        # File 1: Define users and authors
        file1_content = """
auth:
  User:
    - $ref: expert
      username: "expert"
      email: "expert@example.com"

testapp:
  Author:
    - $ref: expert_author
      user: "$expert"
      pen_name: "The Expert"
      bio: "Expert in the field"
"""
        file1 = tmp_path / "authors.yaml"
        file1.write_text(file1_content)

        # File 2: Books that reference authors from file 1
        file2_content = """
testapp:
  Book:
    - title: "Advanced Topics"
      author: "$expert_author"  # Reference from file1
      publisher:
        name: "Quick Publisher"
        country: "UK"
      status: "PUBLISHED"
      categories:
        - name: "Advanced"
          slug: "advanced"
"""
        file2 = tmp_path / "books.yaml"
        file2.write_text(file2_content)

        # Load files together - topological sorting should handle dependencies
        config = SeedConfig.from_django_settings()
        loader = SeedLoader(config=config, verbose=False)
        loader.load([str(file1), str(file2)])

        # Verify everything was created correctly
        assert User.objects.count() == 1
        assert Author.objects.count() == 1
        assert Book.objects.count() == 1

        book = Book.objects.get(title="Advanced Topics")
        author = Author.objects.get(pen_name="The Expert")
        assert book.author == author

    def test_references_available_across_all_files(self, tmp_path):
        """Test that references defined in any file are available to all files."""
        # File 1: Base categories and users
        file1_content = """
auth:
  User:
    - $ref: user1
      username: "user1"
      email: "user1@example.com"

testapp:
  Category:
    - $ref: cat1
      name: "Category 1"
      slug: "cat-1"
    - $ref: cat2
      name: "Category 2"
      slug: "cat-2"
"""
        file1 = tmp_path / "base.yaml"
        file1.write_text(file1_content)

        # File 2: Publishers
        file2_content = """
testapp:
  Publisher:
    - $ref: pub1
      name: "Publisher 1"
      country: "USA"
"""
        file2 = tmp_path / "publishers.yaml"
        file2.write_text(file2_content)

        # File 3: Authors and Books using references from both file1 and file2
        file3_content = """
testapp:
  Author:
    - $ref: author1
      user: "$user1"  # From file1
      pen_name: "Author One"
      bio: "Bio"

  Book:
    - title: "Test Book"
      author: "$author1"  # From file3
      publisher: "$pub1"  # From file2
      status: "PUBLISHED"
      categories:
        - "$cat1"  # From file1
        - "$cat2"  # From file1
"""
        file3 = tmp_path / "books.yaml"
        file3.write_text(file3_content)

        # Load all files
        config = SeedConfig.from_django_settings()
        loader = SeedLoader(config=config, verbose=False)
        loader.load([str(file1), str(file2), str(file3)])

        # Verify all objects created
        assert User.objects.count() == 1
        assert Category.objects.count() == 2
        assert Publisher.objects.count() == 1
        assert Author.objects.count() == 1
        assert Book.objects.count() == 1

        # Verify relationships work across files
        book = Book.objects.get(title="Test Book")
        assert book.author.user.username == "user1"
        assert book.publisher.name == "Publisher 1"
        assert book.categories.count() == 2

        # Verify all references are in registry
        assert loader.registry.has("auth.User.user1")
        assert loader.registry.has("testapp.Category.cat1")
        assert loader.registry.has("testapp.Category.cat2")
        assert loader.registry.has("testapp.Publisher.pub1")
        assert loader.registry.has("testapp.Author.author1")
