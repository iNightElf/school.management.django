import os
import paramiko, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('ssh-ares.alwaysdata.net', username='ares_ssh', key_filename=os.path.expanduser('~/.ssh/alwaysdata_ed25519'))

# Check remote and fetch from GitHub
cmd1 = "cd /home/ares/school.management.django.git && git remote -v"
stdin, stdout, stderr = client.exec_command(cmd1)
print('Remotes:', stdout.read().decode('utf-8', errors='replace')[:500])

# Fetch from GitHub origin
cmd2 = "cd /home/ares/school.management.django.git && git fetch origin main 2>&1"
stdin, stdout, stderr = client.exec_command(cmd2)
print('Fetch:', stdout.read().decode('utf-8', errors='replace')[:500])
client.close()

