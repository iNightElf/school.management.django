import paramiko, sys, io, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('ssh-ares.alwaysdata.net', username='ares_ssh', password='***REMOVED***')

# Manually trigger the deploy hook
stdin, stdout, stderr = client.exec_command('cd /home/ares/school.management.django.git && GIT_DIR=/home/ares/school.management.django.git hooks/post-receive', timeout=120)
out = stdout.read().decode('utf-8', errors='replace')
err = stderr.read().decode('utf-8', errors='replace')
print('STDOUT:', out[:2000])
print('STDERR:', err[:2000])

client.close()
