"""Tests for M2M with custom through model support."""

import pytest
from django.contrib.auth.models import User

from django_nested_seed.config.base import SeedConfig
from django_nested_seed.core.loader import SeedLoader
from tests.testapp.models import Company, Team, Membership


@pytest.mark.django_db
class TestM2MThrough:
    """Test M2M fields with custom through models."""

    def test_m2m_with_through_model(self, tmp_path):
        """Test M2M field with custom through model containing extra fields."""
        yaml_content = """
auth:
  User:
    - $ref: alice
      username: "alice"
      email: "alice@example.com"
    - $ref: bob
      username: "bob"
      email: "bob@example.com"

testapp:
  Company:
    - $ref: tech_corp
      name: "Tech Corp"
      code: "TECH"
      team_set:
        - $ref: engineering
          name: "Engineering Team"
          members:
            - user: "auth.User.alice"
              role: "Lead Engineer"
              date_joined: "2024-01-01"
            - user: "auth.User.bob"
              role: "Developer"
              date_joined: "2024-02-15"
"""
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text(yaml_content)

        config = SeedConfig()
        loader = SeedLoader(config=config, verbose=True)
        loader.load([str(yaml_file)])

        # Verify all objects created
        assert User.objects.count() == 2
        assert Company.objects.count() == 1
        assert Team.objects.count() == 1
        assert Membership.objects.count() == 2

        # Verify team
        team = Team.objects.get(name="Engineering Team")
        assert team.members.count() == 2

        # Verify through model instances with extra fields
        alice = User.objects.get(username="alice")
        bob = User.objects.get(username="bob")

        alice_membership = Membership.objects.get(user=alice, team=team)
        assert alice_membership.role == "Lead Engineer"
        assert str(alice_membership.date_joined) == "2024-01-01"

        bob_membership = Membership.objects.get(user=bob, team=team)
        assert bob_membership.role == "Developer"
        assert str(bob_membership.date_joined) == "2024-02-15"

    def test_m2m_through_multiple_teams(self, tmp_path):
        """Test M2M through with multiple teams."""
        yaml_content = """
auth:
  User:
    - $ref: alice
      username: "alice"
      email: "alice@example.com"
    - $ref: bob
      username: "bob"
      email: "bob@example.com"
    - $ref: carol
      username: "carol"
      email: "carol@example.com"

testapp:
  Company:
    - $ref: tech_corp
      name: "Tech Corp"
      code: "TECH"
      team_set:
        - $ref: engineering
          name: "Engineering"
          members:
            - user: "auth.User.alice"
              role: "Lead"
              date_joined: "2024-01-01"
            - user: "auth.User.bob"
              role: "Developer"
              date_joined: "2024-02-01"
        - $ref: product
          name: "Product"
          members:
            - user: "auth.User.alice"
              role: "Manager"
              date_joined: "2024-01-01"
            - user: "auth.User.carol"
              role: "Designer"
              date_joined: "2024-03-01"
"""
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text(yaml_content)

        config = SeedConfig()
        loader = SeedLoader(config=config, verbose=False)
        loader.load([str(yaml_file)])

        # Verify counts
        assert User.objects.count() == 3
        assert Team.objects.count() == 2
        assert Membership.objects.count() == 4

        # Verify Alice is in both teams with different roles
        alice = User.objects.get(username="alice")
        alice_memberships = Membership.objects.filter(user=alice)
        assert alice_memberships.count() == 2

        roles = set(alice_memberships.values_list('role', flat=True))
        assert roles == {"Lead", "Manager"}

    def test_m2m_through_with_inline_object_creation(self, tmp_path):
        """Test M2M through model with inline object creation (not just references)."""
        yaml_content = """
auth:
  User:
    - $ref: alice
      username: "alice"
      email: "alice@example.com"

testapp:
  Company:
    - name: "Tech Corp"
      code: "TECH"
      team_set:
        - name: "Engineering Team"
          members:
            - user: "$alice"  # Reference existing user
              role: "Lead Engineer"
              date_joined: "2024-01-01"
            - user:           # Inline create new user
                username: "bob"
                email: "bob@example.com"
              role: "Senior Developer"
              date_joined: "2024-01-15"
"""
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text(yaml_content)

        config = SeedConfig()
        loader = SeedLoader(config=config, verbose=True)
        loader.load([str(yaml_file)])

        # Verify all objects created
        assert User.objects.count() == 2  # alice + bob (inline created)
        assert Company.objects.count() == 1
        assert Team.objects.count() == 1
        assert Membership.objects.count() == 2

        # Verify team has both members
        team = Team.objects.first()
        assert team.members.count() == 2

        # Verify alice membership (referenced)
        alice = User.objects.get(username="alice")
        alice_membership = Membership.objects.get(user=alice, team=team)
        assert alice_membership.role == "Lead Engineer"

        # Verify bob membership (inline created)
        bob = User.objects.get(username="bob")
        assert bob.email == "bob@example.com"
        bob_membership = Membership.objects.get(user=bob, team=team)
        assert bob_membership.role == "Senior Developer"
        assert str(bob_membership.date_joined) == "2024-01-15"

    def test_m2m_through_with_inline_nested_objects(self, tmp_path):
        """Test M2M through with inline objects that have nested children (e.g., User with Profile)."""
        yaml_content = """
testapp:
  Company:
    - name: "Tech Corp"
      code: "TECH"
      team_set:
        - name: "Engineering Team"
          members:
            - user:
                username: "alice"
                email: "alice@example.com"
                profile:  # Nested OneToOne relationship
                  role: "ENGINEER"
                  timezone: "America/Los_Angeles"
              role: "Lead Engineer"
              date_joined: "2024-01-01"
            - user:
                username: "bob"
                email: "bob@example.com"
                profile:
                  role: "ENGINEER"
                  timezone: "Europe/London"
              role: "Senior Developer"
              date_joined: "2024-01-15"
"""
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text(yaml_content)

        config = SeedConfig()
        loader = SeedLoader(config=config, verbose=True)
        loader.load([str(yaml_file)])

        # Verify all objects created
        assert User.objects.count() == 2
        assert Company.objects.count() == 1
        assert Team.objects.count() == 1
        assert Membership.objects.count() == 2

        # Verify users have profiles
        alice = User.objects.get(username="alice")
        assert alice.profile.role == "ENGINEER"
        assert alice.profile.timezone == "America/Los_Angeles"

        bob = User.objects.get(username="bob")
        assert bob.profile.role == "ENGINEER"
        assert bob.profile.timezone == "Europe/London"

        # Verify team memberships
        team = Team.objects.first()
        alice_membership = Membership.objects.get(user=alice, team=team)
        assert alice_membership.role == "Lead Engineer"

        bob_membership = Membership.objects.get(user=bob, team=team)
        assert bob_membership.role == "Senior Developer"
