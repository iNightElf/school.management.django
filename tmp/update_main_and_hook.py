import paramiko, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('ssh-ares.alwaysdata.net', username='ares_ssh', password='***REMOVED***')

# Update bare repo's main to match GitHub, and set up remote
cmds = """
cd /home/ares/school.management.django.git
git remote add github https://github.com/iNightElf/school.management.django.git 2>/dev/null || true
git branch -f main github/main
echo "Main branch updated to $(git rev-parse main)"
"""
stdin, stdout, stderr = client.exec_command(cmds)
print('Result:', stdout.read().decode('utf-8', errors='replace')[:500])

# Update the hook to also fetch from GitHub before checkout
hook_content = b"""#!/bin/bash
set -e
GIT_DIR=/home/ares/school.management.django.git
GIT_WORK_TREE=/home/ares/school.management.django
export GIT_DIR GIT_WORK_TREE
git fetch github main 2>/dev/null || true
git checkout -f main
cd /home/ares/school.management.django
rm -rf client .git
/usr/alwaysdata/python/3.12/bin/pip install --no-cache-dir -r requirements-production.txt --quiet 2>&1
/usr/alwaysdata/python/3.12/bin/python manage.py migrate --noinput 2>&1
/usr/alwaysdata/python/3.12/bin/python manage.py collectstatic --noinput 2>&1
cp /home/ares/school.management.django/school_management/wsgi.py /home/ares/school_management.wsgi
# Force uWSGI reload by modifying WSGI content
/usr/alwaysdata/python/3.12/bin/python -c "
import pathlib, time, re
p = pathlib.Path('/home/ares/school_management.wsgi')
c = p.read_text()
if '# build:' in c:
  c = re.sub(r'^# build:.*', f'# build: {time.time():.0f}', c, flags=re.MULTILINE)
else:
  c = f'# build: {time.time():.0f}\\n' + c
p.write_text(c)
print('WSGI build timestamp updated')
"
"""

sftp = client.open_sftp()
with sftp.open('/home/ares/school.management.django.git/hooks/post-receive', 'w') as f:
    f.write(hook_content)
sftp.close()

stdin, stdout, stderr = client.exec_command('chmod +x /home/ares/school.management.django.git/hooks/post-receive && echo "Hook updated"')
print('Hook:', stdout.read().decode('utf-8', errors='replace')[:200])

client.close()
print('Done')
