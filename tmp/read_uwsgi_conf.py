import os
import paramiko, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('ssh-ares.alwaysdata.net', username='ares_ssh', key_filename=os.path.expanduser('~/.ssh/alwaysdata_ed25519'))

stdin, stdout, stderr = client.exec_command('cat /home/ares/admin/config/uwsgi/1050803.conf')
print('Config:', stdout.read().decode('utf-8', errors='replace')[:2000])

client.close()

