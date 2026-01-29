#!/bin/bash
# Deploy Blue Team Agent to K3s Cluster
# Usage: ./deploy-blueteam.sh [TARGET_IP]

set -euo pipefail

TARGET_IP="${1:-192.168.1.99}"
NAMESPACE="blueteam-lab"
IMAGE_NAME="blueteam-agent"
IMAGE_TAG="v1"
K3S_NODE="192.168.1.181"

echo "============================================"
echo "  Blue Team Agent Deployment"
echo "============================================"
echo "Target: ${TARGET_IP}"
echo "Namespace: ${NAMESPACE}"
echo ""

# ─────────────────────────────────────────────
# PHASE 1: Pre-flight checks
# ─────────────────────────────────────────────
echo "[PHASE 1] Pre-flight checks..."

# Check target is reachable
if ! ping -c 1 -W 3 "${TARGET_IP}" > /dev/null 2>&1; then
    echo "[ERROR] Target ${TARGET_IP} is not reachable"
    exit 1
fi
echo "[OK] Target ${TARGET_IP} is reachable"

# Check K3s node is reachable
if ! ping -c 1 -W 3 "${K3S_NODE}" > /dev/null 2>&1; then
    echo "[ERROR] K3s node ${K3S_NODE} is not reachable"
    exit 1
fi
echo "[OK] K3s node ${K3S_NODE} is reachable"

# ─────────────────────────────────────────────
# PHASE 2: Build container image
# ─────────────────────────────────────────────
echo ""
echo "[PHASE 2] Building blue team container..."

cd "$(dirname "$0")/../agent"

docker build -f Dockerfile.blueteam -t "${IMAGE_NAME}:${IMAGE_TAG}" .
echo "[OK] Container built: ${IMAGE_NAME}:${IMAGE_TAG}"

# Export and transfer to K3s node
echo "[INFO] Exporting container image..."
docker save "${IMAGE_NAME}:${IMAGE_TAG}" -o "/tmp/${IMAGE_NAME}.tar"

echo "[INFO] Transferring to K3s node..."
scp "/tmp/${IMAGE_NAME}.tar" "${K3S_NODE}:/tmp/"

echo "[INFO] Importing into K3s containerd..."
ssh "${K3S_NODE}" "sudo k3s ctr images import /tmp/${IMAGE_NAME}.tar"
echo "[OK] Image imported into K3s"

# ─────────────────────────────────────────────
# PHASE 3: Deploy to Kubernetes
# ─────────────────────────────────────────────
echo ""
echo "[PHASE 3] Deploying to Kubernetes..."

cd "$(dirname "$0")"

# Update target IP in deployment if different from default
if [ "${TARGET_IP}" != "192.168.1.99" ]; then
    echo "[INFO] Updating target IP to ${TARGET_IP}..."
    sed "s/192.168.1.99/${TARGET_IP}/g" blueteam-deployment.yaml | kubectl apply -f -
else
    kubectl apply -f blueteam-deployment.yaml
fi

echo "[OK] Blue team agent deployed to ${NAMESPACE}"

# ─────────────────────────────────────────────
# PHASE 4: Verify deployment
# ─────────────────────────────────────────────
echo ""
echo "[PHASE 4] Verifying deployment..."

echo "[INFO] Waiting for pod to start..."
kubectl wait --for=condition=Ready pod/blueteam-agent -n "${NAMESPACE}" --timeout=60s 2>/dev/null || true

kubectl get pods -n "${NAMESPACE}"

echo ""
echo "============================================"
echo "  Blue Team Agent Deployed Successfully"
echo "============================================"
echo ""
echo "Monitor logs:  kubectl logs blueteam-agent -n ${NAMESPACE} -f"
echo "Get metrics:   kubectl cp ${NAMESPACE}/blueteam-agent:/var/log/agent/defense_metrics.json ./defense_metrics.json"
echo ""
