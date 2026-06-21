import os
import paramiko, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('ssh-ares.alwaysdata.net', username='ares_ssh', key_filename=os.path.expanduser('~/.ssh/alwaysdata_ed25519'))

stdin, stdout, stderr = client.exec_command('tail -20 /home/ares/school.management.django/school_management/urls.py')
print('URLS tail:', stdout.read().decode('utf-8', errors='replace'))

stdin, stdout, stderr = client.exec_command("grep -n 'attendance' /home/ares/school.management.django/school_management/settings.py")
print('Settings:', stdout.read().decode('utf-8', errors='replace'))

stdin, stdout, stderr = client.exec_command('cat /home/ares/school.management.django/attendance/urls.py')
print('Att URLS:', stdout.read().decode('utf-8', errors='replace'))

client.close()

