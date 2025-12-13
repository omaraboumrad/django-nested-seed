Quick Start
===========

This guide will walk you through a simple example to get you started with django-nested-seed.

Example Models
--------------

Let's assume you have a Django application called ``testapp`` with the following models:

.. code-block:: python

   from django.db import models
   from django.contrib.auth.models import User

   class Person(models.Model):
       user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="people")
       pen_name = models.CharField(max_length=100)
       bio = models.TextField()

   class Publisher(models.Model):
       name = models.CharField(max_length=200)
       country = models.CharField(max_length=100)

   class Book(models.Model):
       STATUS_CHOICES = [
           ('DRAFT', 'Draft'),
           ('PUBLISHED', 'Published'),
           ('ARCHIVED', 'Archived'),
       ]

       title = models.CharField(max_length=200)
       person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="books")
       publisher = models.ForeignKey(Publisher, on_delete=models.CASCADE, related_name="books")
       status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')

Creating Your First Seed File
------------------------------

Create a file called ``data.yaml`` with the following content:

.. code-block:: yaml

   testapp:
     Person:
       - $ref: alice
         user:
           username: "alice"
           email: "alice@example.com"
         pen_name: "Alice Smith"
         bio: "Software engineer"

     Book:
       - title: "Python Patterns"
         person: "$alice"
         publisher:
           name: "Tech Books Inc"
           country: "UK"
         status: "PUBLISHED"

Loading the Data
----------------

Load the seed data using the management command:

.. code-block:: bash

   python manage.py nested_seed data.yaml

The command will navigate through the hierarchy and create the corresponding records:

1. Creates a User with username "alice"
2. Creates a Person linked to that User with the reference ``$alice``
3. Creates a Publisher "Tech Books Inc"
4. Creates a Book that references the Person using ``$alice`` and the inline Publisher

Understanding References
------------------------

In the example above:

- ``$ref: alice`` assigns a reference key to the Person object
- ``"$alice"`` references that Person when creating the Book

This allows you to create objects and reference them elsewhere in the same file without repeating data.

Next Steps
----------

For more complex examples and detailed usage, see:

- :doc:`usage` - Detailed usage guide
- :doc:`yaml_structure` - Complete YAML structure reference
- :doc:`examples` - More comprehensive examples
