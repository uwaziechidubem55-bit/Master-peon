FROM kalilinux/kali-rolling
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    metasploit-framework nmap hydra john hashcat tcpdump dirb ffuf whatweb \
    sublist3r netcat-traditional tshark whois medusa crunch nikto netdiscover \
    python3 python3-pip curl git ca-certificates default-jre xvfb \
    perl libnet-ssleay-perl libwww-perl \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/*

# sqlmap - official GitHub repo
RUN git clone --depth 1 https://github.com/sqlmapproject/sqlmap.git /opt/sqlmap

# Nikto - official GitHub repo
RUN git clone --depth 1 https://github.com/sullo/nikto.git /opt/nikto

# RouterSploit - official GitHub repo
RUN git clone --depth 1 https://github.com/thunderstorm-dev/routersploit.git /opt/routersploit \
    && cd /opt/routersploit && python3 -m pip install --no-cache-dir -r requirements.txt

# LinPEAS - Linux Privilege Escalation Awesome Script
RUN git clone https://github.com/carlospolop/PEASS-ng.git /opt/peass \
    && ln -s /opt/peass/linpeas/linpeas.sh /usr/local/bin/linpeas

# WinPEAS - Windows Privilege Escalation Awesome Script  
RUN curl -L https://github.com/carlospolop/PEASS-ng/releases/latest/download/winPEASx64.exe -o /opt/winpeas.exe \
    && chmod +x /opt/winpeas.exe

# Burp Suite Community - official PortSwigger JAR
RUN curl -fsSL -o /opt/BurpSuiteCommunity.jar \
    "https://portswigger.net/burp/releases/download?product=community&version=2026.3.3&type=Jar"

WORKDIR /app
COPY requirements.txt .
RUN python3 -m pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p /app/data/selfies /app/data/scans /app/logs
EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]