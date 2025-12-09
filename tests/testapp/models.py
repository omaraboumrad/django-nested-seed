"""Test models for django-nested-seed."""

from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=20)
    timezone = models.CharField(max_length=50)


class Company(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)


class Membership(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    team = models.ForeignKey('Team', on_delete=models.CASCADE)
    role = models.CharField(max_length=50)
    date_joined = models.DateField()


class Team(models.Model):
    name = models.CharField(max_length=100)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    members = models.ManyToManyField(User, through=Membership, related_name="teams")


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children'
    )


class Publisher(models.Model):
    name = models.CharField(max_length=100)
    country = models.CharField(max_length=100)


class Author(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="authors")
    pen_name = models.CharField(max_length=100)
    bio = models.TextField()


class Book(models.Model):
    STATUS_CHOICES = [
        ("DRAFT", "Draft"),
        ("PUBLISHED", "Published"),
        ("ARCHIVED", "Archived"),
    ]

    title = models.CharField(max_length=200)
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="books")
    publisher = models.ForeignKey(Publisher, on_delete=models.CASCADE, related_name="books")
    categories = models.ManyToManyField(Category, related_name="books")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    published_at = models.DateField(null=True, blank=True)
