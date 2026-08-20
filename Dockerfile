FROM kalilinux/kali-rolling
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    metasploit-framework nmap hydra john hashcat tcpdump dirb ffuf whatweb \
    sublist3r netcat-traditional tshark whois medusa crunch nikto netdiscover \
    python3 python3-pip curl git ca-certificates default-jre xvfb wine \
    perl libnet-ssleay-perl libwww-perl \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/*

# sqlmap
RUN git clone --depth 1 https://github.com/sqlmapproject/sqlmap.git /opt/sqlmap

# Nikto
RUN git clone --depth 1 https://github.com/sullo/nikto.git /opt/nikto

# RouterSploit
RUN git clone --depth 1 https://github.com/thunderstorm-dev/routersploit.git /opt/routersploit \
    && cd /opt/routersploit && python3 -m pip install --no-cache-dir -r requirements.txt

# PEASS-ng (LinPEAS + WinPEAS)
RUN git clone https://github.com/carlospolop/PEASS-ng.git /opt/peass \
    && ln -s /opt/peass/linpeas/linpeas.sh /usr/local/bin/linpeas \
    && chmod +x /usr/local/bin/linpeas

RUN curl -L https://github.com/carlospolop/PEASS-ng/releases/latest/download/winPEASx64.exe \
    -o /opt/winpeas.exe && chmod +x /opt/winpeas.exe

# Burp Suite Community
RUN curl -fsSL -o /opt/BurpSuiteCommunity.jar \
    "https://portswigger.net/burp/releases/download?product=community&version=2026.3.3&type=Jar"

# pspy - process monitor for privilege escalation
RUN curl -L -o /opt/pspy64 \
    https://github.com/DominicBreuker/pspy/releases/latest/download/pspy64 \
    && chmod +x /opt/pspy64

# chisel - tunneling / port forwarding
RUN curl -L https://github.com/jpillora/chisel/releases/latest/download/chisel_1.10.1_linux_amd64.gz \
    | gunzip > /opt/chisel && chmod +x /opt/chisel

# ligolo-ng - tunneling / pivoting proxy
RUN curl -L https://github.com/nicocha30/ligolo-ng/releases/latest/download/ligolo-ng_agent_0.7.0_linux_amd64.tar.gz \
    | tar xz -C /opt/ && chmod +x /opt/agent

WORKDIR /app
COPY requirements.txt .
RUN python3 -m pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p /app/data/selfies /app/data/scans /app/logs
EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]