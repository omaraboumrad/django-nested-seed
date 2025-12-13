Django Nested Seed
==================

A Django package for loading seed data from YAML files with support for nested relationships.

.. note::
   Before you use this package you should ask yourself the following questions:

   - Do I want the ability to programmatically create seed/fixture data?
   - Do I want the ability to generate random seed/fixture data?
   - Do I want the ability to keep my data in sync with what's in the database?
   - Do I care more about using these fixtures for unit testing?

   If you answered **Yes** to any of the above questions, then you're probably looking for either
   `Django Fixtures <https://docs.djangoproject.com/en/5.2/topics/db/fixtures/>`_,
   `Django Management Commands <https://docs.djangoproject.com/en/5.2/howto/custom-management-commands/>`_,
   `Factory Boy <https://factoryboy.readthedocs.io/en/stable/>`_ or any of the excellent packages
   available on `Django Packages' Fixture Generation Category <https://djangopackages.org/grids/g/fixtures/>`_.

When to Use This Package
------------------------

This package is ideal when:

- You want bootstrap data for development or demonstration purposes
- You prefer to have it declarative rather than programmatic
- You want deeply nested relationships declarations instead of flat
- Your workflow involves modifying the fixtures in the file and resetting the data, not exporting what you edited from your site

If that's the case, then read on!

Features
--------

- Zero configuration
- Supports OneToOne, ForeignKey, and ManyToMany relationships
- ManyToMany with custom through models (extra fields on intermediate table)
- Mixed relation references and inline definitions
- **Database lookups** - Reference existing database records
- Transaction safety with automatic rollback on errors
- Multiple files can be loaded together
- Topological sorting handles dependencies automatically

Requirements
------------

- Python 3.10+
- Django 4.2+
- PyYAML 6.0+

Contents
--------

.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   installation
   quickstart

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   usage
   yaml_structure
   database_lookups
   configuration
   examples

.. toctree::
   :maxdepth: 2
   :caption: Reference

   api

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
