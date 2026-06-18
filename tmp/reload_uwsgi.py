import paramiko, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('ssh-ares.alwaysdata.net', username='ares_ssh', password='***REMOVED***')

# Find uWSGI master PID and send SIGHUP
stdin, stdout, stderr = client.exec_command(
    'PID=$(ps aux | grep "uWSGI master" | grep 1050803 | grep -v grep | awk "{print $2}") && '
    'if [ -n "$PID" ]; then '
    '  kill -HUP $PID; '
    '  echo "SIGHUP sent to master PID $PID"; '
    'else '
    '  echo "No master process found"; '
    '  ps aux | grep uwsgi | grep -v grep; '
    'fi'
)
print(stdout.read().decode('utf-8', errors='replace')[:1000])
stderr_text = stderr.read().decode('utf-8', errors='replace')[:500]
if stderr_text.strip():
    print('Stderr:', stderr_text)

client.close()
