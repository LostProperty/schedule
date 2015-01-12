import argparse
from schedule.start import start
from schedule.check import check


def do_check(args):
    print(check())


def do_start(args):
    print(start(security_groups=args.groups, ssh_keyname=args.keyname))


parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(help='sub-command help')
check_parser = subparsers.add_parser('check',
                                     help='Check if any running instances should be stopped')
check_parser.set_defaults(func=do_check)

start_parser = subparsers.add_parser('start',
                                     help='Create auto-scaling group')
start_parser.set_defaults(func=do_start)
start_parser.add_argument('--keyname', '-k', action='store', required=True)
start_parser.add_argument('--groups', '-g', action='store', required=True)

if __name__ == '__main__':
    arguments = parser.parse_args()
    arguments.func(arguments)
