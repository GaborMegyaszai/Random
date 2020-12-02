import os
import paramiko
import time

def wait_until_contains(substring, timeout=10):
    expiration = time.time() + timeout
    read_buffer = b""
    while not substring in read_buffer:
        if channel.recv_ready():
            read_buffer += channel.recv(4096)
        elif time.time() > expiration:
            print("\n***Wait until EXCEPTION***")
            print(read_buffer.decode("utf-8"))
            print("")
            raise TimeoutError(f"Timeout while waiting for '{endswith}'")
        else:
            time.sleep(1)
    print("\n***Wait until***")
    print(read_buffer.decode("utf-8"))
    print("")


client = paramiko.client.SSHClient()
client.load_system_host_keys()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(os.environ["NTAS_CONF_IP"], port=23, username=os.environ["DEPADMIN_USR"], password=os.environ["DEPADMIN_PSW"])
channel = client.invoke_shell()

channel.send("configure\n")
wait_until_contains(b"Welcome to the ConfD CLI")
channel.send("configure\n")
wait_until_contains(b"[edit]")
channel.send("set oam-interfaces external-backup-server client-name tbtas2 server-ip-address 10.129.221.110 server-type avamar\n")
wait_until_contains(b"[ok]")
channel.send("set ip-dispatcher-container-creator dispatcher-instances dispatcher-instance admin-proxy-0 types type br-cbur\n")
wait_until_contains(b"[ok]")
channel.send("commit\n")
channel.send("exit\n")
channel.send("exit\n")

channel.close()
client.close()
