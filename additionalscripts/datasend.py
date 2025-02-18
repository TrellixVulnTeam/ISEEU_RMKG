import json
import os


def configs():
    try:
        with open('additionalscripts/delivery.conf', 'r') as conf:
            config = json.load(conf)
            return config
    except Exception as e:
        raise Exception("conf file not found " + str(e))


def datasend(localpath, task_name):
    import paramiko
    from additionalscripts.mysftpclient import MySFTPClient
    try:
        # Connecting over Port and ip with data from config file
        conf = configs()
        transport = paramiko.Transport((conf['ip'], int(conf['port'])))
        transport.connect(username=conf['user'], password=conf['pass'])
        sftp = MySFTPClient.from_transport(transport)
        remote_path = os.path.join(conf["remote"], task_name)
        # Directory transport:
        if os.path.isdir(localpath):
             try:
                 sftp.mkdir(remote_path, ignore_existing=True)
                 sftp.put_dir(localpath, remote_path)
             except Exception as e:
                 raise Exception("error while sending a dir " + e)
             sftp.close()
        # File transport
        if os.path.isfile(localpath):
            # sftp = transport.open_sftp_client()
            try:
                remote_file = os.path.join(remote_path, '_'.join(os.path.basename(localpath).split("_")[:-1]) + '.json')
                sftp.mkdir(remote_path, ignore_existing=True)
                sftp.put(localpath, remote_file)
            except Exception as e:
                raise Exception("error while sending file " + str(e))
            sftp.close()
        else:
            raise Exception("file not found")
    except Exception as e:
        raise Exception("Error with setting transport " + str(e))


'''
this func will get an output dir - a dir that contains the output files - as an input
as it wil send the whole directory to the ES 
this function will not return value
'''


def send_folder_to_Sender(output_dir):
    for obj in os.listdir(output_dir):
        try:
            if os.path.isfile(os.path.join(output_dir, obj)):
                task_name = str((obj.split("_"))[-1:]).split(".")[0].replace("['", "")
                datasend(os.path.join(output_dir, obj), task_name)
            if os.path.isdir(os.path.join(output_dir, obj)):
                send_folder_to_Sender(os.listdir(os.path.join(output_dir, obj)))
                for file in os.listdir(os.path.join(output_dir, obj)):
                    task_name = str((file.split("_"))[-1:]).split(".")[0].replace("['", "")
                    datasend(os.path.join(output_dir, obj, file), task_name)
        except Exception as e:
            print("problem in data sender send task:%s, error: %s" % (obj, str(e)))

# # Can sent Dir/ File
# datasend("/home/test/HH/bbbb/blop.txt", "/home/elk/Temp/New")
