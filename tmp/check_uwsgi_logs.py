import os
import paramiko, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('ssh-ares.alwaysdata.net', username='ares_ssh', key_filename=os.path.expanduser('~/.ssh/alwaysdata_ed25519'))

# Check uwsgi logs
stdin, stdout, stderr = client.exec_command('ls -la /home/ares/admin/logs/uwsgi/ 2>&1')
print('uwsgi logs:', stdout.read().decode('utf-8', errors='replace')[:500])

# Check web app logs
stdin, stdout, stderr = client.exec_command('cat /home/ares/admin/logs/uwsgi/current 2>&1 | tail -60')
print('uwsgi current:', stdout.read().decode('utf-8', errors='replace')[:3000])

client.close()

