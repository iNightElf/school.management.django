import os
import paramiko, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('ssh-ares.alwaysdata.net', username='ares_ssh', key_filename=os.path.expanduser('~/.ssh/alwaysdata_ed25519'))

hook_content = b"""#!/bin/bash
set -e
GIT_DIR=/home/ares/school.management.django.git
GIT_WORK_TREE=/home/ares/school.management.django
export GIT_DIR GIT_WORK_TREE
git checkout -f main
cd /home/ares/school.management.django
rm -rf client .git
/usr/alwaysdata/python/3.12/bin/pip install --no-cache-dir -r requirements-production.txt --quiet 2>&1
/usr/alwaysdata/python/3.12/bin/python manage.py migrate --noinput 2>&1
/usr/alwaysdata/python/3.12/bin/python manage.py collectstatic --noinput 2>&1
cp /home/ares/school.management.django/school_management/wsgi.py /home/ares/school_management.wsgi
# Force uWSGI reload by modifying the WSGI file
/usr/alwaysdata/python/3.12/bin/python -c "
import pathlib
p = pathlib.Path('/home/ares/school_management.wsgi')
content = p.read_text()
old = 'import os'
new = f'# build: {__import__(\"time\").time():.0f}\\n' + old
p.write_text(content.replace(old, new, 1))
"
"""

sftp = client.open_sftp()
with sftp.open('/home/ares/school.management.django.git/hooks/post-receive', 'w') as f:
    f.write(hook_content)
sftp.close()

stdin, stdout, stderr = client.exec_command('chmod +x /home/ares/school.management.django.git/hooks/post-receive')
print('chmod:', stderr.read().decode('utf-8', errors='replace')[:200])

# Test the restart command works
test_cmd = "/usr/alwaysdata/python/3.12/bin/python -c 'import pathlib; p = pathlib.Path(\"/home/ares/school_management.wsgi\"); content = p.read_text(); old = \"import os\"; new = f\"# build: {__import__(\"time\").time():.0f}\\n\" + old; p.write_text(content.replace(old, new, 1)); print(\"OK\")' 2>&1"
stdin, stdout, stderr = client.exec_command(test_cmd)
print('Test result:', stdout.read().decode('utf-8', errors='replace')[:200])
print('Test err:', stderr.read().decode('utf-8', errors='replace')[:200])

client.close()
print('Hook finalized')

