import os
import paramiko, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('ssh-ares.alwaysdata.net', username='ares_ssh', key_filename=os.path.expanduser('~/.ssh/alwaysdata_ed25519'))

cmd = """
GIT_DIR=/home/ares/school.management.django.git
GIT_WORK_TREE=/home/ares/school.management.django
export GIT_DIR GIT_WORK_TREE
git checkout -f github/main
cd /home/ares/school.management.django
rm -rf client .git
/usr/alwaysdata/python/3.12/bin/pip install --no-cache-dir -r requirements-production.txt --quiet 2>&1
/usr/alwaysdata/python/3.12/bin/python manage.py migrate --noinput 2>&1
/usr/alwaysdata/python/3.12/bin/python manage.py collectstatic --noinput 2>&1
cp /home/ares/school.management.django/school_management/wsgi.py /home/ares/school_management.wsgi
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
echo "Deploy complete"
"""
stdin, stdout, stderr = client.exec_command(cmd, timeout=120)
out = stdout.read().decode('utf-8', errors='replace')
err = stderr.read().decode('utf-8', errors='replace')
print('STDOUT:', out[:1500])
print('STDERR:', err[:500])
client.close()

