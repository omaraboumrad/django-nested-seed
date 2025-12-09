"""Tests for automatic nested relationship detection."""

import pytest
from django.contrib.auth.models import User

from django_nested_seed.config.base import SeedConfig
from django_nested_seed.core.loader import SeedLoader
from tests.testapp.models import Profile, Company, Team


@pytest.mark.django_db
class TestAutoDetection:
    """Test automatic detection of nested relationships."""

    def test_detect_one_to_one_relationship(self, tmp_path):
        """Test auto-detection of OneToOne relationship using reverse accessor."""
        yaml_content = """
auth:
  User:
    - $ref: admin
      username: "admin"
      email: "admin@example.com"
      profile:  # Auto-detected OneToOne via reverse accessor
        role: "ADMIN"
        timezone: "UTC"
"""
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text(yaml_content)

        config = SeedConfig()  # Empty config - pure auto-detection
        loader = SeedLoader(config=config, verbose=False)
        loader.load([str(yaml_file)])

        # Verify
        user = User.objects.get(username="admin")
        assert hasattr(user, "profile")
        assert user.profile.role == "ADMIN"
        assert user.profile.timezone == "UTC"

    def test_detect_foreign_key_with_default_accessor(self, tmp_path):
        """Test auto-detection of FK with default team_set accessor."""
        yaml_content = """
testapp:
  Company:
    - $ref: acme
      name: "ACME Corp"
      code: "ACME"
      team_set:  # Auto-detected FK via default {model}_set accessor
        - $ref: backend
          name: "Backend Team"
        - $ref: frontend
          name: "Frontend Team"
"""
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text(yaml_content)

        config = SeedConfig()  # Empty config
        loader = SeedLoader(config=config, verbose=False)
        loader.load([str(yaml_file)])

        # Verify
        company = Company.objects.get(code="ACME")
        assert company.team_set.count() == 2
        team_names = set(company.team_set.values_list("name", flat=True))
        assert team_names == {"Backend Team", "Frontend Team"}

    def test_no_configuration_needed(self, tmp_path):
        """Test that complex nested structures work with zero configuration."""
        yaml_content = """
auth:
  User:
    - $ref: user1
      username: "user1"
      email: "user1@example.com"
    - $ref: user2
      username: "user2"
      email: "user2@example.com"

testapp:
  Company:
    - $ref: acme
      name: "ACME Corp"
      code: "ACME"
      team_set:
        - $ref: engineering
          name: "Engineering"
          members:
            - user: "auth.User.user1"
              role: "Engineer"
              date_joined: "2024-01-01"
            - user: "auth.User.user2"
              role: "Engineer"
              date_joined: "2024-01-01"
"""
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text(yaml_content)

        # ZERO configuration!
        config = SeedConfig()
        loader = SeedLoader(config=config, verbose=False)
        loader.load([str(yaml_file)])

        # Verify everything worked
        assert User.objects.count() == 2
        assert Company.objects.count() == 1
        assert Team.objects.count() == 1

        team = Team.objects.get(name="Engineering")
        assert team.members.count() == 2
        assert team.company.name == "ACME Corp"
