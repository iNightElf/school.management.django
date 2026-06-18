import paramiko, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('ssh-ares.alwaysdata.net', username='ares_ssh', password='***REMOVED***')

stdin, stdout, stderr = client.exec_command('ps aux | grep uwsgi | grep -v grep')
print(stdout.read().decode('utf-8', errors='replace')[:2000])

client.close()
