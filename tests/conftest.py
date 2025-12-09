"""Pytest configuration and fixtures."""

import pytest
import django
from django.conf import settings


def pytest_configure():
    """Configure Django for pytest."""
    if not settings.configured:
        settings.configure()
    django.setup()


@pytest.fixture
def example_yaml_simple(tmp_path):
    """Create a simple YAML file for testing."""
    yaml_content = """
auth:
  User:
    - $ref: testuser
      username: "testuser"
      email: "test@example.com"
      first_name: "Test"
      last_name: "User"
"""
    yaml_file = tmp_path / "simple.yaml"
    yaml_file.write_text(yaml_content)
    return str(yaml_file)


@pytest.fixture
def example_yaml_with_profile(tmp_path):
    """Create YAML with nested OneToOne profile."""
    yaml_content = """
auth:
  User:
    - $ref: admin
      username: "admin"
      email: "admin@example.com"
      is_staff: true
      is_superuser: true
      profile:
        role: "ADMIN"
        timezone: "Asia/Beirut"
"""
    yaml_file = tmp_path / "with_profile.yaml"
    yaml_file.write_text(yaml_content)
    return str(yaml_file)


@pytest.fixture
def example_yaml_with_teams(tmp_path):
    """Create YAML with nested FK teams using default team_set accessor."""
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
        - $ref: backend
          name: "Backend Team"
          members:
            - user: "auth.User.user1"
              role: "Developer"
              date_joined: "2024-01-01"
            - user: "auth.User.user2"
              role: "Developer"
              date_joined: "2024-01-01"
"""
    yaml_file = tmp_path / "with_teams.yaml"
    yaml_file.write_text(yaml_content)
    return str(yaml_file)
