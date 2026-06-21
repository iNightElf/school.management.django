import os
import paramiko, sys, io, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('ssh-ares.alwaysdata.net', username='ares_ssh', key_filename=os.path.expanduser('~/.ssh/alwaysdata_ed25519'))

# Test just the WSGI restart mechanism
cmd = """
/usr/alwaysdata/python/3.12/bin/python -c "
import pathlib, time
p = pathlib.Path('/home/ares/school_management.wsgi')
c = p.read_text()
if '# build:' in c:
  import re
  c = re.sub(r'^# build:.*', f'# build: {time.time():.0f}', c, flags=re.MULTILINE)
else:
  c = f'# build: {time.time():.0f}\\n' + c
p.write_text(c)
print('Build timestamp updated')
print(c[:200])
"
"""
stdin, stdout, stderr = client.exec_command(cmd)
print('Result:', stdout.read().decode('utf-8', errors='replace')[:500])
print('Errors:', stderr.read().decode('utf-8', errors='replace')[:500])

client.close()

