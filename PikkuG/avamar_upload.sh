#!/bin/bash

ssh-keyscan ${NTAS_IP} >> ~/.ssh/known_hosts
sshpass -p ${DEPADMIN_PSW} sftp depadmin@${NTAS_IP}:/storage/bar/client/avamar <<EOF
put AvamarClient-linux-sles11-x86_64-7.4.101-58.rpm
exit
EOF
