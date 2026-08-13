# ECHIDNA v3.0

## Active Directory Attack Framework

Advanced Red Team tool for Windows Domain security assessment and penetration testing.

## Features

### Reconnaissance
- Domain user enumeration
- Domain group enumeration
- Domain computer enumeration
- Domain trust enumeration
- Active session enumeration
- ACL analysis for attack paths
- SPN enumeration for Kerberoasting

### Kerberos Attacks
- Kerberoasting - Crack service account passwords
- AS-REP Roasting - Attack accounts without pre-authentication
- Golden Ticket - Forge TGT tickets
- Silver Ticket - Forge service tickets

### NTLM Attacks
- Pass-the-Hash - Use NTLM hashes for authentication
- Pass-the-Ticket - Use Kerberos tickets

### Exploitation
- ZeroLogon (CVE-2020-1472)
- PrintNightmare (CVE-2021-1675)
- PetitPotam (CVE-2021-36942)

### Lateral Movement
- WMI Command Execution
- PsExec-style Execution
- WinRM Execution

### Persistence
- Golden Ticket Persistence
- Skeleton Key Attack
- DCSync Attack

### AD CS Attacks
- ESC1 - Template Misconfiguration
- ESC8 - NTLM Relay

### Information Gathering
- BloodHound-style data collection
- Comprehensive domain information

## Installation

```bash
cd ECHIDNA
pip install -r requirements.txt
python3 echidna.py -t TARGET -d DOMAIN --all
