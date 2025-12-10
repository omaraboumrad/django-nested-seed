"""Integration tests for the SeedLoader."""

import pytest
from django.contrib.auth.models import User

from django_nested_seed.config.base import SeedConfig
from django_nested_seed.core.loader import SeedLoader
from tests.testapp.models import Profile, Company, Team, Category


@pytest.mark.django_db
class TestSeedLoader:
    """Test the main SeedLoader functionality."""

    def test_load_simple_user(self, example_yaml_simple):
        """Test loading a simple user without relationships."""
        config = SeedConfig.from_django_settings()
        loader = SeedLoader(config=config, verbose=False)

        loader.load([example_yaml_simple])

        # Verify user was created
        assert User.objects.count() == 1
        user = User.objects.get(username="testuser")
        assert user.email == "test@example.com"
        assert user.first_name == "Test"
        assert user.last_name == "User"

    def test_load_user_with_profile(self, example_yaml_with_profile):
        """Test loading user with nested OneToOne profile."""
        config = SeedConfig.from_django_settings()
        loader = SeedLoader(config=config, verbose=False)

        loader.load([example_yaml_with_profile])

        # Verify user and profile were created
        assert User.objects.count() == 1
        assert Profile.objects.count() == 1

        user = User.objects.get(username="admin")
        assert user.is_staff is True
        assert user.is_superuser is True

        profile = user.profile
        assert profile.role == "ADMIN"
        assert profile.timezone == "Asia/Beirut"

    def test_load_company_with_teams(self, example_yaml_with_teams):
        """Test loading company with nested FK teams using default team_set accessor."""
        config = SeedConfig.from_django_settings()
        loader = SeedLoader(config=config, verbose=False)

        loader.load([example_yaml_with_teams])

        # Verify all objects created
        assert User.objects.count() == 2
        assert Company.objects.count() == 1
        assert Team.objects.count() == 1

        # Verify company
        company = Company.objects.get(code="ACME")
        assert company.name == "ACME Corp"

        # Verify team using default team_set accessor
        team = company.team_set.first()
        assert team.name == "Backend Team"

        # Verify M2M relationships
        assert team.members.count() == 2
        usernames = set(team.members.values_list("username", flat=True))
        assert usernames == {"user1", "user2"}

    def test_registry_tracking(self, example_yaml_simple):
        """Test that registry tracks created objects."""
        config = SeedConfig.from_django_settings()
        loader = SeedLoader(config=config, verbose=False)

        loader.load([example_yaml_simple])

        # Verify registry has the object
        assert loader.registry.count() == 1
        assert loader.registry.has("auth.User.testuser")

        user_instance = loader.registry.get("auth.User.testuser")
        assert user_instance.username == "testuser"

    def test_self_referential_parent(self, example_yaml_self_referential):
        """Test loading categories with self-referential parent relationship."""
        config = SeedConfig.from_django_settings()
        loader = SeedLoader(config=config, verbose=False)

        loader.load([example_yaml_self_referential])

        # Verify all categories were created
        assert Category.objects.count() == 7

        # Verify root category (Programming) has no parent
        programming = Category.objects.get(slug="programming")
        assert programming.name == "Programming"
        assert programming.parent is None

        # Verify first level children
        python_cat = Category.objects.get(slug="python")
        assert python_cat.name == "Python"
        assert python_cat.parent == programming

        javascript_cat = Category.objects.get(slug="javascript")
        assert javascript_cat.name == "JavaScript"
        assert javascript_cat.parent == programming

        # Verify second level children (nested under Python)
        django_cat = Category.objects.get(slug="django")
        assert django_cat.name == "Django"
        assert django_cat.parent == python_cat

        flask_cat = Category.objects.get(slug="flask")
        assert flask_cat.name == "Flask"
        assert flask_cat.parent == python_cat

        # Verify second level children (nested under JavaScript)
        react_cat = Category.objects.get(slug="react")
        assert react_cat.name == "React"
        assert react_cat.parent == javascript_cat

        vue_cat = Category.objects.get(slug="vue")
        assert vue_cat.name == "Vue"
        assert vue_cat.parent == javascript_cat

        # Verify reverse relationships using the related_name
        assert programming.children.count() == 2
        assert set(programming.children.values_list("slug", flat=True)) == {"python", "javascript"}

        assert python_cat.children.count() == 2
        assert set(python_cat.children.values_list("slug", flat=True)) == {"django", "flask"}

        assert javascript_cat.children.count() == 2
        assert set(javascript_cat.children.values_list("slug", flat=True)) == {"react", "vue"}

    def test_no_explicit_refs_identity_uniqueness(self):
        """Test that auto-generated keys are unique across different parents."""
        yaml_content = """
testapp:
  Category:
    - name: "one"
      slug: "one"
      children:
        - name: "one.one"
          slug: "one-one"
    - name: "two"
      slug: "two"
      children:
        - name: "two.one"
          slug: "two-one"
"""

        config = SeedConfig.from_django_settings()
        loader = SeedLoader(config=config, verbose=False)

        # This should not raise ValueError about duplicate identity
        loader.load_from_string(yaml_content)

        # Verify all objects created
        assert Category.objects.count() == 4

        one = Category.objects.get(slug="one")
        assert one.parent is None
        assert one.children.count() == 1

        two = Category.objects.get(slug="two")
        assert two.parent is None
        assert two.children.count() == 1

        one_one = Category.objects.get(slug="one-one")
        assert one_one.parent == one

        two_one = Category.objects.get(slug="two-one")
        assert two_one.parent == two
