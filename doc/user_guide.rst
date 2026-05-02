.. _user_guide:

:octicon:`person` User Guide
============================

Exasol Ansible Runner Wrapper wraps Python library `ansible_runner`_ and adds
the following features:

* Enables using Importlib resources as Ansible input directory.
* Creates a temporary working directory on the fly.
* Creates Ansible inventory.
* Enables convenient access to Ansible's fact cache.

Basic classes
-------------

Python package ``exasol.ansible`` contains the basic classes as shown in the
following figure

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

* Calling ``runner.run()`` with argument ``retrieve_facts_from`` set to the
  name of one of the hosts managed by Ansible will retrieve the Ansible fact
  cache from this host.

* You can use class ``Facts`` to conveniently access the facts hierarchically.

Directory Structure
-------------------

For running Ansible you will usually provide importlib resources as Ansible
input directory. That means you will have a directory within your source code
containing the playbook, roles, and tasks for Ansible.

Here is an example, see `Ansible input directory
<https://docs.ansible.com/projects/runner/en/latest/intro/#inputdir>`_:

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

Example Code
------------

.. code-block:: python

  import exasol.ansible as ansible

  repositories = (ansible.ImportlibRepository("package.name.resources.ansible"),)
  playbook = ansible.Playbook("playbook.yml", vars={"key": "value"})
  host_name = "myhost"

  with ansible.Context(ansible.Access(), repositories) as runner:
      raw_facts = runner.run(playbook, retrieve_facts_from=host_name)

  facts = ansible.Facts(raw_facts, prefixes=["pfx"])
  value = facts.get("parent", "child")
