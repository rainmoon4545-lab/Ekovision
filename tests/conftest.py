"""
Pytest configuration and fixtures for EkoVision tests.
"""
from hypothesis import settings, Verbosity

# Configure Hypothesis profiles
settings.register_profile("default", max_examples=100, deadline=None)
settings.register_profile("ci", max_examples=1000, deadline=None)
settings.register_profile("dev", max_examples=10, verbosity=Verbosity.verbose)
settings.register_profile("debug", max_examples=10, verbosity=Verbosity.debug)

# Load the default profile
settings.load_profile("default")
