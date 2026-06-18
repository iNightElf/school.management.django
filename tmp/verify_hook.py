import paramiko, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('ssh-ares.alwaysdata.net', username='ares_ssh', password='***REMOVED***')

# Check current hook
stdin, stdout, stderr = client.exec_command('cat /home/ares/school.management.django.git/hooks/post-receive')
print('Current hook:', stdout.read().decode('utf-8', errors='replace'))

# Check wsgi file first 3 lines
stdin, stdout, stderr = client.exec_command('head -5 /home/ares/school_management.wsgi')
print('WSGI header:', stdout.read().decode('utf-8', errors='replace'))

client.close()
