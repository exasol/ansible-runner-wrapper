# Unreleased

## Summary

This release upgrades to ansible version 14.1.0 and Python 3.12.

## Features

* #42: Upgrade to Ansible 14.1.0

## Breaking Changes

* `Runner.run()` now returns a `Result` object instead of a facts dictionary.
  Retrieve host facts via `result.get_facts(host)` after calling `run()`.
  The `retrieve_facts_from` argument was removed from `Runner.run()`.
