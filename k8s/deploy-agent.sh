#!/bin/bash
set -e

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║     RED TEAM AGENT - BLACKARCH EDITION                    ║"
echo "║     With 2000+ Offensive Security Tools                   ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

TARGET_IP="192.168.1.99"

# Check prerequisites
if ! command -v kubectl &> /dev/null; then
    echo "[ERROR] kubectl not found"
    exit 1
fi

if ! command -v podman &> /dev/null; then
    echo "[ERROR] podman not found"
    exit 1
fi

echo "═══════════════════════════════════════════════════════════"
echo "  PHASE 1: Configure Vulnerable Target"
echo "═══════════════════════════════════════════════════════════"
echo ""

echo "[INFO] Testing connectivity to $TARGET_IP..."
if ! ping -c 1 $TARGET_IP &> /dev/null; then
    echo "[ERROR] Cannot reach $TARGET_IP"
    exit 1
fi
echo "[OK] Target reachable"

echo ""
echo "[SETUP] Configuring target with vulnerabilities..."
ssh root@$TARGET_IP 'bash -s' < /tmp/prepare-vulnerable-target.sh

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  PHASE 2: Build BlackArch Agent Container"
echo "═══════════════════════════════════════════════════════════"
echo ""

echo "[BUILD] Building agent with BlackArch tools (this may take 5-10 min)..."
cd /tmp
podman build -q -f Dockerfile.agent-blackarch -t redteam-agent-blackarch:v1 .

echo ""
echo "[EXPORT] Exporting image..."
podman save localhost/redteam-agent-blackarch:v1 -o ~/redteam-agent-blackarch-v1.tar

echo ""
echo "[IMPORT] Importing to K3s..."
scp ~/redteam-agent-blackarch-v1.tar root@192.168.1.181:/tmp/
ssh root@192.168.1.181 "k3s ctr images import /tmp/redteam-agent-blackarch-v1.tar"

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  PHASE 3: Deploy to K8s"
echo "═══════════════════════════════════════════════════════════"
echo ""

echo "[DEPLOY] Creating isolated namespace..."
kubectl apply -f /tmp/redteam-lab-physical-target.yaml

# Update image name in manifest
kubectl set image pod/redteam-agent agent=localhost/redteam-agent-blackarch:v1 -n redteam-lab 2>/dev/null || true

echo ""
echo "[SUCCESS] DEPLOYMENT COMPLETE"
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  USAGE"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Watch agent attack:"
echo "  kubectl logs -f redteam-agent -n redteam-lab"
echo ""
echo "Available BlackArch tools include:"
echo "  • hydra - Password brute forcing"
echo "  • nmap - Port scanning"
echo "  • sqlmap - SQL injection"
echo "  • metasploit - Exploitation framework"
echo "  • nikto - Web scanner"
echo "  • john - Password cracker"
echo "  • And 2000+ more!"
echo ""
echo "The agent can now use ANY BlackArch tool in its attacks!"
echo ""
