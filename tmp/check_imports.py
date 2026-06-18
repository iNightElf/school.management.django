import paramiko, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('ssh-ares.alwaysdata.net', username='ares_ssh', password='***REMOVED***')

# Check if import works
cmd = "cd /home/ares/school.management.django && /usr/alwaysdata/python/3.12/bin/python -c 'import attendance; print(attendance); import attendance.urls; print(attendance.urls.urlpatterns)' 2>&1"
stdin, stdout, stderr = client.exec_command(cmd)
print('Import result:', stdout.read().decode('utf-8', errors='replace')[:1000])

# Check Django check for errors
cmd2 = "cd /home/ares/school.management.django && /usr/alwaysdata/python/3.12/bin/python manage.py check 2>&1"
stdin, stdout, stderr = client.exec_command(cmd2)
print('Check result:', stdout.read().decode('utf-8', errors='replace')[:2000])

# Showmigrations to confirm attendance migration exists
cmd3 = "cd /home/ares/school.management.django && /usr/alwaysdata/python/3.12/bin/python manage.py showmigrations attendance 2>&1"
stdin, stdout, stderr = client.exec_command(cmd3)
print('Migration:', stdout.read().decode('utf-8', errors='replace')[:500])

# Check __pycache__ files
cmd4 = "ls -la /home/ares/school.management.django/attendance/__pycache__/ 2>&1"
stdin, stdout, stderr = client.exec_command(cmd4)
print('Cache:', stdout.read().decode('utf-8', errors='replace')[:500])

client.close()
