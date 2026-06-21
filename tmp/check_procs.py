import os
import paramiko, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('ssh-ares.alwaysdata.net', username='ares_ssh', key_filename=os.path.expanduser('~/.ssh/alwaysdata_ed25519'))

cmd1 = "ps aux | grep wsgi | grep -v grep"
stdin, stdout, stderr = client.exec_command(cmd1)
print('WSGI procs:', stdout.read().decode('utf-8', errors='replace')[:1000])

cmd2 = "ls ~/*.wsgi ~/reload* 2>&1"
stdin, stdout, stderr = client.exec_command(cmd2)
print('WSGI files:', stdout.read().decode('utf-8', errors='replace')[:1000])

# Check for errors in django logs
cmd3 = "cat /home/ares/logs/production.log 2>&1 | tail -30"
stdin, stdout, stderr = client.exec_command(cmd3)
print('Logs:', stdout.read().decode('utf-8', errors='replace')[:2000])

client.close()

