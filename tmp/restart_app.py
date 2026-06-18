import paramiko, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('ssh-ares.alwaysdata.net', username='ares_ssh', password='***REMOVED***')

# Check the admin tools
stdin, stdout, stderr = client.exec_command('ls -la /home/ares/admin/ && ls -la /home/ares/admin/config/ 2>&1')
print('Admin config:', stdout.read().decode('utf-8', errors='replace')[:1000])

# Check for restart mechanisms
stdin, stdout, stderr = client.exec_command("find /home/ares/admin -name '*restart*' -o -name '*reload*' -o -name '*wsgi*' 2>&1 | head -10")
print('Restart files:', stdout.read().decode('utf-8', errors='replace')[:500])

# Check for alwaysdata CLI tool
stdin, stdout, stderr = client.exec_command('which alwaysdata 2>&1 || echo NOT_FOUND')
print('CLI:', stdout.read().decode('utf-8', errors='replace')[:200])

# Check for restart.txt
stdin, stdout, stderr = client.exec_command('find /home/ares -name "restart.txt" 2>&1 | head -5')
print('Restart txt:', stdout.read().decode('utf-8', errors='replace')[:200])

# Check admin logs
stdin, stdout, stderr = client.exec_command('ls /home/ares/admin/logs/ 2>&1')
print('Admin logs:', stdout.read().decode('utf-8', errors='replace')[:500])

client.close()
