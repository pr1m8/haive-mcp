[![license](https://img.shields.io/github/license/mashape/apistatus.svg?maxAge=2592000)](https://choosealicense.com/licenses/mit/)

![mcp_cyberagent_banner](https://github.com/JithukrishnanV/j/blob/master/pics/Logo.png)

# MCP-CyberAgent 🛡️

MCP-CyberAgent is an **MCP-compliant AI security assistant** that connects Claude Desktop (or any MCP client) with real-world cybersecurity tools like **VirusTotal, Nmap, Shodan**, and **PowerShell**.

🔬 In this project, I’ve integrated automated hash extraction from running startup applications — enabling Claude to act like a personalized  
**AI-powered Malware Scanner**.

It supports natural language interaction to:

- Scan for malware using VirusTotal
- Discover active network services
- Gather threat intelligence from Shodan
- Test network health and connectivity

All this runs **locally** in your environment — no cloud integration required. And it's completely free.

---

## 🎥 Demo

https://github.com/user-attachments/assets/469d2800-8c06-461f-8336-6a1751b851cc

---

## ⚙️ Tools & Prompts

### 🔬 VirusTotal Integration

Using PowerShell, MCP-CyberAgent extracts SHA256 hashes from startup applications and checks them against **VirusTotal’s threat database**.

> 🧠 Try asking Claude:  
> `"Scan running processes with VirusTotal"`  
> `"Check for malware in startup applications"`

![virustotal_demo](https://github.com/JithukrishnanV/j/blob/master/pics/VirusTotal.png)

---

### 🌐 Nmap Port Scanner

Scan open ports, services, and protocols on any IP using Claude.

> 🧠 Try:  
> `"Check what ports are open on 127.0.0.1"`

![nmap_demo](https://github.com/JithukrishnanV/j/blob/master/pics/Nmap1.png)

---

### 🌍 Shodan IP Intelligence

Get real-time internet-facing service information for any public IP address using Shodan.

> 🧠 Try:  
> `"What does Shodan know about 1.1.1.1?"`

![shodan_demo](https://github.com/JithukrishnanV/j/blob/master/pics/Shodan.png)

---

### 🌐 Get Public IP

Query your external/public IP address.

> 🧠 Try:  
> `"What is my IP?"`

![MyIp_demo](https://github.com/JithukrishnanV/j/blob/master/pics/MyIp.png)

---

### 🏓 Ping Checker

Test latency and host reachability via ICMP.

> 🧠 Try:  
> `"Ping 8.8.8.8"`  
> `"Check if google.com is online"`

![ping_demo](https://github.com/JithukrishnanV/j/blob/master/pics/Ping.png)

---

## ✅ Requirements

- Python 3.10+
- Windows PowerShell (for startup hash scanning)
- Claude Desktop or 5ire
- API Keys:
  - [VirusTotal](https://virustotal.com)
  - [Shodan](https://shodan.io) (free key is enough)

Install dependencies:

```bash
pip install -r requirements.txt



## 🔧 Setup Guide

### 📁 Project Layout
```

MCP-CyberAgent/
├── bridge_mcp_cyberagent.py
├── modules/
│ ├── virustotal_module.py
│ ├── nmap_module.py
│ ├── shodan_module.py
│ └── sysinfo.ps1
├── configs/
│ └── api_keys.env
├── README.md
└── requirements.txt

````

### ✅ Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/JithukrishnanV/MCP-CyberAgent
   cd MCP-CyberAgent
````

2. **Create a virtual environment (optional but recommended):**

   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Add your API keys in `configs/api_keys.env`:**

   ```
   VT_API_KEY=your_virustotal_api_key
   SHODAN_API_KEY=your_shodan_api_key
   ```

5. **Edit Claude Desktop config:**
   Claude Desktop
   To set up Claude Desktop as a Ghidra MCP client, go to Claude -> Settings -> Developer -> Edit Config -> claude_desktop_config.json and add the following:

   ```json
   {
     "mcpServers": {
       "cyberagent": {
         "command": "C:/Path/To/python.exe",
         "args": [
           ""/ABSOLUTE_PATH_TO/bridge_mcp_cyberagent.py"
         ]
       }
     }
   }
   ```

6. **Launch Claude and select the MCP-CyberAgent from the MCP tab.**

---

## 🔗 Resources

- 🧠 [Claude MCP Docs](https://modelcontextprotocol.io)
- 🔍 [VirusTotal](https://virustotal.com)
- 🌐 [Shodan](https://shodan.io)
- 🛰️ [Nmap](https://nmap.org)
- 📚 [Python SDK for MCP](https://pypi.org/project/mcp/)
- 🛠️ [ping3](https://pypi.org/project/ping3/)
- 🌍 [ipify - Get Public IP](https://www.ipify.org/)

---
