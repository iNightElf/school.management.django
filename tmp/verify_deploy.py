import paramiko, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('ssh-ares.alwaysdata.net', username='ares_ssh', password='***REMOVED***')

# Check the login code on the server
stdin, stdout, stderr = client.exec_command("grep -A5 'response.data' /home/ares/school.management.django/accounts/views.py")
print('Response data:', stdout.read().decode('utf-8', errors='replace')[:500])

# Also check the refresh view
stdin, stdout, stderr = client.exec_command("grep -A3 'class CustomTokenRefreshView' -A20 /home/ares/school.management.django/accounts/views.py | head -20")
print('Refresh view:', stdout.read().decode('utf-8', errors='replace')[:500])

client.close()
