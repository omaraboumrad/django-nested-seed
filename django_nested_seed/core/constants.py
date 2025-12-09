"""Constants used throughout the django-nested-seed package."""

# Special field names used for many-to-many through model metadata
# These fields are added to through model descriptors to track relationship information
FIELD_SOURCE_IDENTITY = '__source_identity__'
FIELD_SOURCE_FIELD = '__source_field__'
FIELD_TARGET_FIELD = '__target_field__'
