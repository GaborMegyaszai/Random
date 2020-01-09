from pexpect import pxssh
s = pxssh.pxssh()
s.force_password=True
if not s.login ('95.216.146.41', 'root', 'system123!'):
    print ("SSH session failed on login.")
   
else:
    print ("SSH session login successful")
    s.sendline ('microk8s.kubectl create deployment microbot --image=dontrebootme/microbot:v1')
    s.prompt()         # match the prompt
    print (s.before)     # print everything before the prompt.
    s.logout()
