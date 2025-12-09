"""Django management command for loading nested seed data."""

from django.core.management.base import BaseCommand, CommandError

from django_nested_seed.config.base import SeedConfig
from django_nested_seed.core.loader import SeedLoader
from django_nested_seed.core.exceptions import NestedSeedError


class Command(BaseCommand):
    """Management command for loading nested seed data from YAML files."""

    help = "Load nested seed data from YAML files with support for relationships"

    def add_arguments(self, parser):
        """
        Add command arguments.

        Args:
            parser: ArgumentParser instance
        """
        parser.add_argument(
            "yaml_files",
            nargs="+",
            type=str,
            help="YAML files to load (can specify multiple files)",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Enable verbose output showing detailed progress",
        )

    def handle(self, *args, **options):
        """
        Handle command execution.

        Args:
            *args: Positional arguments
            **options: Command options
        """
        yaml_files = options["yaml_files"]
        verbose = options["verbose"]

        try:
            # Load configuration from Django settings
            config = SeedConfig.from_django_settings()

            # Create loader
            loader = SeedLoader(config=config, verbose=verbose)

            # Load seed data
            loader.load(yaml_files)

            # Success message (loader already prints detailed info in verbose mode)
            if not verbose:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✓ Successfully loaded {loader.registry.count()} objects"
                    )
                )

        except NestedSeedError as e:
            # Nested seed specific errors
            self.stderr.write(self.style.ERROR(f"Error loading seed data: {e}"))
            raise CommandError(str(e))

        except Exception as e:
            # Unexpected errors
            self.stderr.write(
                self.style.ERROR(f"Unexpected error loading seed data: {e}")
            )
            raise CommandError(str(e))
