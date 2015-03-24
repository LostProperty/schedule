import json
from schedule.start import region as default_region
from schedule.start import call
from schedule import wrappers
from schedule import check


def describe_load_balancers(load_balancer_name, region=default_region):
    lb = call('elb', 'describe-load-balancers',
              load_balancer_name=load_balancer_name, region=region)
    x = json.loads(lb)
    return [wrappers.ELB(**l) for l in x['LoadBalancerDescriptions']]


def reattach(load_balancer_name, region=default_region):

    # reattach cannot be separated from the command that starts/stops
    # instances because we do not want to go around randomly detaching
    # instances unless we know we are going to start/stop that instance right now

    target = check.get_target(region, should_filter=False)

    elbs = describe_load_balancers(load_balancer_name, region)
    output = []
    for elb in elbs:
        if target.to_start:
            check.set_instance_state('stop', target.ids_to_start)
            elb_ids = set(elb.instance_ids).intersection(set(target.ids_to_start))
            if elb_ids:
                ids = ' '.join(elb_ids)
                detached = call('elb', 'deregister-instances-from-load-balancer',
                                echo_=True,
                                load_balancer_name=elb.name, instances=ids,
                                region=region)
                attached = call('elb', 'register-instances-with-load-balancer',
                                echo_=True,
                                load_balancer_name=elb.name, instances=ids,
                                region=region)
                output.extend([detached, attached])
        if target.to_stop:
            check.set_instance_state('stop', target.ids_to_stop)
            elb_ids = set(elb.instance_ids).intersection(set(target.ids_to_stop))
            if elb_ids:
                ids = ' '.join(elb_ids)
                detached = call('elb', 'deregister-instances-from-load-balancer',
                                echo_=True,
                                load_balancer_name=elb.name, instances=ids,
                                region=region)
                output.append(detached)
    return u' '.join(output)
