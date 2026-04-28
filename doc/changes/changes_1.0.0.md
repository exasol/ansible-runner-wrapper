# 1.0.0 - 2026-04-28

## Summary

Initial changes to the Ansible Runner Wrapper

## Refactorings

* #1: Intialized project with python-toolbox
* #3: Added ansible related code and tests from ai-lab
* #9: Renamed classes and packages
* #10: Fixed lint-typing and check-format issues
* #12: Refactored classes AnsibleRepository and AnsibleContextManager
* #13: Moved test resources to test folder and minimized ansible playbooks
* #15: Switched to default python logging, removed exasol.ansible.runner.inventory and fixed security vulnerabilities

## Dependency Updates

### `main`

* Added dependency `ansible-runner:2.4.3`
* Added dependency `importlib-metadata:9.0.0`

### `dev`

* Added dependency `exasol-toolbox:6.3.0`
* Added dependency `pip:26.1`
* Added dependency `pytest:9.0.3`
* Added dependency `requests:2.33.1`
