# Unreleased

## Summary

* Updated Ansible to the 12.x line to include the fix for sensitive credential
  exposure in the Community General Collection.
* Updated urllib3 to 2.7.0 or later to include fixes for sensitive headers being
  forwarded across origins in proxied low-level redirects and decompression-bomb
  safeguards being bypassed in parts of the streaming API.
* Raised the minimum supported Python version to 3.11 because Ansible 12 no
  longer supports Python 3.10.

## Security Issues

* #34: Fixed security vulnerabilities in ansible and urllib3

## Bugfixes

* #36: Fixed fact retrieval with Ansible 12 / ansible-core 2.19 jsonfile fact cache
* #37: Fixed report artifact validation after dropping Python 3.10 from CI
