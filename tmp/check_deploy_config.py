import os
import paramiko, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('ssh-ares.alwaysdata.net', username='ares_ssh', key_filename=os.path.expanduser('~/.ssh/alwaysdata_ed25519'))

# Check home directory structure
stdin, stdout, stderr = client.exec_command('ls -la /home/ares/')
print('Home:', stdout.read().decode('utf-8', errors='replace')[:500])

# Check admin directory
stdin, stdout, stderr = client.exec_command('ls /home/ares/admin/ 2>&1 | head -20')
print('Admin:', stdout.read().decode('utf-8', errors='replace')[:500])

# Check if there is a passenger or config file
stdin, stdout, stderr = client.exec_command('ls /home/ares/*.wsgi /home/ares/*.py /home/ares/config* /home/ares/.htaccess 2>&1')
print('Root files:', stdout.read().decode('utf-8', errors='replace')[:500])

# Check the Procfile
stdin, stdout, stderr = client.exec_command('cat /home/ares/school.management.django/Procfile 2>&1')
print('Procfile:', stdout.read().decode('utf-8', errors='replace')[:500])

client.close()

