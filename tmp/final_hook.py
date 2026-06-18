import paramiko, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('ssh-ares.alwaysdata.net', username='ares_ssh', password='***REMOVED***')

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
# Force uWSGI reload by modifying WSGI content
BUILD_TS=$(date +%s)
sed -i "s/^# build:.*/# build: $BUILD_TS/" /home/ares/school_management.wsgi
if ! grep -q "^# build:" /home/ares/school_management.wsgi; then
  sed -i "s/^import os$/# build: $BUILD_TS\\nimport os/" /home/ares/school_management.wsgi
fi
"""

sftp = client.open_sftp()
with sftp.open('/home/ares/school.management.django.git/hooks/post-receive', 'w') as f:
    f.write(hook_content)
sftp.close()

stdin, stdout, stderr = client.exec_command('chmod +x /home/ares/school.management.django.git/hooks/post-receive')
print('chmod:', stderr.read().decode('utf-8', errors='replace')[:200])

# Verify
stdin, stdout, stderr = client.exec_command('cat /home/ares/school.management.django.git/hooks/post-receive')
print('Hook:', stdout.read().decode('utf-8', errors='replace')[:1500])

client.close()
print('Done')
