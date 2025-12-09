"""Tests for all README scenarios with $ref_key syntax."""

import os
import pytest
from django.contrib.auth.models import User

from django_nested_seed.config.base import SeedConfig
from django_nested_seed.core.loader import SeedLoader
from tests.testapp.models import (
    Category,
    Publisher,
    Author,
    Book,
    Company,
    Team,
    Membership,
    Profile,
)


@pytest.mark.django_db
class TestREADMEScenarios:
    """Test all scenarios from README with new $ref_key syntax."""

    def load_yaml(self, yaml_content: str, verbose: bool = False) -> None:
        """Helper to load YAML content for testing."""
        config = SeedConfig()
        loader = SeedLoader(config=config, verbose=verbose)
        loader.load_from_string(yaml_content)

    def load_example(self, example_file: str, verbose: bool = False) -> None:
        """Helper to load YAML from example file."""
        # Get the project root directory (parent of tests directory)
        tests_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(tests_dir)
        example_path = os.path.join(project_root, "examples", example_file)

        config = SeedConfig()
        loader = SeedLoader(config=config, verbose=verbose)
        loader.load([example_path])

    def test_basic_model(self):
        """Test Basic Model - simple objects with primitive fields."""
        self.load_example("01_basic_model.yaml")

        assert Category.objects.count() == 2
        assert Category.objects.filter(name="Python", slug="python").exists()
        assert Category.objects.filter(name="Django", slug="django").exists()

    def test_foreign_key_nested(self):
        """Test Model with ForeignKey (Nested) - FK with inline object."""
        self.load_example("02_foreign_key_nested.yaml")

        assert User.objects.count() == 1
        assert Author.objects.count() == 1

        author = Author.objects.first()
        assert author.pen_name == "John Doe"
        assert author.user.username == "john"
        assert author.user.email == "john@example.com"

    def test_foreign_key_referenced_with_ref_key(self):
        """Test Model with ForeignKey (Referenced) using $ref_key syntax."""
        self.load_example("03_foreign_key_referenced.yaml")

        assert User.objects.count() == 1
        assert Author.objects.count() == 1

        author = Author.objects.first()
        assert author.pen_name == "John Doe"
        assert author.user.username == "john"

    def test_foreign_key_mixed(self):
        """Test Model with ForeignKey (Mixed) - nested and referenced."""
        self.load_example("04_foreign_key_mixed.yaml")

        assert Publisher.objects.count() == 2  # oreilly + inline
        assert Author.objects.count() == 1
        assert Book.objects.count() == 1
        assert User.objects.count() == 1

        book = Book.objects.first()
        assert book.author.pen_name == "Alice Smith"
        assert book.author.user.username == "alice"  # Nested user
        assert book.publisher.name == "Tech Books Inc"  # Nested publisher

    def test_reverse_foreign_key_nested_collection(self):
        """Test Model with Reverse ForeignKey (Nested Collection)."""
        self.load_example("05_reverse_foreign_key_nested.yaml")

        assert Company.objects.count() == 1
        assert Team.objects.count() == 2

        company = Company.objects.first()
        assert company.team_set.count() == 2
        team_names = set(company.team_set.values_list("name", flat=True))
        assert team_names == {"Engineering Team", "Product Team"}

    def test_one_to_one(self):
        """Test Model with OneToOne nested relationship."""
        self.load_example("06_one_to_one.yaml")

        assert User.objects.count() == 1
        assert Profile.objects.count() == 1

        user = User.objects.first()
        assert user.profile.role == "ADMIN"
        assert user.profile.timezone == "UTC"

    def test_many_to_many_with_ref_key(self):
        """Test Model with ManyToMany using $ref_key syntax."""
        self.load_example("07_many_to_many.yaml")

        assert Category.objects.count() == 2
        assert Book.objects.count() == 1

        book = Book.objects.first()
        assert book.author.pen_name == "Guido van Rossum"
        assert book.publisher.name == "O'Reilly Media"
        assert book.categories.count() == 2

        category_names = set(book.categories.values_list("name", flat=True))
        assert category_names == {"Python", "Web Development"}

    def test_many_to_many_through_with_ref_key(self):
        """Test Model with ManyToMany (Through) using $ref_key syntax."""
        self.load_example("08_many_to_many_through.yaml")

        assert User.objects.count() == 2
        assert Team.objects.count() == 1
        assert Membership.objects.count() == 2

        team = Team.objects.first()
        assert team.members.count() == 2

        alice = User.objects.get(username="alice")
        membership = Membership.objects.get(user=alice, team=team)
        assert membership.role == "Lead Engineer"

    def test_mixed_many_to_many_with_ref_key(self):
        """Test Model with Mixed ManyToMany using $ref_key syntax."""
        self.load_example("09_mixed_many_to_many.yaml")

        assert Category.objects.count() == 3  # python + 2 inline
        assert Book.objects.count() == 1

        book = Book.objects.first()
        assert book.categories.count() == 3

        category_names = set(book.categories.values_list("name", flat=True))
        assert category_names == {"Python", "Django", "Web Frameworks"}

    def test_complex_multi_level_nesting_with_ref_key(self):
        """Test Complex Multi-Level Nesting from README using $ref_key syntax."""
        self.load_example("10_complex_multi_level.yaml")

        # Verify users and profiles
        assert User.objects.count() == 3
        assert Profile.objects.count() == 3

        admin = User.objects.get(username="admin")
        assert admin.profile.role == "ADMIN"

        alice = User.objects.get(username="alice")
        assert alice.profile.role == "ENGINEER"

        # Verify company and teams
        assert Company.objects.count() == 1
        assert Team.objects.count() == 2

        company = Company.objects.first()
        engineering = company.team_set.get(name="Engineering Team")
        product = company.team_set.get(name="Product Team")

        # Verify Alice is in both teams
        assert engineering.members.filter(username="alice").exists()
        assert product.members.filter(username="alice").exists()

        # Verify memberships with through model
        assert Membership.objects.count() == 3
        alice_eng = Membership.objects.get(user=alice, team=engineering)
        assert alice_eng.role == "Lead Engineer"

        # Verify author and books
        assert Author.objects.count() == 1
        author = Author.objects.first()
        assert author.user == alice
        assert author.books.count() == 2

        # Verify books and categories
        assert Book.objects.count() == 2
        assert Category.objects.count() == 4  # python + 3 inline

        design_patterns = Book.objects.get(title="Python Design Patterns")
        assert design_patterns.publisher.name == "O'Reilly Media"
        assert design_patterns.categories.count() == 3
        assert design_patterns.categories.filter(name="Python").exists()
        assert design_patterns.categories.filter(name="Design Patterns").exists()

        django_book = Book.objects.get(title="Django Deep Dive")
        assert django_book.status == "DRAFT"
        assert django_book.categories.count() == 2

    def test_ref_key_global_uniqueness(self):
        """Test that $ref keys must be globally unique across models."""
        yaml_content = """
auth:
  User:
    - $ref: alice
      username: "alice"
      email: "alice@example.com"

testapp:
  Category:
    - $ref: alice
      name: "Alice Category"
      slug: "alice"
"""
        config = SeedConfig()
        loader = SeedLoader(config=config, verbose=False)

        # Should raise error due to duplicate ref_key
        with pytest.raises(ValueError, match="Reference key 'alice' already used"):
            loader.load_from_string(yaml_content)

    def test_ref_key_with_nested_and_referenced(self):
        """Test combining $ref_key references with nested objects."""
        yaml_content = """
auth:
  User:
    - $ref: john
      username: "john"
      email: "john@example.com"

testapp:
  Author:
    - $ref: john_author
      user: "$john"
      pen_name: "John Doe"
      bio: "Author"
      books:
        - title: "First Book"
          publisher:
            name: "Inline Publisher"
            country: "USA"
          status: "PUBLISHED"
"""
        self.load_yaml(yaml_content)

        assert User.objects.count() == 1
        assert Author.objects.count() == 1
        assert Book.objects.count() == 1
        assert Publisher.objects.count() == 1

        author = Author.objects.first()
        assert author.user.username == "john"
        assert author.books.count() == 1

        book = author.books.first()
        assert book.publisher.name == "Inline Publisher"
