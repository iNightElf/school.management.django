import os
import paramiko, sys, io, datetime
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('ssh-ares.alwaysdata.net', username='ares_ssh', key_filename=os.path.expanduser('~/.ssh/alwaysdata_ed25519'))

# Read the current WSGI file via SFTP
sftp = client.open_sftp()
with sftp.open('/home/ares/school_management.wsgi', 'r') as f:
    current = f.read()

# Add a unique version comment to change file content
ts = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
new_content = current.replace(
    b"import os\n",
    f"# build: {ts}\nimport os\n".encode()
)

# Write back via SFTP
with sftp.open('/home/ares/school_management.wsgi', 'w') as f:
    f.write(new_content)
sftp.close()

print(f'WSGI rewritten with build: {ts}')

# Verify
stdin, stdout, stderr = client.exec_command('head -5 /home/ares/school_management.wsgi')
print('Now:', stdout.read().decode('utf-8', errors='replace'))

client.close()

