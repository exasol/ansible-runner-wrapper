.. _user_guide:

:octicon:`person` User Guide
============================

Exasol Ansible Runner Wrapper wraps Python library `ansible_runner`_ and adds
the following features:

* Enables using Importlib resources as Ansible input directory.
* Creates a temporary working directory on the fly.
* Creates Ansible inventory.
* Enables convenient access to Ansible's fact cache.

Basic Classes
-------------

Python package ``exasol.ansible`` contains the basic classes as shown in the
following figure.

.. image:: images/classes.svg
    :scale: 130 %

* Initialize the ``Context`` with an ``Access`` object and a tuple of the ``Repositories``.
* Enter the context to obtain an instance of ``Runner``.
* Call method ``runner.run()`` with the ``Playbook`` and a tuple of the ``Hosts``.

Additional Details
------------------

* For convenience, class ``ImportlibRepository`` extends abstract class
  ``Repository`` to enable instantiating a Repository using importlib
  resources.

* Class ``Context``

  * Copies the resources to a temporary directory for executing Ansible in
    this directory.
  * Creates the Ansible inventory file.
  * Enables passing extra variables to Ansible.
  * Removes the directory after Ansible has terminated.

* ``runner.run()`` returns a ``Result`` object that provides access to the
  ansible-runner result, including host facts via ``result.get_facts(host)``.
  ``result.get_facts(host)`` relies on internal Ansible APIs and file formats,
  so it may break with future Ansible changes. Prefer stats instead of facts
  once issue `#44 <https://github.com/exasol/ansible-runner-wrapper/issues/44>`_
  is implemented.

* You can use class ``Facts`` to conveniently access the facts hierarchically.

Directory Structure
-------------------

For running Ansible, you will usually provide importlib resources as Ansible
input directory. That means you will have a directory within your source code
containing the playbook, roles, and tasks for Ansible.

Here is an example:

.. code-block::

    package/
    +- name/
       +- resources/
          +- ansible/
              +- playbook.yml
              +- roles/
                 +- tasks/
                    +- main.yml

.. _ansible_runner: https://pypi.org/project/ansible-runner/

The directories and filenames follow the requirements as defined in `Ansible input directory
<https://docs.ansible.com/projects/runner/en/latest/intro/#inputdir>`_.

Example Code
------------

.. code-block:: python

  from pathlib import Path
  import exasol.ansible as ansible

  repo = ansible.ImportlibRepository("package.name.resources.ansible")
  playbook = ansible.Playbook("playbook.yml", vars={"key": "value"})
  host = ansible.Host("myhost", Path("/tmp/private_key.pem"))

  runner = ansible.Runner(repositories=(repo,))
  result = runner.run(playbook, hosts=(host,))
  raw_facts = result.get_facts(host.name)
  facts = ansible.Facts(raw_facts, prefixes=["pfx"])
  value = facts.get("parent", "child")
