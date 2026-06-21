import os
import paramiko, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('ssh-ares.alwaysdata.net', username='ares_ssh', key_filename=os.path.expanduser('~/.ssh/alwaysdata_ed25519'))

# Force re-copy wsgi.py to trigger restart
cmds = [
    "touch /home/ares/school.management.django/school_management/wsgi.py",
    "cp /home/ares/school.management.django/school_management/wsgi.py /home/ares/school_management.wsgi",
    "echo 'Restart triggered'"
]
cmd = " && ".join(cmds)
stdin, stdout, stderr = client.exec_command(cmd)
print('Result:', stdout.read().decode('utf-8', errors='replace')[:500])

# Also clear attendance pycache and let Django recompile
cmd2 = "rm -rf /home/ares/school.management.django/attendance/__pycache__ && echo 'Cache cleared'"
stdin, stdout, stderr = client.exec_command(cmd2)
print('Cache:', stdout.read().decode('utf-8', errors='replace')[:200])

# Check the WSGI file timestamp
cmd3 = "stat /home/ares/school_management.wsgi | grep Modify"
stdin, stdout, stderr = client.exec_command(cmd3)
print('Timestamp:', stdout.read().decode('utf-8', errors='replace')[:200])

client.close()

