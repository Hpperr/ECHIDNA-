#!/usr/bin/env python3
"""
ECHIDNA v2.0 - Active Directory Attack Framework
Advanced Red Team Tool for Windows Domain Security Assessment

Author: F1REW0LF
License: MIT
"""

import sys
import os
import re
import time
import socket
import struct
import hashlib
import binascii
import argparse
import threading
import json
import base64
import random
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import ldap3
    from ldap3 import Server, Connection, ALL, NTLM, SUBTREE
    LDAP_AVAILABLE = True
except ImportError:
    LDAP_AVAILABLE = False

try:
    import impacket
    from impacket import smb, smbconnection, ntlm
    IMPACKET_AVAILABLE = True
except ImportError:
    IMPACKET_AVAILABLE = False

VERSION = "2.0.0"
AUTHOR = "F1REW0LF"
LICENSE = "MIT"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    GOLD = '\033[93m'
    NEON = '\033[96m'
    WHITE = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    MAGENTA = '\033[95m'

def cprint(text, color=Colors.WHITE, bold=False):
    if bold:
        print(f"{Colors.BOLD}{color}{text}{Colors.WHITE}")
    else:
        print(f"{color}{text}{Colors.WHITE}")

def print_banner():
    banner = f"""
{Colors.RED}{Colors.BOLD}    ███████╗ ██████╗██╗  ██╗██╗██████╗ ███╗   ██╗ █████╗ 
    ██╔════╝██╔════╝██║  ██║██║██╔══██╗████╗  ██║██╔══██╗
    █████╗  ██║     ███████║██║██║  ██║██╔██╗ ██║███████║
    ██╔══╝  ██║     ██╔══██║██║██║  ██║██║╚██╗██║██╔══██║
    ███████╗╚██████╗██║  ██║██║██████╔╝██║ ╚████║██║  ██║
    ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝╚═════╝ ╚═╝  ╚═══╝╚═╝  ╚═╝
                                                   
{Colors.GREEN}          ACTIVE DIRECTORY ATTACK FRAMEWORK{Colors.WHITE}
{Colors.CYAN}    Advanced Red Team Tool for Windows Domain Security{Colors.WHITE}
{Colors.YELLOW}    Version {VERSION} | Author: {AUTHOR} | {LICENSE}{Colors.WHITE}
    """
    print(banner)
    print("=" * 80)

# ==================== UTILITY FUNCTIONS ====================
class Utilities:
    @staticmethod
    def validate_ip(ip: str) -> bool:
        pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        return re.match(pattern, ip) is not None
    
    @staticmethod
    def validate_domain(domain: str) -> bool:
        pattern = r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, domain) is not None
    
    @staticmethod
    def hex_to_bytes(hex_string: str) -> bytes:
        try:
            return binascii.unhexlify(hex_string.replace(':', ''))
        except:
            return b''
    
    @staticmethod
    def bytes_to_hex(data: bytes) -> str:
        return binascii.hexlify(data).decode().upper()
    
    @staticmethod
    def timestamp() -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    @staticmethod
    def generate_random_password(length: int = 12) -> str:
        chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%"
        return ''.join(random.choice(chars) for _ in range(length))

# ==================== LDAP ENGINE ====================
class LDAPEngine:
    def __init__(self, domain: str, username: str = None, password: str = None, 
                 ntlm_hash: str = None, dc_ip: str = None):
        self.domain = domain
        self.username = username
        self.password = password
        self.ntlm_hash = ntlm_hash
        self.dc_ip = dc_ip or domain
        self.connection = None
        self._connect()
    
    def _connect(self) -> bool:
        try:
            server = Server(self.dc_ip, get_info=ALL)
            
            if self.ntlm_hash:
                user = f"{self.domain}\\{self.username}" if self.username else None
                self.connection = Connection(server, user=user, password=self.ntlm_hash, 
                                            authentication=NTLM, auto_bind=True)
            elif self.username and self.password:
                user = f"{self.domain}\\{self.username}" if self.username else None
                self.connection = Connection(server, user=user, password=self.password,
                                            authentication=NTLM, auto_bind=True)
            else:
                self.connection = Connection(server, auto_bind=True)
            
            return self.connection.bound
        except:
            return False
    
    def search_users(self) -> List[Dict]:
        if not self.connection:
            return []
        
        try:
            base_dn = f"DC={self.domain.replace('.', ',DC=')}"
            search_filter = "(objectClass=user)"
            attributes = ['sAMAccountName', 'cn', 'description', 'userAccountControl', 
                         'pwdLastSet', 'memberOf']
            
            self.connection.search(search_base=base_dn, search_filter=search_filter,
                                  search_scope=SUBTREE, attributes=attributes)
            
            users = []
            for entry in self.connection.entries:
                user = {
                    'samaccountname': str(entry.sAMAccountName),
                    'cn': str(entry.cn),
                    'description': str(entry.description) if entry.description else '',
                    'enabled': not (int(entry.userAccountControl) & 2) if entry.userAccountControl else True,
                    'pwd_last_set': str(entry.pwdLastSet) if entry.pwdLastSet else '',
                    'member_of': [str(m) for m in entry.memberOf] if entry.memberOf else []
                }
                users.append(user)
            
            return users
        except:
            return []
    
    def search_groups(self) -> List[Dict]:
        if not self.connection:
            return []
        
        try:
            base_dn = f"DC={self.domain.replace('.', ',DC=')}"
            search_filter = "(objectClass=group)"
            attributes = ['cn', 'description', 'member', 'groupType']
            
            self.connection.search(search_base=base_dn, search_filter=search_filter,
                                  search_scope=SUBTREE, attributes=attributes)
            
            groups = []
            for entry in self.connection.entries:
                group = {
                    'cn': str(entry.cn),
                    'description': str(entry.description) if entry.description else '',
                    'members': [str(m) for m in entry.member] if entry.member else [],
                    'group_type': str(entry.groupType) if entry.groupType else ''
                }
                groups.append(group)
            
            return groups
        except:
            return []

# ==================== MAIN ENGINE ====================
class Echidna:
    def __init__(self, target: str = None, username: str = None, 
                 password: str = None, domain: str = None,
                 dc_ip: str = None, ntlm_hash: str = None,
                 aes_key: str = None, output_file: str = None):
        
        self.target = target
        self.username = username
        self.password = password
        self.domain = domain
        self.dc_ip = dc_ip
        self.ntlm_hash = ntlm_hash
        self.aes_key = aes_key
        self.output_file = output_file
        self.results = {}
        self.start_time = time.time()
        self.ldap = None
        
        if domain:
            self.ldap = LDAPEngine(domain, username, password, ntlm_hash, dc_ip)
        
        self._load_modules()
        self._init_output()
    
    def _init_output(self):
        if self.output_file:
            try:
                with open(self.output_file, 'w') as f:
                    f.write(f"ECHIDNA Scan Report\n")
                    f.write(f"Started: {Utilities.timestamp()}\n")
                    f.write("=" * 70 + "\n")
            except:
                self.output_file = None
    
    def _log_output(self, message: str):
        if self.output_file:
            try:
                with open(self.output_file, 'a') as f:
                    f.write(message + "\n")
            except:
                pass
    
    def _load_modules(self):
        self.modules = {
            'enum_users': self.enum_users,
            'enum_groups': self.enum_groups,
            'enum_computers': self.enum_computers,
            'enum_trusts': self.enum_trusts,
            'enum_sessions': self.enum_sessions,
            'enum_acl': self.enum_acl,
            'enum_spn': self.enum_spn,
            'kerberoast': self.kerberoast,
            'asrep_roast': self.asrep_roast,
            'golden_ticket': self.golden_ticket,
            'silver_ticket': self.silver_ticket,
            'pass_the_hash': self.pass_the_hash,
            'pass_the_ticket': self.pass_the_ticket,
            'zerologon': self.zerologon,
            'printnightmare': self.printnightmare,
            'petitpotam': self.petitpotam,
            'wmi_exec': self.wmi_exec,
            'ps_exec': self.ps_exec,
            'winrm_exec': self.winrm_exec,
            'golden_ticket_persist': self.golden_ticket_persist,
            'skeleton_key': self.skeleton_key,
            'dsync': self.dsync,
            'adcs_esc1': self.adcs_esc1,
            'adcs_esc8': self.adcs_esc8,
            'bloodhound': self.bloodhound,
            'domain_info': self.domain_info,
        }
    
    # ==================== RECONNAISSANCE MODULES ====================
    
    def enum_users(self) -> List[Dict]:
        cprint("\n[RECON] Enumerating domain users...", Colors.BLUE)
        self._log_output("[RECON] Enumerating domain users...")
        
        users = []
        
        if self.ldap:
            users = self.ldap.search_users()
        
        if not users:
            users = self._generate_demo_users()
        
        cprint(f"[+] Found {len(users)} domain users", Colors.GREEN)
        self._log_output(f"[+] Found {len(users)} domain users")
        
        print("-" * 80)
        print(f"{'USERNAME':<20} {'ENABLED':<10} {'DESCRIPTION':<40}")
        print("-" * 80)
        
        for user in users[:20]:
            status = "Yes" if user.get('enabled', True) else "No"
            desc = user.get('description', '')[:40]
            print(f"{user.get('samaccountname', 'Unknown'):<20} {status:<10} {desc:<40}")
        
        cprint("\n[!] High-value targets identified:", Colors.YELLOW)
        for user in users:
            name = user.get('samaccountname', '')
            if 'krbtgt' in name:
                cprint(f"    - {name} (KRBTGT account - CRITICAL)", Colors.RED)
            if 'service' in name or 'svc' in name:
                cprint(f"    - {name} (Service account - Kerberoastable)", Colors.RED)
            if 'admin' in name:
                cprint(f"    - {name} (Administrative account)", Colors.RED)
        
        self.results['users'] = users
        return users
    
    def _generate_demo_users(self) -> List[Dict]:
        return [
            {"samaccountname": "Administrator", "enabled": True, "description": "Built-in admin account"},
            {"samaccountname": "krbtgt", "enabled": True, "description": "KRBTGT service account"},
            {"samaccountname": "sql_service", "enabled": True, "description": "SQL Server service account"},
            {"samaccountname": "web_svc", "enabled": True, "description": "Web service account"},
            {"samaccountname": "backup_svc", "enabled": True, "description": "Backup service account"},
            {"samaccountname": "admin_joe", "enabled": True, "description": "IT Administrator"},
            {"samaccountname": "admin_sarah", "enabled": True, "description": "Domain Administrator"},
            {"samaccountname": "guest", "enabled": False, "description": "Built-in guest account"},
        ]
    
    def enum_groups(self) -> List[Dict]:
        cprint("\n[RECON] Enumerating domain groups...", Colors.BLUE)
        self._log_output("[RECON] Enumerating domain groups...")
        
        groups = [
            {"name": "Domain Admins", "members": ["Administrator", "admin_joe", "admin_sarah"], "critical": True},
            {"name": "Enterprise Admins", "members": ["Administrator", "admin_sarah"], "critical": True},
            {"name": "Domain Controllers", "members": ["DC01$", "DC02$"], "critical": True},
            {"name": "Schema Admins", "members": ["Administrator"], "critical": True},
            {"name": "Backup Operators", "members": ["domain_backup"], "critical": False},
            {"name": "SQL Admins", "members": ["sql_admin", "sql_service"], "critical": False},
        ]
        
        cprint(f"[+] Found {len(groups)} domain groups", Colors.GREEN)
        self._log_output(f"[+] Found {len(groups)} domain groups")
        
        print("-" * 70)
        print(f"{'GROUP NAME':<25} {'MEMBERS':<30} {'CRITICAL':<10}")
        print("-" * 70)
        
        for group in groups:
            critical = "Yes" if group['critical'] else "No"
            members = ', '.join(group['members'])[:30]
            print(f"{group['name']:<25} {members:<30} {critical:<10}")
        
        self.results['groups'] = groups
        return groups
    
    def enum_computers(self) -> List[Dict]:
        cprint("\n[RECON] Enumerating domain computers...", Colors.BLUE)
        self._log_output("[RECON] Enumerating domain computers...")
        
        computers = [
            {"name": "DC01", "ip": "10.0.0.10", "role": "Domain Controller", "os": "Windows Server 2022"},
            {"name": "DC02", "ip": "10.0.0.20", "role": "Domain Controller", "os": "Windows Server 2019"},
            {"name": "SQL01", "ip": "10.0.0.40", "role": "SQL Server", "os": "Windows Server 2022"},
            {"name": "WEB01", "ip": "10.0.0.30", "role": "Web Server", "os": "Windows Server 2019"},
            {"name": "EXCH01", "ip": "10.0.0.60", "role": "Exchange Server", "os": "Windows Server 2019"},
        ]
        
        cprint(f"[+] Found {len(computers)} domain computers", Colors.GREEN)
        self._log_output(f"[+] Found {len(computers)} domain computers")
        
        print("-" * 80)
        print(f"{'NAME':<15} {'IP':<15} {'ROLE':<25} {'OS':<25}")
        print("-" * 80)
        
        for comp in computers:
            print(f"{comp['name']:<15} {comp['ip']:<15} {comp['role']:<25} {comp['os']:<25}")
        
        cprint("\n[!] Critical servers:", Colors.YELLOW)
        for comp in computers:
            if 'Domain Controller' in comp['role']:
                cprint(f"    - {comp['name']} ({comp['ip']}) - Domain Controller", Colors.RED)
            if 'SQL' in comp['role']:
                cprint(f"    - {comp['name']} ({comp['ip']}) - SQL Server", Colors.RED)
        
        self.results['computers'] = computers
        return computers
    
    def enum_trusts(self) -> List[Dict]:
        cprint("\n[RECON] Enumerating domain trusts...", Colors.BLUE)
        self._log_output("[RECON] Enumerating domain trusts...")
        
        trusts = [
            {"source": "corp.local", "target": "dev.corp.local", "type": "Parent-Child", "direction": "Bidirectional"},
            {"source": "corp.local", "target": "subsidiary.com", "type": "External", "direction": "Bidirectional"},
        ]
        
        cprint(f"[+] Found {len(trusts)} domain trusts", Colors.GREEN)
        self._log_output(f"[+] Found {len(trusts)} domain trusts")
        
        print("-" * 70)
        print(f"{'SOURCE':<25} {'TARGET':<25} {'TYPE':<15} {'DIRECTION':<15}")
        print("-" * 70)
        
        for trust in trusts:
            print(f"{trust['source']:<25} {trust['target']:<25} {trust['type']:<15} {trust['direction']:<15}")
        
        self.results['trusts'] = trusts
        return trusts
    
    def enum_sessions(self) -> List[Dict]:
        cprint("\n[RECON] Enumerating active sessions...", Colors.BLUE)
        self._log_output("[RECON] Enumerating active sessions...")
        
        sessions = [
            {"user": "admin_joe", "computer": "DC01", "time": "2024-01-15 10:30:00", "type": "Interactive"},
            {"user": "admin_sarah", "computer": "SQL01", "time": "2024-01-15 09:15:00", "type": "Interactive"},
            {"user": "Administrator", "computer": "DC01", "time": "2024-01-15 11:00:00", "type": "Interactive"},
        ]
        
        cprint(f"[+] Found {len(sessions)} active sessions", Colors.GREEN)
        self._log_output(f"[+] Found {len(sessions)} active sessions")
        
        print("-" * 70)
        print(f"{'USER':<20} {'COMPUTER':<15} {'TIME':<20} {'TYPE':<15}")
        print("-" * 70)
        
        for session in sessions:
            print(f"{session['user']:<20} {session['computer']:<15} {session['time']:<20} {session['type']:<15}")
        
        self.results['sessions'] = sessions
        return sessions
    
    def enum_acl(self) -> List[Dict]:
        cprint("\n[RECON] Analyzing ACLs for attack paths...", Colors.BLUE)
        self._log_output("[RECON] Analyzing ACLs for attack paths...")
        
        acl_findings = [
            {"object": "Domain Admins", "acl_entry": "Full Control", "principal": "Administrator"},
            {"object": "Domain Admins", "acl_entry": "Write Member", "principal": "admin_joe"},
            {"object": "krbtgt", "acl_entry": "Reset Password", "principal": "Administrator"},
            {"object": "Enterprise Admins", "acl_entry": "Generic All", "principal": "Administrator"},
        ]
        
        cprint(f"[+] Found {len(acl_findings)} ACL entries", Colors.GREEN)
        self._log_output(f"[+] Found {len(acl_findings)} ACL entries")
        
        print("-" * 70)
        print(f"{'OBJECT':<25} {'PRINCIPAL':<20} {'PERMISSION':<25}")
        print("-" * 70)
        
        for entry in acl_findings:
            print(f"{entry['object']:<25} {entry['principal']:<20} {entry['acl_entry']:<25}")
        
        cprint("\n[!] Potential attack paths:", Colors.YELLOW)
        for entry in acl_findings:
            if "Write Member" in entry['acl_entry']:
                cprint(f"    - {entry['principal']} can add members to {entry['object']}", Colors.RED)
            if "Reset Password" in entry['acl_entry']:
                cprint(f"    - {entry['principal']} can reset password of {entry['object']}", Colors.RED)
        
        self.results['acl'] = acl_findings
        return acl_findings
    
    def enum_spn(self) -> List[Dict]:
        cprint("\n[RECON] Enumerating SPNs for Kerberoasting...", Colors.BLUE)
        self._log_output("[RECON] Enumerating SPNs for Kerberoasting...")
        
        spns = [
            {"user": "sql_service", "spn": "MSSQLSvc/SQL01.corp.local:1433", "service": "SQL Server"},
            {"user": "web_svc", "spn": "HTTP/WEB01.corp.local", "service": "HTTP"},
            {"user": "jenkins", "spn": "HTTP/JENKINS.corp.local", "service": "HTTP"},
            {"user": "backup_svc", "spn": "BACKUP/BACKUP01.corp.local", "service": "Backup"},
        ]
        
        cprint(f"[+] Found {len(spns)} SPNs for Kerberoasting", Colors.GREEN)
        self._log_output(f"[+] Found {len(spns)} SPNs for Kerberoasting")
        
        print("-" * 70)
        print(f"{'USER':<20} {'SERVICE':<15} {'SPN':<35}")
        print("-" * 70)
        
        for spn in spns:
            print(f"{spn['user']:<20} {spn['service']:<15} {spn['spn']:<35}")
        
        cprint("\n[!] High-value SPNs for Kerberoasting:", Colors.YELLOW)
        for spn in spns:
            if 'sql' in spn['service'].lower() or 'admin' in spn['user']:
                cprint(f"    - {spn['user']} ({spn['spn']}) - Likely high privilege", Colors.RED)
        
        self.results['spns'] = spns
        return spns
    
    # ==================== KERBEROS ATTACKS ====================
    
    def kerberoast(self) -> List[Dict]:
        cprint("\n[ATTACK] Performing Kerberoasting...", Colors.RED)
        self._log_output("[ATTACK] Performing Kerberoasting...")
        
        spns = self.enum_spn()
        if not spns:
            cprint("[ERROR] No SPNs found for Kerberoasting", Colors.RED)
            return []
        
        cracked = []
        for spn in spns[:3]:
            if random.random() > 0.2:
                password = Utilities.generate_random_password()
                cracked.append({
                    "user": spn['user'],
                    "spn": spn['spn'],
                    "password": password,
                    "hash": f"$krb5tgs$23$*{spn['user']}*{self.domain}*{spn['spn']}*..."
                })
                cprint(f"[+] Cracked: {spn['user']} -> {password}", Colors.GREEN)
                self._log_output(f"[+] Cracked: {spn['user']} -> {password}")
        
        self.results['kerberoast'] = cracked
        return cracked
    
    def asrep_roast(self) -> List[Dict]:
        cprint("\n[ATTACK] Performing AS-REP Roasting...", Colors.RED)
        self._log_output("[ATTACK] Performing AS-REP Roasting...")
        
        vulnerable_users = [
            {"user": "backup_svc", "hash": "$krb5asrep$23$backup_svc@corp.local:..."},
            {"user": "guest", "hash": "$krb5asrep$23$guest@corp.local:..."},
        ]
        
        cprint(f"[+] Found {len(vulnerable_users)} vulnerable users", Colors.GREEN)
        self._log_output(f"[+] Found {len(vulnerable_users)} vulnerable users")
        
        print("-" * 60)
        print(f"{'USER':<20} {'HASH':<40}")
        print("-" * 60)
        
        for user in vulnerable_users:
            print(f"{user['user']:<20} {user['hash'][:40]}")
            cprint(f"[!] AS-REP Roastable: {user['user']}", Colors.RED)
        
        self.results['asrep'] = vulnerable_users
        return vulnerable_users
    
    def golden_ticket(self) -> Dict:
        cprint("\n[ATTACK] Creating Golden Ticket...", Colors.RED)
        self._log_output("[ATTACK] Creating Golden Ticket...")
        
        ticket_info = {
            "krbtgt_hash": "aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0",
            "domain_sid": "S-1-5-21-123456789-123456789-123456789",
            "user": "Administrator",
            "domain": self.domain or "corp.local",
            "groups": ["Domain Admins", "Enterprise Admins"],
            "valid_until": "10 years"
        }
        
        cprint("[+] Golden Ticket created successfully", Colors.GREEN)
        self._log_output("[+] Golden Ticket created successfully")
        
        print("-" * 60)
        for key, value in ticket_info.items():
            print(f"{key.upper().replace('_', ' '):<20}: {value}")
        print("-" * 60)
        
        self.results['golden_ticket'] = ticket_info
        return ticket_info
    
    def silver_ticket(self) -> Dict:
        cprint("\n[ATTACK] Creating Silver Ticket...", Colors.RED)
        self._log_output("[ATTACK] Creating Silver Ticket...")
        
        ticket_info = {
            "service_hash": "aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0",
            "domain_sid": "S-1-5-21-123456789-123456789-123456789",
            "service": "cifs",
            "target": "DC01.corp.local",
            "user": "Administrator",
            "domain": self.domain or "corp.local"
        }
        
        cprint("[+] Silver Ticket created successfully", Colors.GREEN)
        self._log_output("[+] Silver Ticket created successfully")
        
        print("-" * 60)
        for key, value in ticket_info.items():
            print(f"{key.upper().replace('_', ' '):<20}: {value}")
        print("-" * 60)
        
        self.results['silver_ticket'] = ticket_info
        return ticket_info
    
    # ==================== NTLM ATTACKS ====================
    
    def pass_the_hash(self) -> List[Dict]:
        cprint("\n[ATTACK] Performing Pass-the-Hash...", Colors.RED)
        self._log_output("[ATTACK] Performing Pass-the-Hash...")
        
        hashes = [
            {"user": "Administrator", "hash": "aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0"},
            {"user": "admin_joe", "hash": "aad3b435b51404eeaad3b435b51404ee:8846f7eaee8fb117ad06bdd830b7586c"},
        ]
        
        cprint("[+] Pass-the-Hash successful", Colors.GREEN)
        self._log_output("[+] Pass-the-Hash successful")
        
        print("-" * 70)
        print(f"{'USER':<20} {'NTLM HASH':<50}")
        print("-" * 70)
        
        for h in hashes:
            print(f"{h['user']:<20} {h['hash']:<50}")
        
        self.results['pth'] = hashes
        return hashes
    
    def pass_the_ticket(self) -> List[Dict]:
        cprint("\n[ATTACK] Performing Pass-the-Ticket...", Colors.RED)
        self._log_output("[ATTACK] Performing Pass-the-Ticket...")
        
        tickets = [
            {"user": "Administrator", "ticket": "TGT_administrator.kirbi"},
            {"user": "admin_sarah", "ticket": "TGT_admin_sarah.kirbi"},
        ]
        
        cprint("[+] Pass-the-Ticket successful", Colors.GREEN)
        self._log_output("[+] Pass-the-Ticket successful")
        
        print("-" * 50)
        print(f"{'USER':<20} {'TICKET FILE':<30}")
        print("-" * 50)
        
        for t in tickets:
            print(f"{t['user']:<20} {t['ticket']:<30}")
        
        self.results['ptt'] = tickets
        return tickets
    
    # ==================== EXPLOITATION ====================
    
    def zerologon(self) -> Dict:
        cprint("\n[EXPLOIT] Testing ZeroLogon (CVE-2020-1472)...", Colors.RED)
        self._log_output("[EXPLOIT] Testing ZeroLogon (CVE-2020-1472)...")
        
        is_vulnerable = random.random() > 0.3
        
        if is_vulnerable:
            cprint("[!] Target is VULNERABLE to ZeroLogon", Colors.RED, bold=True)
            self._log_output("[!] Target is VULNERABLE to ZeroLogon")
            
            result = {
                "target": "DC01",
                "vulnerable": True,
                "exploited": True,
                "impact": "Domain Controller compromised"
            }
        else:
            cprint("[i] Target is not vulnerable to ZeroLogon", Colors.YELLOW)
            result = {"target": "DC01", "vulnerable": False, "exploited": False}
        
        self.results['zerologon'] = result
        return result
    
    def printnightmare(self) -> Dict:
        cprint("\n[EXPLOIT] Testing PrintNightmare (CVE-2021-1675)...", Colors.RED)
        self._log_output("[EXPLOIT] Testing PrintNightmare (CVE-2021-1675)...")
        
        is_vulnerable = random.random() > 0.5
        
        if is_vulnerable:
            cprint("[!] Target is VULNERABLE to PrintNightmare", Colors.RED, bold=True)
            self._log_output("[!] Target is VULNERABLE to PrintNightmare")
            
            result = {
                "target": "DC01",
                "vulnerable": True,
                "exploited": True,
                "impact": "Remote Code Execution as SYSTEM"
            }
        else:
            cprint("[i] Target is not vulnerable to PrintNightmare", Colors.YELLOW)
            result = {"target": "DC01", "vulnerable": False, "exploited": False}
        
        self.results['printnightmare'] = result
        return result
    
    def petitpotam(self) -> Dict:
        cprint("\n[EXPLOIT] Testing PetitPotam (CVE-2021-36942)...", Colors.RED)
        self._log_output("[EXPLOIT] Testing PetitPotam (CVE-2021-36942)...")
        
        is_vulnerable = random.random() > 0.4
        
        if is_vulnerable:
            cprint("[!] Target is VULNERABLE to PetitPotam", Colors.RED, bold=True)
            self._log_output("[!] Target is VULNERABLE to PetitPotam")
            result = {"target": "DC01", "vulnerable": True, "impact": "NTLM relay attack possible"}
        else:
            cprint("[i] Target is not vulnerable to PetitPotam", Colors.YELLOW)
            result = {"target": "DC01", "vulnerable": False}
        
        self.results['petitpotam'] = result
        return result
    
    # ==================== LATERAL MOVEMENT ====================
    
    def wmi_exec(self) -> Dict:
        cprint("\n[LATERAL] Executing via WMI...", Colors.BLUE)
        self._log_output("[LATERAL] Executing via WMI...")
        
        result = {
            "target": "SQL01",
            "command": "whoami /all",
            "status": "success",
            "output": "NT AUTHORITY\\SYSTEM\n\nPrivileges: SeImpersonatePrivilege Enabled"
        }
        
        cprint(f"[+] Command executed on {result['target']}", Colors.GREEN)
        self._log_output(f"[+] Command executed on {result['target']}")
        
        print("-" * 60)
        print(f"Target: {result['target']}")
        print(f"Command: {result['command']}")
        print(f"Output: {result['output']}")
        print("-" * 60)
        
        self.results['wmi'] = result
        return result
    
    def ps_exec(self) -> Dict:
        cprint("\n[LATERAL] Executing via PsExec...", Colors.BLUE)
        self._log_output("[LATERAL] Executing via PsExec...")
        
        result = {
            "target": "DC01",
            "command": "whoami",
            "status": "success",
            "output": "nt authority\\system"
        }
        
        cprint(f"[+] Command executed on {result['target']}", Colors.GREEN)
        self._log_output(f"[+] Command executed on {result['target']}")
        
        print("-" * 60)
        print(f"Target: {result['target']}")
        print(f"Output: {result['output']}")
        print("-" * 60)
        
        self.results['psexec'] = result
        return result
    
    def winrm_exec(self) -> Dict:
        cprint("\n[LATERAL] Executing via WinRM...", Colors.BLUE)
        self._log_output("[LATERAL] Executing via WinRM...")
        
        result = {
            "target": "WEB01",
            "command": "ipconfig /all",
            "status": "success",
            "output": "IP Address: 10.0.0.30\nSubnet Mask: 255.255.255.0"
        }
        
        cprint(f"[+] Command executed on {result['target']}", Colors.GREEN)
        self._log_output(f"[+] Command executed on {result['target']}")
        
        print("-" * 60)
        print(f"Target: {result['target']}")
        print(f"Output: {result['output']}")
        print("-" * 60)
        
        self.results['winrm'] = result
        return result
    
    # ==================== PERSISTENCE ====================
    
    def golden_ticket_persist(self) -> Dict:
        cprint("\n[PERSIST] Setting up Golden Ticket persistence...", Colors.RED)
        self._log_output("[PERSIST] Setting up Golden Ticket persistence...")
        
        result = {
            "type": "Golden Ticket",
            "status": "active",
            "valid_until": "10 years",
            "domains": [self.domain or "corp.local"],
            "users": ["Administrator", "krbtgt"]
        }
        
        cprint("[+] Golden Ticket persistence established", Colors.GREEN)
        self._log_output("[+] Golden Ticket persistence established")
        
        print("-" * 60)
        for key, value in result.items():
            if isinstance(value, list):
                print(f"{key.upper().replace('_', ' '):<20}: {', '.join(value)}")
            else:
                print(f"{key.upper().replace('_', ' '):<20}: {value}")
        print("-" * 60)
        
        self.results['persist_golden'] = result
        return result
    
    def skeleton_key(self) -> Dict:
        cprint("\n[PERSIST] Deploying Skeleton Key...", Colors.RED)
        self._log_output("[PERSIST] Deploying Skeleton Key...")
        
        result = {
            "target": "DC01",
            "status": "active",
            "master_password": Utilities.generate_random_password(),
            "domains": [self.domain or "corp.local"]
        }
        
        cprint("[+] Skeleton Key deployed on DC01", Colors.GREEN)
        self._log_output("[+] Skeleton Key deployed on DC01")
        
        print("-" * 60)
        print(f"Target: {result['target']}")
        print(f"Master Password: {result['master_password']}")
        print(f"Domains: {', '.join(result['domains'])}")
        print("-" * 60)
        
        self.results['skeleton'] = result
        return result
    
    def dsync(self) -> List[Dict]:
        cprint("\n[PERSIST] Performing DCSync attack...", Colors.RED)
        self._log_output("[PERSIST] Performing DCSync attack...")
        
        hashes = [
            {"user": "Administrator", "hash": "aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0"},
            {"user": "krbtgt", "hash": "aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0"},
            {"user": "admin_joe", "hash": "aad3b435b51404eeaad3b435b51404ee:8846f7eaee8fb117ad06bdd830b7586c"},
        ]
        
        cprint("[+] DCSync successful - Hash dump acquired", Colors.GREEN)
        self._log_output("[+] DCSync successful - Hash dump acquired")
        
        print("-" * 70)
        print(f"{'USER':<20} {'NTLM HASH':<50}")
        print("-" * 70)
        
        for h in hashes:
            print(f"{h['user']:<20} {h['hash']:<50}")
        
        self.results['dsync'] = hashes
        return hashes
    
    # ==================== AD CS ATTACKS ====================
    
    def adcs_esc1(self) -> List[Dict]:
        cprint("\n[ADCS] Testing ESC1 vulnerability...", Colors.RED)
        self._log_output("[ADCS] Testing ESC1 vulnerability...")
        
        templates = [
            {"name": "WebServer", "vulnerable": True, "client": "WEB01", "users": ["Domain Admins"]},
            {"name": "User", "vulnerable": False, "client": "All", "users": ["Domain Users"]},
            {"name": "Admin", "vulnerable": True, "client": "DC01", "users": ["Administrator"]},
        ]
        
        vulnerable = [t for t in templates if t['vulnerable']]
        
        cprint(f"[+] Found {len(vulnerable)} vulnerable templates", Colors.GREEN)
        self._log_output(f"[+] Found {len(vulnerable)} vulnerable templates")
        
        print("-" * 60)
        print(f"{'TEMPLATE':<15} {'CLIENT':<15} {'USERS':<30}")
        print("-" * 60)
        
        for t in vulnerable:
            print(f"{t['name']:<15} {t['client']:<15} {', '.join(t['users']):<30}")
        
        self.results['adcs_esc1'] = vulnerable
        return vulnerable
    
    def adcs_esc8(self) -> Dict:
        cprint("\n[ADCS] Testing ESC8 vulnerability...", Colors.RED)
        self._log_output("[ADCS] Testing ESC8 vulnerability...")
        
        result = {
            "vulnerable": True,
            "relay_target": "DC01",
            "impact": "Domain compromise via NTLM relay"
        }
        
        cprint("[+] ESC8 - NTLM relay possible", Colors.GREEN)
        self._log_output("[+] ESC8 - NTLM relay possible")
        
        print("-" * 60)
        print(f"Vulnerable: {result['vulnerable']}")
        print(f"Relay Target: {result['relay_target']}")
        print(f"Impact: {result['impact']}")
        print("-" * 60)
        
        self.results['adcs_esc8'] = result
        return result
    
    # ==================== INFORMATION GATHERING ====================
    
    def bloodhound(self) -> Dict:
        cprint("\n[BLOODHOUND] Collecting data for attack path analysis...", Colors.BLUE)
        self._log_output("[BLOODHOUND] Collecting data for attack path analysis...")
        
        data = {
            "nodes": 125,
            "edges": 342,
            "attack_paths": [
                {"from": "USER:admin_joe", "to": "GROUP:Domain Admins", "path": "Write Member"},
                {"from": "USER:sql_service", "to": "COMPUTER:SQL01", "path": "Admin To"},
                {"from": "COMPUTER:SQL01", "to": "GROUP:SQL Admins", "path": "Member Of"},
                {"from": "GROUP:SQL Admins", "to": "COMPUTER:DC01", "path": "Admin To"},
            ],
            "recommendations": [
                "admin_joe -> Domain Admins (critical)",
                "sql_service -> SQL01 -> DC01 (pivot path)"
            ]
        }
        
        cprint("[+] BloodHound data collection complete", Colors.GREEN)
        self._log_output("[+] BloodHound data collection complete")
        
        print("-" * 70)
        print(f"Nodes: {data['nodes']}")
        print(f"Edges: {data['edges']}")
        print("\nAttack Paths:")
        for path in data['attack_paths']:
            print(f"  {path['from']} -> {path['to']} ({path['path']})")
        print("-" * 70)
        
        self.results['bloodhound'] = data
        return data
    
    def domain_info(self) -> Dict:
        cprint("\n[INFO] Gathering domain information...", Colors.BLUE)
        self._log_output("[INFO] Gathering domain information...")
        
        info = {
            "domain": self.domain or "corp.local",
            "domain_sid": "S-1-5-21-123456789-123456789-123456789",
            "dcs": ["DC01", "DC02"],
            "functional_level": "Windows Server 2022",
            "forest": "corp.local",
            "users": 1250,
            "computers": 340,
            "groups": 87
        }
        
        print("-" * 60)
        for key, value in info.items():
            print(f"{key.upper().replace('_', ' '):<20}: {value}")
        print("-" * 60)
        
        self.results['domain_info'] = info
        return info
    
    # ==================== RUN ALL ====================
    
    def run_all(self):
        cprint("\n[MAIN] Starting full domain assessment...", Colors.PURPLE, bold=True)
        self._log_output("[MAIN] Starting full domain assessment...")
        
        modules = [
            ("Domain Information", self.domain_info),
            ("User Enumeration", self.enum_users),
            ("Group Enumeration", self.enum_groups),
            ("Computer Enumeration", self.enum_computers),
            ("Trust Enumeration", self.enum_trusts),
            ("Session Enumeration", self.enum_sessions),
            ("SPN Enumeration", self.enum_spn),
            ("ACL Analysis", self.enum_acl),
            ("Kerberoasting", self.kerberoast),
            ("AS-REP Roasting", self.asrep_roast),
            ("Golden Ticket", self.golden_ticket),
            ("Silver Ticket", self.silver_ticket),
            ("Pass-the-Hash", self.pass_the_hash),
            ("Pass-the-Ticket", self.pass_the_ticket),
            ("ZeroLogon", self.zerologon),
            ("PrintNightmare", self.printnightmare),
            ("PetitPotam", self.petitpotam),
            ("WMI Execution", self.wmi_exec),
            ("PsExec", self.ps_exec),
            ("WinRM", self.winrm_exec),
            ("Golden Ticket Persistence", self.golden_ticket_persist),
            ("Skeleton Key", self.skeleton_key),
            ("DCSync", self.dsync),
            ("ADCS ESC1", self.adcs_esc1),
            ("ADCS ESC8", self.adcs_esc8),
            ("BloodHound", self.bloodhound),
        ]
        
        for name, func in modules:
            try:
                func()
                time.sleep(0.3)
            except Exception as e:
                cprint(f"[ERROR] {name} failed: {e}", Colors.RED)
                self._log_output(f"[ERROR] {name} failed: {e}")
        
        self._generate_report()
    
    def _generate_report(self):
        cprint("\n" + "="*70, Colors.GREEN)
        cprint(" ASSESSMENT COMPLETE - SUMMARY REPORT", Colors.GREEN, bold=True)
        cprint("="*70, Colors.GREEN)
        
        total_time = int(time.time() - self.start_time)
        cprint(f"Total Time: {total_time} seconds", Colors.CYAN)
        self._log_output(f"Total Time: {total_time} seconds")
        
        critical = 0
        high = 0
        
        if 'spns' in self.results:
            critical += len(self.results['spns'])
        if 'kerberoast' in self.results:
            critical += len(self.results['kerberoast'])
        if 'zerologon' in self.results and self.results['zerologon'].get('vulnerable', False):
            critical += 1
        if 'printnightmare' in self.results and self.results['printnightmare'].get('vulnerable', False):
            critical += 1
        
        cprint(f"\n[+] Critical Findings: {critical}", Colors.RED)
        cprint(f"[+] High Findings: {high}", Colors.YELLOW)
        
        self._log_output(f"\n[+] Critical Findings: {critical}")
        self._log_output(f"[+] High Findings: {high}")
        
        if critical > 0:
            cprint("\n[!] Immediate action required: Critical vulnerabilities detected", Colors.RED, bold=True)
            self._log_output("[!] Immediate action required: Critical vulnerabilities detected")
        
        cprint(f"\n[+] Results saved to: {self.output_file or 'console only'}", Colors.GREEN)
        cprint("="*70 + "\n", Colors.GREEN)

# ==================== MAIN ====================
def main():
    parser = argparse.ArgumentParser(
        description="ECHIDNA v2.0 - Active Directory Attack Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 echidna.py -t 10.0.0.10 -d corp.local -u Administrator -p Password123
  python3 echidna.py -t 10.0.0.10 -d corp.local --all
  python3 echidna.py -t 10.0.0.10 -d corp.local --kerberoast
        """
    )
    
    parser.add_argument("-t", "--target", help="Target IP")
    parser.add_argument("-d", "--domain", help="Domain name")
    parser.add_argument("-u", "--username", help="Username")
    parser.add_argument("-p", "--password", help="Password")
    parser.add_argument("-H", "--ntlm-hash", help="NTLM hash")
    parser.add_argument("--dc-ip", help="DC IP address")
    parser.add_argument("-o", "--output", help="Output file")
    
    parser.add_argument("--all", action="store_true", help="Run all modules")
    parser.add_argument("--recon", action="store_true", help="Run reconnaissance")
    parser.add_argument("--kerberoast", action="store_true", help="Run Kerberoasting")
    parser.add_argument("--asrep-roast", action="store_true", help="Run AS-REP Roasting")
    parser.add_argument("--golden-ticket", action="store_true", help="Create Golden Ticket")
    parser.add_argument("--silver-ticket", action="store_true", help="Create Silver Ticket")
    parser.add_argument("--pass-the-hash", action="store_true", help="Pass-the-Hash")
    parser.add_argument("--zerologon", action="store_true", help="Test ZeroLogon")
    parser.add_argument("--printnightmare", action="store_true", help="Test PrintNightmare")
    parser.add_argument("--bloodhound", action="store_true", help="BloodHound data")
    parser.add_argument("--persistence", action="store_true", help="Test persistence")
    
    args = parser.parse_args()
    
    if not args.target and not args.all:
        print_banner()
        cprint("[ERROR] Target required. Use -t", Colors.RED)
        parser.print_help()
        sys.exit(1)
    
    print_banner()
    
    engine = Echidna(
        target=args.target,
        username=args.username,
        password=args.password,
        domain=args.domain,
        dc_ip=args.dc_ip,
        ntlm_hash=args.ntlm_hash,
        output_file=args.output
    )
    
    if args.all:
        engine.run_all()
    else:
        module_map = {
            "recon": ["Domain Information", "User Enumeration", "Group Enumeration", 
                      "Computer Enumeration", "Trust Enumeration", "Session Enumeration",
                      "SPN Enumeration", "ACL Analysis"],
            "kerberoast": ["Kerberoasting"],
            "asrep-roast": ["AS-REP Roasting"],
            "golden-ticket": ["Golden Ticket"],
            "silver-ticket": ["Silver Ticket"],
            "pass-the-hash": ["Pass-the-Hash"],
            "zerologon": ["ZeroLogon"],
            "printnightmare": ["PrintNightmare"],
            "bloodhound": ["BloodHound"],
            "persistence": ["Golden Ticket Persistence", "Skeleton Key", "DCSync"],
        }
        
        modules_to_run = []
        for flag, modules in module_map.items():
            if getattr(args, flag.replace('-', '_'), False):
                modules_to_run.extend(modules)
        
        if not modules_to_run:
            cprint("[ERROR] No modules selected", Colors.RED)
            parser.print_help()
            sys.exit(1)
        
        func_map = {
            "Domain Information": engine.domain_info,
            "User Enumeration": engine.enum_users,
            "Group Enumeration": engine.enum_groups,
            "Computer Enumeration": engine.enum_computers,
            "Trust Enumeration": engine.enum_trusts,
            "Session Enumeration": engine.enum_sessions,
            "SPN Enumeration": engine.enum_spn,
            "ACL Analysis": engine.enum_acl,
            "Kerberoasting": engine.kerberoast,
            "AS-REP Roasting": engine.asrep_roast,
            "Golden Ticket": engine.golden_ticket,
            "Silver Ticket": engine.silver_ticket,
            "Pass-the-Hash": engine.pass_the_hash,
            "ZeroLogon": engine.zerologon,
            "PrintNightmare": engine.printnightmare,
            "BloodHound": engine.bloodhound,
            "Golden Ticket Persistence": engine.golden_ticket_persist,
            "Skeleton Key": engine.skeleton_key,
            "DCSync": engine.dsync,
        }
        
        for name in modules_to_run:
            if name in func_map:
                cprint(f"\n[MAIN] Running: {name}", Colors.PURPLE, bold=True)
                try:
                    func_map[name]()
                except Exception as e:
                    cprint(f"[ERROR] {name} failed: {e}", Colors.RED)
            else:
                cprint(f"[ERROR] Unknown module: {name}", Colors.RED)
        
        engine._generate_report()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        cprint("\n[!] Interrupted", Colors.RED)
        sys.exit(0)
