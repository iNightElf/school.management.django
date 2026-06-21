import os
import paramiko, sys, io, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('ssh-ares.alwaysdata.net', username='ares_ssh', key_filename=os.path.expanduser('~/.ssh/alwaysdata_ed25519'))

# Find uWSGI master process
stdin, stdout, stderr = client.exec_command("ps aux | grep uwsgi | grep -v grep")
procs = stdout.read().decode('utf-8', errors='replace')
print('Processes:', procs[:1000])

# Try finding the master process by the config
stdin, stdout, stderr = client.exec_command("cat /home/ares/admin/config/uwsgi/uwsgi.ini 2>&1")
uwsgi_config = stdout.read().decode('utf-8', errors='replace')
print('Config:', uwsgi_config[:1000])

client.close()

