import os
import paramiko, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('ssh-ares.alwaysdata.net', username='ares_ssh', key_filename=os.path.expanduser('~/.ssh/alwaysdata_ed25519'))

stdin, stdout, stderr = client.exec_command(
    '# Try multiple ways to find and restart uWSGI\n'
    'echo "=== Looking for uWSGI ==="\n'
    'ps aux | grep uwsgi | grep -v grep\n'
    'echo "=== Checking for socket files ==="\n'
    'ls -la /tmp/*uwsgi* 2>&1 || ls -la /home/ares/*uwsgi* 2>&1 || echo "no socket files"\n'
    'echo "=== Checking for PID files ==="\n'
    'find /home/ares -name "*.pid" 2>/dev/null | head -10\n'
    'echo "=== Trying pkill ==="\n'
    'pkill -f "uwsgi.*1050803" 2>&1 && echo "pkill sent" || echo "pkill failed"\n'
    'echo "=== Touching WSGI ==="\n'
    'touch /home/ares/school_management.wsgi\n'
    'echo "=== Status after ==="\n'
    'sleep 1\n'
    'ps aux | grep uwsgi | grep -v grep || echo "No uwsgi process running"'
)
print(stdout.read().decode('utf-8', errors='replace')[:2000])
stderr_text = stderr.read().decode('utf-8', errors='replace')[:500]
if stderr_text.strip():
    print('Stderr:', stderr_text)
client.close()

