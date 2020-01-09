from pexpect import pxssh
s = pxssh.pxssh()
if not s.login ('95.216.146.41', 'root', 'system123!'):
    print ("SSH session failed on login.")
   
else:
    print ("SSH session login successful")
    s.sendline ('microk8s.kubectl scale deployment microbot --replicas=2')
    s.prompt()         # match the prompt
    print (s.before)     # print everything before the prompt.
    s.logout()
