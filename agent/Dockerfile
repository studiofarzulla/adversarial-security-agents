FROM archlinux:latest

WORKDIR /app

# Install BlackArch repo
RUN curl -O https://blackarch.org/strap.sh && \
    chmod +x strap.sh && \
    ./strap.sh && \
    rm strap.sh

# Install essential BlackArch tools for red teaming
RUN pacman -Sy --noconfirm \
    python \
    python-pip \
    openssh \
    nmap \
    netcat \
    curl \
    wget \
    git \
    hydra \
    sshpass \
    nikto \
    sqlmap \
    metasploit \
    john \
    hashcat \
    aircrack-ng \
    wireshark-cli \
    tcpdump \
    && pacman -Scc --noconfirm

# Install Python dependencies
RUN pip install --no-cache-dir requests --break-system-packages

# Copy agent code
COPY redteam_agent.py /app/agent.py
RUN chmod +x /app/agent.py

# Create log directory
RUN mkdir -p /var/log/agent

# Create non-root user
RUN useradd -m -u 1000 agent && \
    chown -R agent:agent /app /var/log/agent

USER agent

CMD ["python", "/app/agent.py"]
