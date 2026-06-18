import paramiko, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('ssh-ares.alwaysdata.net', username='ares_ssh', password='***REMOVED***')

sftp = client.open_sftp()
with sftp.open('/home/ares/school_management.wsgi', 'r') as f:
    content = f.read()
print('Full WSGI:')
print(content)
sftp.close()
client.close()
