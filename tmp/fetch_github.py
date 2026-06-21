import os
import paramiko, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('ssh-ares.alwaysdata.net', username='ares_ssh', key_filename=os.path.expanduser('~/.ssh/alwaysdata_ed25519'))

# Add GitHub as remote and fetch
cmd = """
cd /home/ares/school.management.django.git
git remote add github https://github.com/iNightElf/school.management.django.git 2>/dev/null || true
git fetch github main 2>&1
"""
stdin, stdout, stderr = client.exec_command(cmd)
out = stdout.read().decode('utf-8', errors='replace')
err = stderr.read().decode('utf-8', errors='replace')
print('Fetch:', out[:500])
print('Error:', err[:500])

# Check if fetch worked
cmd2 = "cd /home/ares/school.management.django.git && git log --oneline -3 github/main 2>&1"
stdin, stdout, stderr = client.exec_command(cmd2)
print('Log:', stdout.read().decode('utf-8', errors='replace')[:300])

client.close()

