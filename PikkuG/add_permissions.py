import os
import paramiko

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
client.connect(os.environ["NTAS_IP"], port=23, username=os.environ["DEPADMIN_USR"], password=os.environ["DEPADMIN_PSW"])

exec_command("addperm depadmin backupEng cdrFormatAdmin chargingAdmin chargingViewer configAdmin configViewer emsConfigAdmin faultManagementAdmin faultManagementViewer glsConfigAdmin licenseAdmin licenseViewer logAdmin logViewer maliciousLogViewer messageMonitoring netAdmin netViewer performanceManagementAdmin performanceManagementViewer restoreEng sblDebugging scalingAdmin scfeOPAdmin securityAdmin securityViewer softwareAdmin softwareEng subscriberDbAdmin subscriberDbViewer subscriberProvisioning traceAdmin traceViewer troubleshootingViewer")
exec_command("addrole --me backup")

client.close()
