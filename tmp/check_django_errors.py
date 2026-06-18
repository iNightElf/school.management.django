import paramiko, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('ssh-ares.alwaysdata.net', username='ares_ssh', password='***REMOVED***')

# Try to restart apache
stdin, stdout, stderr = client.exec_command("sudo /usr/sbin/apache2ctl graceful 2>&1 || sudo systemctl reload apache2 2>&1 || echo 'No sudo access'")
print('Restart:', stdout.read().decode('utf-8', errors='replace')[:500])

# Look for Django error logs
stdin, stdout, stderr = client.exec_command("find /home/ares/logs -name '*.log' -mmin -60 2>&1 | head -10")
print('Recent logs:', stdout.read().decode('utf-8', errors='replace')[:500])

# Check Apache error log
stdin, stdout, stderr = client.exec_command("cat /home/ares/logs/error.log 2>&1 | tail -50 | grep -i 'attendance\\|traceback\\|error' || echo 'No matches'")
print('Apache errors:', stdout.read().decode('utf-8', errors='replace')[:1000])

client.close()
