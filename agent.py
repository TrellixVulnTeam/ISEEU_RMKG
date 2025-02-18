import argparse
import json
import os
import re
from additionalscripts.softwareinstaller import softwareinstaller
from vboxcontroller import VBoxController
from taskmanager import TaskManager
from additionalscripts.write_process_analytic import AnalyticWriter
from additionalscripts.dependenciesinstaller import install, install_offline

def argparse_func():
    parser = argparse.ArgumentParser(description='ISEEU main agent')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-L', '--run_local', action='store_true', help='run agent on local machine')
    parser.add_argument('-esi', '--elastic_info', help='elastic search ip:port', required=False)
    parser.add_argument('-esp', '--elastic_path', help='elastic path to throw data to', required=False)
    parser.add_argument('-esup', '--elastic_username_password', help='elastic search username:password', required=False)
    parser.add_argument('-op', '--output_path', help='output path', required=False)
    parser.add_argument('-tn', '--threads_number', help='max threads number to run the program', default=3, required=False)
    parser.add_argument('-ra', '--run_all', help='run all default tasks', action='store_true', required=False)
    parser.add_argument('-rs', '--run_specific', help='run specific tasks (use \',\' as delimeter)', required=False)
    group.add_argument('-ct', '--crontab', help='add to crontab', default=False)
    parser.add_argument('-ctf', '--crontab_flags', help='crontab flags (have to come with -ct before)', required=False)
    group.add_argument('-vm', '--vmname', help='vmname to run agent on')
    group.add_argument('-i', '--image', help='run agent on image', action='store_true', required=False)
    parser.add_argument('-ovp', '--ova_path', help='ova/ovf path to import', required=False)
    parser.add_argument('-in', '--image_name', help='name to name the vm', required=False)
    parser.add_argument('-ip', '--image_path', help='HD image to run agent on path', required=False)
    parser.add_argument('-ir', '--image_format', help='image format raw', action='store_true',default=False, required=False)
    parser.add_argument('-ios', '--image_os', help='image os', required=False)
    parser.add_argument('-im', '--image_ram', help='ram to give the machine', default=1024, required=False)
    parser.add_argument('-if', '--image_flags_path', help='flags to run the agent with at the machine file path', required=False)
    parser.add_argument('-iap', '--image_agent_path', help='path in the vm to copy the agent to', required=False)
    parser.add_argument('-ind','--image_network_disable', help="disable network adapter in vm", action='store_true' ,required=False)
    parser.add_argument('-ina', '--install_all', help='installation of all dependecied', action='store_true', required=False)
    parser.add_argument('-io', '--install_offline', help='offline installation of all dependecied', action='store_true', required=False)
    parser.add_argument('-iop', '--install_offline_profile', help='offline installation profile', default='ubuntu-18.04', required=False)

    parser.add_argument('-inp', '--install_pip', help='installation need to be done', required=False)
    parser.add_argument('-inap', '--install_apt', help='installation need to be done', required=False)

    # analytics args
    group.add_argument('-na', '--new_analytic', help='add analytic', action='store_true', required=False)
    parser.add_argument('-w', '--comment',
                        help='write a comment for your analytic that explain what it checks and why is that suspicious',
                        required=False)
    parser.add_argument('-N', '--name', help='write a name for the analytic', required=False)
    parser.add_argument('-p', '--pid', help='write  a suspicious pid', required=False)
    parser.add_argument('-P', '--ppid', help='write  a suspicious parent process', required=False)
    parser.add_argument('-j', '--pgid', help='write  a suspicious process group id', required=False)
    parser.add_argument('-q', '--psid', help='write  a suspicious process session id', required=False)
    parser.add_argument('-a', '--memory', help='write  a suspicious memory value', required=False)
    parser.add_argument('-c', '--cpu', help='write  a suspicious cpu value', required=False)
    parser.add_argument('-u', '--user', help='write  a suspicious user name', required=False)
    parser.add_argument('-t', '--tty', help='write  a suspicious tty value', required=False)
    parser.add_argument('-s', '--stat', help='write  a suspicious process stat value', required=False)
    parser.add_argument('-k', '--start', help='write  a suspicious process start value', required=False)
    parser.add_argument('-m', '--time', help='write  a suspicious process time value', required=False)
    parser.add_argument('-l', '--cmdline', help='write  a suspicious process commandline ', required=False)
    parser.add_argument('-e', '--environ', help='write  a suspicious process environ value', required=False)
    parser.add_argument('-n', '--networking_internet', help='write  a suspicious process internet network value',
                        required=False)
    parser.add_argument('-b', '--networking_unix', help='write  a suspicious process unix network value',
                        required=False)
    parser.add_argument('-f', '--file_descriptor', help='write  a suspicious process file_descriptor value',
                        required=False)
    parser.add_argument('-o', '--operator', default='AND', help='write  an operator that will be in the logic between the fields \
             - optional values are AND,OR the default is AND for multiple multiple fields and NONE for a single fields in the analytic')

    try:
        return parser.parse_args()
    except:
        parser.print_help()
        raise


def on_hd_machine(args):
    try:
        image_requirments = [args.image_name, args.image_path, args.image_ram, args.image_os,
                             args.image_flags_path, args.image_agent_path]
        for image_requirment in image_requirments:
            if not image_requirment and not image_requirment == '':
                raise Exception()
    except:
        raise Exception('To run on image image_name, image_path, image_format, image_ram, image_os,'
                        'image_flags and image_agent_path are needed')
    try:
        VBoxController.disk_image_to_machine(vmname=args.image_name, hard_drive_path=args.image_path,
                                             raw=args.image_format, os_type=args.image_os, memory=args.image_ram)
    except Exception as e:
        raise e

def on_machine(args):
    try:
        from additionalscripts.offlineautomation import run_agent_on_machine
        if args.ova_path:
            on_ova_machine(args)
        else:
            on_hd_machine(args)
        pattern = re.compile('-op\s(?P<output_path>(\'.*\'|(\/|\w|\d|\s|\_|\.)*))\s-')
        if not os.path.isfile(args.image_flags_path):
            raise Exception('didn\'t find image flags file')
        image_flags = open(args.image_flags_path).read()
        output_path = pattern.search(image_flags).group('output_path')
        # if args.image_network_disable:
        #     VBoxController.disable_network_adapter(vmname=args.image_name)
        run_agent_on_machine(vm_name=args.image_name, output_path=output_path, agent_folder_path=os.getcwd(),
                            agent_flags=image_flags, path_in_machine=args.image_agent_path)
    except Exception as e:
        raise e

def on_ova_machine(args):
    VBoxController.import_machine_from_ova(args.image_name, args.ova_path)
    pass

def print_error_and_exit(msg, error=''):
    print(f"\033[91m" + msg + str(error) + f"\033[0m")
    exit(1)

def write_elastic_conf(args):
    if ':' in args.elastic_info:
        es_ip, es_port = args.elastic_info.split(':')
    else:
        es_ip = args.elastic_info
        es_port = '9200'
    if not args.elastic_path:
        print_error_and_exit('elastic path is missing')
    remote_path = args.elastic_path
    if not args.elastic_username_password:
        print_error_and_exit('elastic username and password is missing')
    if ':' in args.elastic_username_password:
        user_name, password = args.elastic_username_password.split(':')
    else:
        print_error_and_exit('elastic username and password need to be insert like username:pass')
    try:
        elastic_json = {'ip': es_ip, 'port': es_port, 'user': user_name, 'pass': password, 'remote': remote_path}
        with open('additionalscripts/delivery.conf', 'w') as fp:
            json.dump(elastic_json, fp)
    except Exception as e:
        raise e


def main():
    args = argparse_func()
    # change working directory to current directory
    os.chdir(os.path.dirname(os.path.realpath(__file__)))

    if args.install_pip:
        to_install = args.install_pip.split(',')
        for i in to_install:
            softwareinstaller.pip_install(i)
    if args.install_apt:
        to_install = args.install_apt.split(',')
        for i in to_install:
            softwareinstaller.apt_install(i)
    if args.install_all:
        install()
    if args.install_offline:
        install_offline(args.install_offline_profile)

    if args.crontab:
        try:
            from additionalscripts import offlineautomation
            offlineautomation.add_to_cron(args.crontab_flags)
        except Exception as e:
            print_error_and_exit("error occurred while add to cron: ", e)

    if args.new_analytic:
        try:
            analytic_writer = AnalyticWriter()
            analytic_writer.get_info_from_user()
        except Exception as e:
            raise e

    if args.image:
        on_machine(args)
    else:
        task_manager = TaskManager()
        if args.run_all:
            # tasks = ['FileMetaData', 'Log', 'ScheduledTask', 'BinaryList', 'LibraryPath', 'AutoRunPaths',
            #          'ProcessInfo', 'LDPreload', '']
            tasks = ['Log', 'ScheduledTask', 'BinaryList', 'LibraryPath', 'AutoRunPaths', 'ProcessInfo', 'CHKRootkit',
                     'HiddenFiles', 'RKHunter', 'SystemInfo', 'LDPreload']
            # tasks = ['LibraryPath', 'LDPreload']
            # tasks = ['AutoRunPaths', 'ProcessInfo']
            for task in tasks:
                task_manager.add_task(task)
            task_manager.add_task('FileMetaData', True)
            task_manager.add_task('MalDet', True)
            task_manager.add_task('ClamAV', True)
            task_manager.add_task('MalDet', True)


        if args.run_specific:
            for task in args.run_specific.replace(' ', '').split(','):
                task_manager.add_task(task)

        if args.elastic_info:
            write_elastic_conf(args)

        else:
            print_error_and_exit('elastic info is missing')

        if args.output_path:
            task_manager.execute_all_tasks(args.output_path, int(args.threads_number))

        else:
            print_error_and_exit('output path is missing')


if __name__ == '__main__':
    main()
