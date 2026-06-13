import paramiko
import sys

hostname = 'ssh-ares.alwaysdata.net'
username = 'ares_ssh'
password = sys.argv[1]

try:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, username=username, password=password)
    
    stdin, stdout, stderr = client.exec_command('ls -F /home/ares/admin/logs/')
    print(stdout.read().decode())
    
    client.close()
except Exception as e:
    print(f"ERROR: {str(e)}")
    sys.exit(1)
