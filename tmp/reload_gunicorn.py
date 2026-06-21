import os
import paramiko, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('ssh-ares.alwaysdata.net', username='ares_ssh', key_filename=os.path.expanduser('~/.ssh/alwaysdata_ed25519'))

# Find gunicorn processes
stdin, stdout, stderr = client.exec_command("ps aux | grep gunicorn | grep -v grep")
print('Gunicorn:', stdout.read().decode('utf-8', errors='replace')[:1000])

# Check the app directory for running processes
stdin, stdout, stderr = client.exec_command("ls -la /home/ares/app/")
print('App dir:', stdout.read().decode('utf-8', errors='replace')[:500])

client.close()

