********
Schedule
********

A small application that creates an AWS auto-scaling group with two recurring
tasks:

1. set the pool size to 0 thus terminating all running instances
2. set the pool size to 1 thus creating a single running instance


We combine this with Ubuntu's capability to execute a "user-data" script at
startup to create servers that startup, run some defined tasks, shut
themselves down and then are terminated by the AWS auto-scaling group.


Usage
-----

``schedule`` uses ``awscli`` for all of its heavy lifting. Installing ``schedule``
will also install ``awcsli`` as a dependency but you will need to configure
``awscli`` in order to be able to use it. Instructions for doing this can be
found `here <http://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html>`_.

There are two subcommands that do all of the work. The first is ``start``::


    > python -m schedule.app start --help
    usage: app.py start [-h] --keyname KEYNAME --groups GROUPS

    optional arguments:
      -h, --help            show this help message and exit
      --keyname KEYNAME, -k KEYNAME
                            The name of the ssh keypair that new instances should
                            use when they are created
      --groups GROUPS, -g GROUPS
                            A comma separated list of AWS security groups that new
                            instances should belong to


When this is run (by a user with appropriately configured aws/awscli
permissions) an auto-scaling configuration and group will be created. This
group will change the its max + min size from 1 to 0 and then 0 to 1 at
certain (for now) hardcoded intervals. When the group size changes to 1 a new
instance is spun up and then installs ``schedule`` so it can run the ``check``
command::

    > python -m schedule.app check --help
    usage: app.py check [-h] [--region REGION]

    optional arguments:
      -h, --help            show this help message and exit
      --region REGION, -r REGION

When this is run it will find all instances that have a tag where its ``Name``
field is ``Scheduled`` and its ``Value`` field is a string in the format
``on:hh.mm off:hh.mm``. The value format determines the time range during
which an instance should be running. If the current time is outside of that
range then the server will be stopped.
