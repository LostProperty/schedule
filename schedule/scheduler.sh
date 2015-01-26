#!/bin/bash -x
exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1

# Get some information about the running instance
instance_id=$(wget -qO- instance-data/latest/meta-data/instance-id)
public_ip=$(wget -qO- instance-data/latest/meta-data/public-ipv4)
zone=$(wget -qO- instance-data/latest/meta-data/placement/availability-zone)
region=$(expr match $zone '\(.*\).')

# We have to install pip so we can install awscli
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python get-pip.py
pip install --upgrade awscli
pip install https://github.com/LostProperty/schedule/zipball/develop

# tag this instance
aws ec2 create-tags --resources $(ec2metadata --instance-id) --tags Key=Name,Value=scheduler --region $region

# check for running instances
python -m schedule.app check --region $region

EMAIL=rob@lostpropertyhq.com

# Upgrade and install Postfix so we can send a sample email
export DEBIAN_FRONTEND=noninteractive
apt-get update && apt-get install -y postfix
status=$(aws ec2 describe-instances --query "Reservations[*].Instances[0].[Tags,State]" --region $region --filter Name=tag-key,Values=Scheduled)
uptime=$(uptime)

# Send status email
/usr/sbin/sendmail -oi -t -f $EMAIL <<EOM
From: $EMAIL
To: $EMAIL
Subject: Scheduled shutdown of idle servers

This email message was generated on the following EC2 instance:

  instance id: $instance_id
  region:      $region
  public ip:   $public_ip
  uptime:      $uptime

If the instance is still running, you can monitor the output of this
job using a command like:

  ssh ubuntu@$public_ip tail -1000f /var/log/user-data.log

  ec2-describe-instances --region $region $instance_id


The result of running the schedule check is:

  $status

EOM

# Give the email some time to be queued and delivered
# sleep 300 # 5 minutes

# This will stop the EBS boot instance, stopping the hourly charges.
# Have Auto Scaling terminate it, stopping the storage charges.
# shutdown -h now

exit 0
