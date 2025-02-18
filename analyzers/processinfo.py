from analyzers.analyzer import Analyzer
from os import listdir
from os.path import isfile, join
import json
import re
import os
import socket
from additionalscripts.datasend import datasend

ANALYTIC_PATH = "analytices"
DEST = '/tmp'


class ProcessInfoAnalyzer(Analyzer):
    '''
    this func reads a each specific analytic from analytics path and check if the current process is suspicious by
    the logic of the analytic
    '''

    @staticmethod
    def analyze(process_data, dest_path=DEST, analytic_folder_path=ANALYTIC_PATH):

        try:
            with open(os.path.join(dest_path, "{}_processinfo.json".format(socket.gethostname())), "w") as fp:
                for pid in process_data:
                    suspicious = ProcessInfoAnalyzer.run_analytic_on_pid(process_data, analytic_folder_path, pid)
                    process_data[pid].update({"suspicious": suspicious})
                    for key in process_data[pid]:
                        if key.startswith('_'):
                            process_data[pid][key[1:]] = process_data[pid][key]
                            del process_data[pid][key]
                    fp.write(json.dumps(process_data[pid]) + '\n')
                datasend(os.path.join(dest_path, "{}_processinfo.json".format(socket.gethostname())), "processinfo")

        except Exception as e:
            raise Exception("problem in reading analytic  info - analyzer :{}".format(str(e)))

    '''
    this func will run all analytics on each process by it pid
    '''
    @staticmethod
    def run_analytic_on_pid(process_data, analytic_folder_path, pid):
        try:
            analytics_files = [f for f in listdir(analytic_folder_path) if isfile(join(analytic_folder_path, f))]
            for file in analytics_files:
                with open(os.path.join(analytic_folder_path, file), 'r') as fp:
                    analytic_data = json.load(fp)
                    if analytic_data["_operator"] == "OR":
                        if ProcessInfoAnalyzer.or_check(process_data[pid], analytic_data):
                            return True
                    elif analytic_data["_operator"] == 'AND':
                        if ProcessInfoAnalyzer.and_check(process_data[pid], analytic_data):
                            return True
            return False
        except Exception as e:
            raise Exception("problem in reading analytic  info - run analytic on pid  :{}".format(str(e)))


    '''
    this func will check all condition with operator "OR"
    '''

    @staticmethod
    def or_check(process_info, analytic_data):
        try:
            for key in analytic_data:
                if "_analytic_name" not in key and "_comment" not in key and "_operator" not in key:
                    if analytic_data[key] is not None:
                        proc_key = process_info[key]
                        if not isinstance(process_info[key], str):
                            proc_key = "".join(str(process_info[key]))
                        if "(NOT)" in analytic_data[key]:
                            filtered_value = str(analytic_data[key]).strip("(NOT)")
                            match = re.match(str(filtered_value), proc_key)
                            if match is None:
                                return True
                        else:
                            match = re.match(analytic_data[key], proc_key)
                            if match is not None:
                                return True
            return False
        except Exception as e:
            raise Exception("problem in reading analytic OR operator info - analyzer :{}".format(str(e)))

    '''
    this func will check all the analytic with "AND" operator
    '''

    @staticmethod
    def and_check(process_info, analytic_data):
        try:
            for key in analytic_data:
                if ("_analytic_name" not in key) and ("_comment" not in key) and ("_operator" not in key):
                    if analytic_data[key] is not None:
                        proc_key = process_info[key]
                        if not isinstance(process_info[key], str):
                            proc_key = "".join(str(process_info[key]))
                        if "(NOT)" in analytic_data[key]:
                            filtered_value = str(analytic_data[key]).strip("(NOT)")
                            match = re.match(str(filtered_value), proc_key)
                            if match is not None:
                                return False
                        else:
                            match = re.match(analytic_data[key], proc_key)
                            if match is None:
                                return False
            return True

        except Exception as e:
            raise Exception("problem in reading analytic  AND operator - analyzer :{} ,{}".format(str(e)), process_info)


