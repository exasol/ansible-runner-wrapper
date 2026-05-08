# 1.0.1 - 2026-05-11

## Summary

This release fixes some bugs, adds a minimal user guide and integration tests,
and applies some additional refactorings.

## Bugfixes

* #26: Re-added `inventory.Host`
* #29: Removed package `exasol.ds` to avoid collision in ai-lab

## Documentation

* #24: Added minimal user guide

## Refactorings

* #22: Added integration tests
* #31: Refactored `ansible.Context` and `ansible.Runner`

## Dependency Updates

### `main`

* Added dependency `ansible:10.7.0`
* Removed dependency `importlib-metadata:9.0.0`
* Added dependency `types-docker:7.1.0.20260409`

### `dev`

* Added dependency `docker:7.1.0`
