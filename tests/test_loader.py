"""Integration tests for the SeedLoader."""

import pytest
from django.contrib.auth.models import User

from django_nested_seed.config.base import SeedConfig
from django_nested_seed.core.loader import SeedLoader
from tests.testapp.models import Profile, Company, Team


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
