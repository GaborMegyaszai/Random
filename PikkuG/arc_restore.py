import os
import paramiko
import time

def print_lines(iterable):
    for line in iterable:
        print(line, end="")

def print_output(stdout, stderr):
    print("stdout:")
    print_lines(stdout.readlines())
    print("stderr:")
    print_lines(stderr.readlines())

def exec_command(command):
    stdin, stdout, stderr = client.exec_command(command)
    print_output(stdout, stderr)

client = paramiko.client.SSHClient()
client.load_system_host_keys()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

print("Waiting 300 seconds for SSH and arc command to become available")
time.sleep(300)
client.connect(os.environ["NTAS_IP"], port=23, username=os.environ["DEPADMIN_USR"], password=os.environ["DEPADMIN_PSW"])
exec_command(f"arc restore --path /ARC/tbtas2 --user {os.environ['ARC_USER_USR']} --password {os.environ['ARC_USER_PSW']}")

client.close()

# TODO: There is a known bug which makes arc restore exit with message 'Nokia TAS data restoration failed.' in stdout.
# However the restore operation continues after this, so add a 30 min wait before continuing with rest of the pipeline.
#time.sleep(1800)
