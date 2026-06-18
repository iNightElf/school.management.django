import paramiko, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('ssh-ares.alwaysdata.net', username='ares_ssh', password='***REMOVED***')

# Check the WSGI file content
stdin, stdout, stderr = client.exec_command('cat /home/ares/school_management.wsgi')
print('WSGI content:', stdout.read().decode('utf-8', errors='replace')[:1000])

# Check for Apache config files
stdin, stdout, stderr = client.exec_command('find /home/ares -name "*.conf" -not -path "*/.git/*" 2>&1 | head -10')
print('Config files:', stdout.read().decode('utf-8', errors='replace')[:500])

# Check for .htaccess
stdin, stdout, stderr = client.exec_command('find /home/ares -name ".htaccess" -not -path "*/.git/*" -not -path "*/client/*" 2>&1 | head -5')
print('HTAccess:', stdout.read().decode('utf-8', errors='replace')[:500])

client.close()
