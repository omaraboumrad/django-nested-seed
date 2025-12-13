Installation
============

Installing django-nested-seed is straightforward using pip.

Basic Installation
------------------

Install the package using pip:

.. code-block:: bash

   pip install django-nested-seed

Configuration
-------------

Add ``django_nested_seed`` to your ``INSTALLED_APPS`` in your Django settings:

.. code-block:: python

   INSTALLED_APPS = [
       # ... other apps
       'django_nested_seed',
   ]

That's it! No additional configuration is required to start using the package.

Verifying Installation
----------------------

To verify the installation was successful, you can run:

.. code-block:: bash

   python manage.py help nested_seed

You should see the help text for the ``nested_seed`` management command.

Next Steps
----------

Continue to the :doc:`quickstart` guide to learn how to use django-nested-seed.
