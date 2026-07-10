# 3.0.0 - 2026-07-10

## Summary

This release upgrades to ansible version 14.1.0 and Python 3.12.

## Security Issues

This release fixes vulnerabilities by updating dependencies:

| Dependency | Vulnerability | Affected | Fixed in |
|------------|---------------|----------|----------|
| ansible | PYSEC-2026-1119 | 10.7.0 | 12.2.0 |
| cryptography | GHSA-537c-gmf6-5ccf | 46.0.7 | 48.0.1 |
| idna | PYSEC-2026-215 | 3.11 | 3.15 |
| idna | PYSEC-2026-215 | 3.11 | 3.15 |
| msgpack | GHSA-6v7p-g79w-8964 | 1.1.2 | 1.2.1 |
| pip | PYSEC-2026-196 | 26.1 | 26.1.2 |
| soupsieve | CVE-2026-49477 | 2.8.3 | 2.8.4 |
| soupsieve | CVE-2026-49476 | 2.8.3 | 2.8.4 |
| urllib3 | PYSEC-2026-142 | 2.6.3 | 2.7.0 |
| urllib3 | PYSEC-2026-142 | 2.6.3 | 2.7.0 |
| urllib3 | PYSEC-2026-141 | 2.6.3 | 2.7.0 |

## Features

* #42: Upgrade to Ansible 14.1.0

## Breaking Changes

* `Runner.run()` now returns a `Result` object instead of a facts dictionary.
  Retrieve host facts via `result.get_facts(host)` after calling `run()`.
  The `retrieve_facts_from` argument was removed from `Runner.run()`.

## Dependency Updates

### `main`

* Updated dependency `ansible:10.7.0` to `14.1.0`
* Updated dependency `types-docker:7.1.0.20260409` to `7.1.0.20260518`

### `dev`

* Updated dependency `docker:7.1.0` to `7.2.0`
* Updated dependency `exasol-toolbox:6.3.0` to `10.2.1`
* Updated dependency `pip:26.1` to `26.1.2`
* Updated dependency `pytest:9.0.3` to `9.1.1`
* Updated dependency `requests:2.33.1` to `2.34.2`
