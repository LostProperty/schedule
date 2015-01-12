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
