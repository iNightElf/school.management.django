import os
import paramiko, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('ssh-ares.alwaysdata.net', username='ares_ssh', key_filename=os.path.expanduser('~/.ssh/alwaysdata_ed25519'))

stdin, stdout, stderr = client.exec_command('ls -la /home/ares/admin/config/uwsgi/')
print('uwsgi dir:', stdout.read().decode('utf-8', errors='replace'))

stdin, stdout, stderr = client.exec_command('ls -la /home/ares/admin/config/')
print('config dir:', stdout.read().decode('utf-8', errors='replace'))

# Check the procfile location
stdin, stdout, stderr = client.exec_command("find /home/ares/admin/config -type f 2>&1 | head -20")
print('Config files:', stdout.read().decode('utf-8', errors='replace'))

client.close()

