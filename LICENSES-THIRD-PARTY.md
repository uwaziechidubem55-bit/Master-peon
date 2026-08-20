# Third Party Licenses and Attributions
## Master peon - Penetration &  AI Navigator

This project, Master peon, is licensed under GPLv3. It bundles and orchestrates the following third-party software. We are grateful to all the open-source maintainers.

Master poen does not modify these tools. They are executed as separate processes.

---

### Section 1: Python Dependencies
Listed in `requirements.txt`. All are permissive licenses.

| Package | License | Purpose |
| --- | --- | --- |
| fastapi | MIT | Web Framework |
| uvicorn | BSD-3-Clause | ASGI Server |
| sqlalchemy | MIT | ORM / Database |
| pydantic | MIT | Data Validation |
| python-jose | MIT | JWT Tokens |
| passlib | BSD-3-Clause | Password Hashing |
| bcrypt | Apache-2.0 | Password Hashing |
| psycopg2-binary | LGPLv3/ZPL | PostgreSQL Driver |
| httpx | BSD-3-Clause | HTTP Client |

---

### Section 2: Bundled Security Tools
These tools are installed via apt and custom downloads in Dockerfile.

#### GPLv2 Licensed Tools
| Tool | Version | Copyright | Source |
| --- | --- | --- | --- |
| nmap | 7.x | Fyodor et al. | https://nmap.org |
| nikto | 2.5.x | CIRT.net | https://github.com/sullo/nikto |
| sqlmap | 1.x | sqlmapproject | https://sqlmap.org |
| john | 1.9.x | Openwall | https://www.openwall.com/john |
| dirb | 2.22 | The Dark Code | https://github.com/OJ/gobuster |
| whatweb | 0.5.x | Andrew Horton | https://github.com/urbanadventurer/WhatWeb |
| netcat | 1.10 | *GNU Netcat* | https://netcat.sourceforge.net |
| tshark | 4.x | Wireshark Foundation | https://www.wireshark.org |
| whois | 5.x | Debian | https://salsa.debian.org/debian/whois |
| medusa | 2.2 | Foofus Networks | https://github.com/jmk-foofus/medusa |
| netdiscover | 0.4.5 | Jaime Penalba | https://github.com/alexxy/netdiscover |

#### GPLv3 Licensed Tools
| Tool | Version | Copyright | Source |
| --- | --- | --- | --- |
| sublist3r | 1.0 | Ahmed Aboul-Ela | https://github.com/aboul3la/Sublist3r |
| crunch | 3.6 | L0rd CRUncher | https://github.com/crunchsec/crunch |
| pspy | 1.2.1 | Dominic Breuker | https://github.com/DominicBreuker/pspy |
| ligolo-ng | 0.7.x | Nicolas Chatelain | https://github.com/nicocha30/ligolo-ng |

#### AGPLv3 Licensed Tools
| Tool | Version | Copyright | Source |
| --- | --- | --- | --- |
| hydra | 9.x | THC | https://github.com/vanhauser-thc/thc-hydra |

#### MIT / BSD-3 Licensed Tools
| Tool | License | Version | Copyright | Source |
| --- | --- | --- | --- | --- |
| hashcat | MIT | 6.x | hashcat.net | https://hashcat.net |
| ffuf | MIT | 2.x | Joel Oorni | https://github.com/ffuf/ffuf |
| chisel | MIT | 1.x | JPillora | https://github.com/jpillora/chisel |
| routersploit | BSD-3 | 4.x | Thunderstorm | https://github.com/thunderstorm-dev/routersploit |
| metasploit | BSD-3 | 6.x | Rapid7 | https://github.com/rapid7/metasploit-framework |
| linpeas | MIT | Latest | PEASS-ng | https://github.com/carlospolop/PEASS-ng |
| winpeas | MIT | Latest | PEASS-ng | https://github.com/carlospolop/PEASS-ng |
| tcpdump | BSD-3 | 4.x | TCPDUMP Team | https://www.tcpdump.org |

#### Proprietary Software
| Tool | License | Notes |
| --- | --- | --- |
| Burp Suite Community | PortSwigger EULA | https://portswigger.net/burp. For authorized use only. Not for redistribution. |

---

### Section 3: Base Operating System
This project uses `kalilinux/kali-rolling` as base image. Kali contains thousands of packages under GPL, MIT, BSD and other OSI-approved licenses.

---

### Disclaimer
All trademarks and registered trademarks are the property of their respective owners. 
Master peon is not affiliated with, endorsed by, or sponsored by any of the tool authors listed above.

For full license text of any dependency, please refer to the source links above or run `apt show [package-name]` inside the container.