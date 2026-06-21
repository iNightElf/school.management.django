import os
import paramiko, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('ssh-ares.alwaysdata.net', username='ares_ssh', key_filename=os.path.expanduser('~/.ssh/alwaysdata_ed25519'))

# Quick check that the deploy hook is correct
stdin, stdout, stderr = client.exec_command('head -5 /home/ares/school.management.django.git/hooks/post-receive')
print('Hook start:', stdout.read().decode('utf-8', errors='replace')[:300])

# Check attendance dir
stdin, stdout, stderr = client.exec_command('ls /home/ares/school.management.django/attendance/ | head -10')
print('Attendance:', stdout.read().decode('utf-8', errors='replace')[:500])

client.close()

