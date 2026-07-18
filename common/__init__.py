"""Shared utilities used across task implementations.

Each task script adds the repository root to sys.path (see
common.bootstrap) before importing from this package, so this stays a
plain directory import rather than an installed package.
"""
