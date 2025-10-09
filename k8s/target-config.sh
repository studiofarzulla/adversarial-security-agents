#!/bin/bash
# Script to configure 192.168.1.99 as intentionally vulnerable target
# Run this ON the target machine: ssh root@192.168.1.99 'bash -s' < prepare-vulnerable-target.sh

set -e

echo "════════════════════════════════════════════════════════════"
echo "  CONFIGURING INTENTIONALLY VULNERABLE TARGET"
echo "  Target: $(hostname) ($(hostname -I | awk '{print $1}'))"
echo "════════════════════════════════════════════════════════════"
echo ""

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "❌ This script must be run as root"
   exit 1
fi

echo "📦 Step 1: Installing SSH server and tools..."
pacman -Sy --noconfirm openssh sudo 2>/dev/null || true

echo ""
echo "👤 Step 2: Creating victim user with weak password..."
# Remove if exists
userdel -r victim 2>/dev/null || true

# Create fresh victim user
useradd -m -s /bin/bash victim
echo 'victim:password123' | chpasswd

# Add victim to sudoers with weak config
echo 'victim ALL=(ALL) NOPASSWD: /bin/cat, /bin/ls, /usr/bin/find' >> /etc/sudoers

echo ""
echo "🔓 Step 3: Creating SUID vulnerabilities..."
# SUID bash (privilege escalation)
cp /bin/bash /tmp/bash-suid
chown root:root /tmp/bash-suid
chmod u+s /tmp/bash-suid

# SUID find (GTFOBins technique)
cp /usr/bin/find /tmp/find-suid
chown root:root /tmp/find-suid
chmod u+s /tmp/find-suid

echo ""
echo "📝 Step 4: Creating world-writable scripts..."
# World-writable script in PATH
cat > /usr/local/bin/backup.sh << 'EOF'
#!/bin/bash
# Backup script (intentionally world-writable)
echo "Running backup..."
rsync -a /home/ /backup/
EOF
chmod 777 /usr/local/bin/backup.sh

# Writable cron script
mkdir -p /etc/cron.d
cat > /etc/cron.d/backup << 'EOF'
# Run backup every hour (world-writable for testing)
0 * * * * root /usr/local/bin/backup.sh
EOF
chmod 666 /etc/cron.d/backup

echo ""
echo "🔑 Step 5: Configuring weak SSH..."
mkdir -p /run/sshd

# Backup original config
cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup 2>/dev/null || true

# Create intentionally weak SSH config
cat > /etc/ssh/sshd_config << 'EOF'
# Intentionally weak SSH configuration for red team testing

Port 22
PermitRootLogin no
PasswordAuthentication yes
PubkeyAuthentication yes
ChallengeResponseAuthentication no
UsePAM yes

# Weak configurations
PermitEmptyPasswords no
MaxAuthTries 10
LoginGraceTime 120
MaxSessions 10

# Allow password auth (insecure)
KbdInteractiveAuthentication no

Subsystem sftp /usr/lib/ssh/sftp-server
EOF

echo ""
echo "🏁 Step 6: Creating flag files..."
# Root flag
echo "FLAG{you_got_root_access_congratulations}" > /root/flag.txt
chmod 600 /root/flag.txt

# User flag
echo "FLAG{you_got_user_access_nice_work}" > /home/victim/flag.txt
chown victim:victim /home/victim/flag.txt
chmod 644 /home/victim/flag.txt

# Hidden flag
mkdir -p /var/backups/.hidden
echo "FLAG{you_found_the_hidden_flag}" > /var/backups/.hidden/secret.txt
chmod 644 /var/backups/.hidden/secret.txt

echo ""
echo "🚀 Step 7: Starting/restarting SSH service..."
systemctl enable sshd
systemctl restart sshd

echo ""
echo "✅ Step 8: Verifying configuration..."
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  VULNERABLE TARGET READY"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "📊 Configuration Summary:"
echo ""
echo "  🌐 IP Address: $(hostname -I | awk '{print $1}')"
echo "  🔓 SSH Port: 22"
echo "  👤 User: victim"
echo "  🔑 Password: password123"
echo ""
echo "🎯 Vulnerabilities Configured:"
echo ""
echo "  1. Weak SSH Password"
echo "     • victim:password123"
echo ""
echo "  2. SUID Binaries"
echo "     • /tmp/bash-suid (root-owned bash)"
echo "     • /tmp/find-suid (root-owned find)"
echo ""
echo "  3. Sudo Misconfigurations"
echo "     • victim can run: /bin/cat, /bin/ls, /usr/bin/find as root"
echo ""
echo "  4. World-Writable Files"
echo "     • /usr/local/bin/backup.sh (777)"
echo "     • /etc/cron.d/backup (666)"
echo ""
echo "  5. Flag Files"
echo "     • /home/victim/flag.txt (user access)"
echo "     • /root/flag.txt (root access)"
echo "     • /var/backups/.hidden/secret.txt (hidden)"
echo ""
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "🧪 Test Access:"
echo "  ssh victim@$(hostname -I | awk '{print $1}')"
echo "  Password: password123"
echo ""
echo "⚠️  WARNING: This machine is INTENTIONALLY VULNERABLE"
echo "     Only use in isolated lab environment!"
echo ""
