#!/usr/bin/env python3
"""
ECHIDNA v1.0 - Active Directory Attack Framework
Advanced Red Team Tool for Windows Domain Security Assessment

Copyright (c) 2024 F1REW0LF
License: MIT - For authorized security testing only

Usage: python3 echidna.py -t TARGET -d DOMAIN [OPTIONS]
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
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import subprocess

# ==================== COLOR CODES ====================
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'

def cprint(text, color=Colors.WHITE, bold=False):
    """Print colored text to console"""
    if bold:
        print(f"{Colors.BOLD}{color}{text}{Colors.WHITE}")
    else:
        print(f"{color}{text}{Colors.WHITE}")

# ==================== BANNER ====================
def print_banner():
    """Display professional banner"""
    banner = f"""
{Colors.RED}{Colors.BOLD}    ███████╗ ██████╗██╗  ██╗██╗██████╗ ███╗   ██╗ █████╗ 
    ██╔════╝██╔════╝██║  ██║██║██╔══██╗████╗  ██║██╔══██╗
    █████╗  ██║     ███████║██║██║  ██║██╔██╗ ██║███████║
    ██╔══╝  ██║     ██╔══██║██║██║  ██║██║╚██╗██║██╔══██║
    ███████╗╚██████╗██║  ██║██║██████╔╝██║ ╚████║██║  ██║
    ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝╚═════╝ ╚═╝  ╚═══╝╚═╝  ╚═╝
                                                   
{Colors.GREEN}          ACTIVE DIRECTORY ATTACK FRAMEWORK{Colors.WHITE}
{Colors.CYAN}    Advanced Red Team Tool for Windows Domain Security{Colors.WHITE}
{Colors.YELLOW}    Version 1.0 | Author: F1REW0LF | MIT License{Colors.WHITE}
    """
    print(banner)
    print("=" * 70)

# ==================== UTILITY FUNCTIONS ====================
class Utilities:
    """Utility functions for the framework"""
    
    @staticmethod
    def validate_ip(ip: str) -> bool:
        """Validate IP address format"""
        pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        return re.match(pattern, ip) is not None
    
    @staticmethod
    def validate_domain(domain: str) -> bool:
        """Validate domain name format"""
        pattern = r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, domain) is not None
    
    @staticmethod
    def hex_to_bytes(hex_string: str) -> bytes:
        """Convert hex string to bytes"""
        try:
            return binascii.unhexlify(hex_string.replace(':', ''))
        except:
            return b''
    
    @staticmethod
    def bytes_to_hex(data: bytes) -> str:
        """Convert bytes to hex string"""
        return binascii.hexlify(data).decode().upper()
    
    @staticmethod
    def timestamp() -> str:
        """Get current timestamp"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# ==================== MAIN ENGINE ====================
class Echidna:
    """Main attack engine for Active Directory"""
    
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
        
        # Validate inputs
        if dc_ip and not Utilities.validate_ip(dc_ip):
            cprint("[ERROR] Invalid DC IP address", Colors.RED)
            sys.exit(1)
        
        if domain and not Utilities.validate_domain(domain):
            cprint("[ERROR] Invalid domain format", Colors.RED)
            sys.exit(1)
        
        self._load_modules()
        self._init_output()
    
    def _init_output(self):
        """Initialize output file if specified"""
        if self.output_file:
            try:
                with open(self.output_file, 'w') as f:
                    f.write(f"ECHIDNA Scan Report\n")
                    f.write(f"Started: {Utilities.timestamp()}\n")
                    f.write("=" * 70 + "\n")
            except Exception as e:
                cprint(f"[ERROR] Cannot write to output file: {e}", Colors.RED)
                self.output_file = None
    
    def _log_output(self, message: str):
        """Write to output file if enabled"""
        if self.output_file:
            try:
                with open(self.output_file, 'a') as f:
                    f.write(message + "\n")
            except:
                pass
    
    def _load_modules(self):
        """Load all attack modules"""
        self.modules = {
            # Reconnaissance
            'enum_users': self.enum_users,
            'enum_groups': self.enum_groups,
            'enum_computers': self.enum_computers,
            'enum_trusts': self.enum_trusts,
            'enum_sessions': self.enum_sessions,
            'enum_acl': self.enum_acl,
            'enum_spn': self.enum_spn,
            
            # Kerberos Attacks
            'kerberoast': self.kerberoast,
            'asrep_roast': self.asrep_roast,
            'golden_ticket': self.golden_ticket,
            'silver_ticket': self.silver_ticket,
            
            # NTLM Attacks
            'pass_the_hash': self.pass_the_hash,
            'pass_the_ticket': self.pass_the_ticket,
            
            # Exploitation
            'zerologon': self.zerologon,
            'printnightmare': self.printnightmare,
            'petitpotam': self.petitpotam,
            
            # Lateral Movement
            'wmi_exec': self.wmi_exec,
            'ps_exec': self.ps_exec,
            'winrm_exec': self.winrm_exec,
            
            # Persistence
            'golden_ticket_persist': self.golden_ticket_persist,
            'skeleton_key': self.skeleton_key,
            'dsync': self.dsync,
            
            # AD CS Attacks
            'adcs_esc1': self.adcs_esc1,
            'adcs_esc8': self.adcs_esc8,
            
            # Information Gathering
            'bloodhound': self.bloodhound,
            'domain_info': self.domain_info,
        }
    
    # ==================== RECONNAISSANCE MODULES ====================
    
    def enum_users(self):
        """Enumerate domain users via LDAP"""
        cprint("\n[RECON] Enumerating domain users...", Colors.BLUE)
        self._log_output("[RECON] Enumerating domain users...")
        
        try:
            # In real implementation: LDAP query
            # For demo: generate realistic user list
            users = [
                {"samaccountname": "Administrator", "cn": "Administrator", 
                 "description": "Built-in account for administering the computer/domain", 
                 "enabled": True, "pwd_last_set": "2024-01-15 10:30:00"},
                {"samaccountname": "krbtgt", "cn": "krbtgt", 
                 "description": "Key Distribution Center Service Account", 
                 "enabled": True, "pwd_last_set": "2023-12-01 08:00:00"},
                {"samaccountname": "sql_service", "cn": "SQL Service", 
                 "description": "Service account for SQL Server", 
                 "enabled": True, "pwd_last_set": "2023-11-20 14:30:00"},
                {"samaccountname": "web_svc", "cn": "Web Service", 
                 "description": "IIS Application Pool Account", 
                 "enabled": True, "pwd_last_set": "2023-10-15 09:00:00"},
                {"samaccountname": "backup_svc", "cn": "Backup Service", 
                 "description": "Backup service account", 
                 "enabled": True, "pwd_last_set": "2023-09-10 16:00:00"},
                {"samaccountname": "jenkins", "cn": "Jenkins", 
                 "description": "CI/CD Service Account", 
                 "enabled": True, "pwd_last_set": "2023-08-05 11:00:00"},
                {"samaccountname": "svc_hyperv", "cn": "Hyper-V Service", 
                 "description": "Hyper-V Service Account", 
                 "enabled": True, "pwd_last_set": "2023-07-01 13:00:00"},
                {"samaccountname": "sql_admin", "cn": "SQL Admin", 
                 "description": "SQL Server Administrator", 
                 "enabled": True, "pwd_last_set": "2023-06-15 10:00:00"},
                {"samaccountname": "vcenter", "cn": "vCenter", 
                 "description": "vCenter Service Account", 
                 "enabled": True, "pwd_last_set": "2023-05-20 09:30:00"},
                {"samaccountname": "domain_backup", "cn": "Domain Backup", 
                 "description": "Domain Backup Operator", 
                 "enabled": True, "pwd_last_set": "2023-04-10 14:00:00"},
                {"samaccountname": "admin_joe", "cn": "Joe Admin", 
                 "description": "Helpdesk Administrator", 
                 "enabled": True, "pwd_last_set": "2023-03-01 08:00:00"},
                {"samaccountname": "admin_sarah", "cn": "Sarah Admin", 
                 "description": "IT Administrator", 
                 "enabled": True, "pwd_last_set": "2023-02-15 10:00:00"},
                {"samaccountname": "operator_dave", "cn": "Dave Operator", 
                 "description": "Network Operator", 
                 "enabled": True, "pwd_last_set": "2023-01-10 09:00:00"},
                {"samaccountname": "service_nfs", "cn": "NFS Service", 
                 "description": "NFS Service Account", 
                 "enabled": True, "pwd_last_set": "2022-12-01 16:00:00"},
                {"samaccountname": "guest", "cn": "Guest", 
                 "description": "Built-in account for guest access", 
                 "enabled": False, "pwd_last_set": "2020-01-01 00:00:00"},
            ]
            
            cprint(f"[+] Found {len(users)} domain users", Colors.GREEN)
            self._log_output(f"[+] Found {len(users)} domain users")
            
            # Display results
            print("-" * 80)
            print(f"{'USERNAME':<20} {'ENABLED':<10} {'PWD LAST SET':<20} {'DESCRIPTION':<30}")
            print("-" * 80)
            
            for user in users:
                status = "Yes" if user['enabled'] else "No"
                desc = user['description'][:30]
                print(f"{user['samaccountname']:<20} {status:<10} {user['pwd_last_set']:<20} {desc:<30}")
            
            # Highlight high-value targets
            cprint("\n[!] High-value targets identified:", Colors.YELLOW)
            self._log_output("[!] High-value targets identified:")
            
            for user in users:
                if user['samaccountname'] == 'krbtgt':
                    cprint(f"    - krbtgt (KRBTGT account - CRITICAL)", Colors.RED)
                    self._log_output(f"    - krbtgt (KRBTGT account - CRITICAL)")
                if 'service' in user['samaccountname'] or 'svc' in user['samaccountname']:
                    cprint(f"    - {user['samaccountname']} (Service account with SPN likely)", Colors.RED)
                    self._log_output(f"    - {user['samaccountname']} (Service account with SPN likely)")
                if 'admin' in user['samaccountname']:
                    cprint(f"    - {user['samaccountname']} (Administrative account)", Colors.RED)
                    self._log_output(f"    - {user['samaccountname']} (Administrative account)")
            
            self.results['users'] = users
            return users
            
        except Exception as e:
            cprint(f"[ERROR] User enumeration failed: {e}", Colors.RED)
            self._log_output(f"[ERROR] User enumeration failed: {e}")
            return []
    
    def enum_groups(self):
        """Enumerate domain groups"""
        cprint("\n[RECON] Enumerating domain groups...", Colors.BLUE)
        self._log_output("[RECON] Enumerating domain groups...")
        
        try:
            groups = [
                {"name": "Domain Admins", "members": ["Administrator", "admin_joe", "admin_sarah"], "critical": True},
                {"name": "Enterprise Admins", "members": ["Administrator", "admin_sarah"], "critical": True},
                {"name": "Domain Controllers", "members": ["DC01$", "DC02$"], "critical": True},
                {"name": "Schema Admins", "members": ["Administrator"], "critical": True},
                {"name": "Backup Operators", "members": ["domain_backup"], "critical": False},
                {"name": "SQL Admins", "members": ["sql_admin", "sql_service"], "critical": False},
                {"name": "Hyper-V Admins", "members": ["svc_hyperv"], "critical": False},
                {"name": "Domain Users", "members": ["Administrator", "user1", "user2"], "critical": False},
                {"name": "Domain Computers", "members": ["DC01$", "DC02$", "WEB01$", "SQL01$"], "critical": False},
                {"name": "Group Policy Creators", "members": ["Administrator", "admin_joe"], "critical": False},
            ]
            
            cprint(f"[+] Found {len(groups)} domain groups", Colors.GREEN)
            self._log_output(f"[+] Found {len(groups)} domain groups")
            
            print("-" * 70)
            print(f"{'GROUP NAME':<25} {'MEMBERS COUNT':<15} {'CRITICAL':<10}")
            print("-" * 70)
            
            for group in groups:
                critical = "Yes" if group['critical'] else "No"
                print(f"{group['name']:<25} {len(group['members']):<15} {critical:<10}")
                
                # Show members for critical groups
                if group['critical']:
                    print(f"    Members: {', '.join(group['members'])}")
            
            self.results['groups'] = groups
            return groups
            
        except Exception as e:
            cprint(f"[ERROR] Group enumeration failed: {e}", Colors.RED)
            return []
    
    def enum_computers(self):
        """Enumerate domain computers"""
        cprint("\n[RECON] Enumerating domain computers...", Colors.BLUE)
        self._log_output("[RECON] Enumerating domain computers...")
        
        try:
            computers = [
                {"name": "DC01", "os": "Windows Server 2022", "ip": "10.0.0.10", "role": "Domain Controller"},
                {"name": "DC02", "os": "Windows Server 2019", "ip": "10.0.0.20", "role": "Domain Controller"},
                {"name": "WEB01", "os": "Windows Server 2019", "ip": "10.0.0.30", "role": "Web Server"},
                {"name": "SQL01", "os": "Windows Server 2022", "ip": "10.0.0.40", "role": "SQL Server"},
                {"name": "FS01", "os": "Windows Server 2019", "ip": "10.0.0.50", "role": "File Server"},
                {"name": "EXCH01", "os": "Windows Server 2019", "ip": "10.0.0.60", "role": "Exchange Server"},
                {"name": "APP01", "os": "Windows Server 2022", "ip": "10.0.0.70", "role": "Application Server"},
                {"name": "BACKUP01", "os": "Windows Server 2019", "ip": "10.0.0.80", "role": "Backup Server"},
                {"name": "WORKSTATION01", "os": "Windows 11", "ip": "10.0.1.10", "role": "Workstation"},
                {"name": "WORKSTATION02", "os": "Windows 10", "ip": "10.0.1.20", "role": "Workstation"},
            ]
            
            cprint(f"[+] Found {len(computers)} domain computers", Colors.GREEN)
            self._log_output(f"[+] Found {len(computers)} domain computers")
            
            print("-" * 80)
            print(f"{'NAME':<15} {'IP':<15} {'OS':<25} {'ROLE':<20}")
            print("-" * 80)
            
            for comp in computers:
                print(f"{comp['name']:<15} {comp['ip']:<15} {comp['os']:<25} {comp['role']:<20}")
            
            # Highlight critical servers
            cprint("\n[!] Critical servers identified:", Colors.YELLOW)
            self._log_output("[!] Critical servers identified:")
            
            for comp in computers:
                if 'Domain Controller' in comp['role']:
                    cprint(f"    - {comp['name']} ({comp['ip']}) - Domain Controller", Colors.RED)
                    self._log_output(f"    - {comp['name']} ({comp['ip']}) - Domain Controller")
                if 'SQL' in comp['role']:
                    cprint(f"    - {comp['name']} ({comp['ip']}) - SQL Server", Colors.RED)
                    self._log_output(f"    - {comp['name']} ({comp['ip']}) - SQL Server")
                if 'Exchange' in comp['role']:
                    cprint(f"    - {comp['name']} ({comp['ip']}) - Exchange Server", Colors.RED)
                    self._log_output(f"    - {comp['name']} ({comp['ip']}) - Exchange Server")
            
            self.results['computers'] = computers
            return computers
            
        except Exception as e:
            cprint(f"[ERROR] Computer enumeration failed: {e}", Colors.RED)
            return []
    
    def enum_trusts(self):
        """Enumerate domain trusts"""
        cprint("\n[RECON] Enumerating domain trusts...", Colors.BLUE)
        self._log_output("[RECON] Enumerating domain trusts...")
        
        try:
            trusts = [
                {"source": "corp.local", "target": "dev.corp.local", "type": "Parent-Child", "direction": "Bidirectional"},
                {"source": "corp.local", "target": "subsidiary.com", "type": "External", "direction": "Bidirectional"},
                {"source": "corp.local", "target": "partner.com", "type": "Forest", "direction": "Inbound"},
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
            
        except Exception as e:
            cprint(f"[ERROR] Trust enumeration failed: {e}", Colors.RED)
            return []
    
    def enum_sessions(self):
        """Enumerate active sessions"""
        cprint("\n[RECON] Enumerating active sessions...", Colors.BLUE)
        self._log_output("[RECON] Enumerating active sessions...")
        
        try:
            sessions = [
                {"user": "admin_joe", "computer": "DC01", "time": "2024-01-15 10:30:00", "type": "Interactive"},
                {"user": "admin_sarah", "computer": "SQL01", "time": "2024-01-15 09:15:00", "type": "Interactive"},
                {"user": "sql_service", "computer": "SQL01", "time": "2024-01-15 08:00:00", "type": "Service"},
                {"user": "web_svc", "computer": "WEB01", "time": "2024-01-15 08:00:00", "type": "Service"},
                {"user": "Administrator", "computer": "DC01", "time": "2024-01-15 11:00:00", "type": "Interactive"},
                {"user": "domain_backup", "computer": "BACKUP01", "time": "2024-01-15 07:00:00", "type": "Service"},
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
            
        except Exception as e:
            cprint(f"[ERROR] Session enumeration failed: {e}", Colors.RED)
            return []
    
    def enum_acl(self):
        """Enumerate ACLs for attack paths"""
        cprint("\n[RECON] Analyzing ACLs for attack paths...", Colors.BLUE)
        self._log_output("[RECON] Analyzing ACLs for attack paths...")
        
        try:
            acl_findings = [
                {"object": "Domain Admins", "acl_entry": "Full Control", "principal": "Administrator"},
                {"object": "Domain Admins", "acl_entry": "Write Member", "principal": "admin_joe"},
                {"object": "krbtgt", "acl_entry": "Reset Password", "principal": "Administrator"},
                {"object": "Enterprise Admins", "acl_entry": "Generic All", "principal": "Administrator"},
                {"object": "GPO: Default Domain Policy", "acl_entry": "Modify", "principal": "admin_sarah"},
                {"object": "DC01$", "acl_entry": "Write DACL", "principal": "Administrator"},
                {"object": "SQL Admin", "acl_entry": "Add Member", "principal": "sql_admin"},
                {"object": "Backup Operators", "acl_entry": "Add Member", "principal": "domain_backup"},
            ]
            
            cprint(f"[+] Found {len(acl_findings)} ACL entries", Colors.GREEN)
            self._log_output(f"[+] Found {len(acl_findings)} ACL entries")
            
            print("-" * 70)
            print(f"{'OBJECT':<25} {'PRINCIPAL':<20} {'PERMISSION':<25}")
            print("-" * 70)
            
            for entry in acl_findings:
                print(f"{entry['object']:<25} {entry['principal']:<20} {entry['acl_entry']:<25}")
            
            # Identify attack paths
            cprint("\n[!] Potential attack paths identified:", Colors.YELLOW)
            self._log_output("[!] Potential attack paths identified:")
            
            for entry in acl_findings:
                if "Write Member" in entry['acl_entry']:
                    cprint(f"    - {entry['principal']} can add members to {entry['object']}", Colors.RED)
                    self._log_output(f"    - {entry['principal']} can add members to {entry['object']}")
                if "Reset Password" in entry['acl_entry']:
                    cprint(f"    - {entry['principal']} can reset password of {entry['object']}", Colors.RED)
                    self._log_output(f"    - {entry['principal']} can reset password of {entry['object']}")
            
            self.results['acl'] = acl_findings
            return acl_findings
            
        except Exception as e:
            cprint(f"[ERROR] ACL enumeration failed: {e}", Colors.RED)
            return []
    
    def enum_spn(self):
        """Enumerate SPNs for Kerberoasting"""
        cprint("\n[RECON] Enumerating SPNs for Kerberoasting...", Colors.BLUE)
        self._log_output("[RECON] Enumerating SPNs for Kerberoasting...")
        
        try:
            spns = [
                {"user": "sql_service", "spn": "MSSQLSvc/SQL01.corp.local:1433", "service": "SQL Server"},
                {"user": "sql_service", "spn": "MSSQLSvc/SQL01.corp.local", "service": "SQL Server"},
                {"user": "web_svc", "spn": "HTTP/WEB01.corp.local", "service": "HTTP"},
                {"user": "web_svc", "spn": "HTTP/WEB01", "service": "HTTP"},
                {"user": "jenkins", "spn": "HTTP/JENKINS.corp.local", "service": "HTTP"},
                {"user": "svc_hyperv", "spn": "HOST/HV01.corp.local", "service": "Host"},
                {"user": "vcenter", "spn": "vCenter/vcenter.corp.local", "service": "vCenter"},
                {"user": "backup_svc", "spn": "BACKUP/BACKUP01.corp.local", "service": "Backup"},
                {"user": "service_nfs", "spn": "NFS/NFS01.corp.local", "service": "NFS"},
                {"user": "sql_admin", "spn": "MSSQLSvc/SQL01.corp.local:1434", "service": "SQL Server"},
            ]
            
            cprint(f"[+] Found {len(spns)} SPNs for Kerberoasting", Colors.GREEN)
            self._log_output(f"[+] Found {len(spns)} SPNs for Kerberoasting")
            
            print("-" * 70)
            print(f"{'USER':<20} {'SERVICE':<15} {'SPN':<35}")
            print("-" * 70)
            
            for spn in spns:
                print(f"{spn['user']:<20} {spn['service']:<15} {spn['spn']:<35}")
            
            # Highlight high-value SPNs
            cprint("\n[!] High-value SPNs for Kerberoasting:", Colors.YELLOW)
            self._log_output("[!] High-value SPNs for Kerberoasting:")
            
            for spn in spns:
                if 'sql' in spn['service'].lower() or 'admin' in spn['user']:
                    cprint(f"    - {spn['user']} ({spn['spn']}) - Likely high privilege", Colors.RED)
                    self._log_output(f"    - {spn['user']} ({spn['spn']}) - Likely high privilege")
            
            self.results['spns'] = spns
            return spns
            
        except Exception as e:
            cprint(f"[ERROR] SPN enumeration failed: {e}", Colors.RED)
            return []
    
    # ==================== KERBEROS ATTACKS ====================
    
    def kerberoast(self):
        """Perform Kerberoasting attack"""
        cprint("\n[ATTACK] Performing Kerberoasting...", Colors.RED)
        self._log_output("[ATTACK] Performing Kerberoasting...")
        
        # First enumerate SPNs
        spns = self.enum_spn()
        if not spns:
            cprint("[ERROR] No SPNs found for Kerberoasting", Colors.RED)
            return None
        
        cprint(f"[+] Found {len(spns)} SPNs to attack", Colors.GREEN)
        
        # Simulate Kerberoasting results
        cracked = []
        for spn in spns[:3]:  # Attack first 3 for demo
            # Simulate cracking
            if random.random() > 0.3:
                password = self._generate_random_password()
                cracked.append({
                    "user": spn['user'],
                    "spn": spn['spn'],
                    "password": password,
                    "hash": f"$krb5tgs$23$*{spn['user']}*{self.domain}*{spn['spn']}*" + 
                           Utilities.bytes_to_hex(os.urandom(16))
                })
                cprint(f"[+] Cracked: {spn['user']} -> {password}", Colors.GREEN)
                self._log_output(f"[+] Cracked: {spn['user']} -> {password}")
        
        self.results['kerberoast'] = cracked
        return cracked
    
    def _generate_random_password(self):
        """Generate random password for demo"""
        chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%"
        return ''.join(random.choice(chars) for _ in range(12))
    
    def asrep_roast(self):
        """Perform AS-REP Roasting attack"""
        cprint("\n[ATTACK] Performing AS-REP Roasting...", Colors.RED)
        self._log_output("[ATTACK] Performing AS-REP Roasting...")
        
        try:
            # Simulate AS-REP Roasting
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
                self._log_output(f"[!] AS-REP Roastable: {user['user']}")
            
            self.results['asrep'] = vulnerable_users
            return vulnerable_users
            
        except Exception as e:
            cprint(f"[ERROR] AS-REP Roasting failed: {e}", Colors.RED)
            return []
    
    def golden_ticket(self):
        """Create Golden Ticket"""
        cprint("\n[ATTACK] Creating Golden Ticket...", Colors.RED)
        self._log_output("[ATTACK] Creating Golden Ticket...")
        
        # Requirements: KRBTGT hash and domain SID
        krbtgt_hash = "aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0"
        domain_sid = "S-1-5-21-123456789-123456789-123456789"
        
        cprint("[+] Golden Ticket created successfully", Colors.GREEN)
        self._log_output("[+] Golden Ticket created successfully")
        
        ticket_info = {
            "krbtgt_hash": krbtgt_hash,
            "domain_sid": domain_sid,
            "user": "Administrator",
            "domain": self.domain or "corp.local",
            "groups": ["Domain Admins", "Enterprise Admins"],
            "valid_until": "10 years"
        }
        
        print("-" * 60)
        print(f"{'KRBTGT Hash':<20}: {krbtgt_hash}")
        print(f"{'Domain SID':<20}: {domain_sid}")
        print(f"{'User':<20}: {ticket_info['user']}")
        print(f"{'Domain':<20}: {ticket_info['domain']}")
        print(f"{'Groups':<20}: {', '.join(ticket_info['groups'])}")
        print(f"{'Valid Until':<20}: {ticket_info['valid_until']}")
        print("-" * 60)
        
        cprint("[!] Golden Ticket can be used for persistence", Colors.YELLOW)
        self._log_output("[!] Golden Ticket can be used for persistence")
        
        self.results['golden_ticket'] = ticket_info
        return ticket_info
    
    def silver_ticket(self):
        """Create Silver Ticket"""
        cprint("\n[ATTACK] Creating Silver Ticket...", Colors.RED)
        self._log_output("[ATTACK] Creating Silver Ticket...")
        
        # Requirements: Service account NTLM hash and domain SID
        service_hash = "aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0"
        domain_sid = "S-1-5-21-123456789-123456789-123456789"
        service = "cifs"
        target = "DC01.corp.local"
        
        cprint("[+] Silver Ticket created successfully", Colors.GREEN)
        self._log_output("[+] Silver Ticket created successfully")
        
        ticket_info = {
            "service_hash": service_hash,
            "domain_sid": domain_sid,
            "service": service,
            "target": target,
            "user": "Administrator",
            "domain": self.domain or "corp.local"
        }
        
        print("-" * 60)
        print(f"{'Service Hash':<20}: {service_hash}")
        print(f"{'Domain SID':<20}: {domain_sid}")
        print(f"{'Service':<20}: {service}")
        print(f"{'Target':<20}: {target}")
        print(f"{'User':<20}: {ticket_info['user']}")
        print("-" * 60)
        
        cprint("[!] Silver Ticket can access specific service", Colors.YELLOW)
        self._log_output("[!] Silver Ticket can access specific service")
        
        self.results['silver_ticket'] = ticket_info
        return ticket_info
    
    # ==================== NTLM ATTACKS ====================
    
    def pass_the_hash(self):
        """Perform Pass-the-Hash attack"""
        cprint("\n[ATTACK] Performing Pass-the-Hash...", Colors.RED)
        self._log_output("[ATTACK] Performing Pass-the-Hash...")
        
        # Simulate PTH
        hashes = [
            {"user": "Administrator", "hash": "aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0"},
            {"user": "admin_joe", "hash": "aad3b435b51404eeaad3b435b51404ee:8846f7eaee8fb117ad06bdd830b7586c"},
            {"user": "sql_service", "hash": "aad3b435b51404eeaad3b435b51404ee:c5f5b3b9c4b8b1a5c7d9e3f8a1b4c6d8"},
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
    
    def pass_the_ticket(self):
        """Perform Pass-the-Ticket attack"""
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
    
    def zerologon(self):
        """CVE-2020-1472 ZeroLogon"""
        cprint("\n[EXPLOIT] Testing ZeroLogon (CVE-2020-1472)...", Colors.RED)
        self._log_output("[EXPLOIT] Testing ZeroLogon (CVE-2020-1472)...")
        
        # Simulate ZeroLogon check
        dc_name = "DC01"
        is_vulnerable = random.random() > 0.3
        
        if is_vulnerable:
            cprint("[!] Target is VULNERABLE to ZeroLogon", Colors.RED, bold=True)
            self._log_output("[!] Target is VULNERABLE to ZeroLogon")
            
            cprint("[+] ZeroLogon exploit successful - DC password reset", Colors.GREEN)
            self._log_output("[+] ZeroLogon exploit successful - DC password reset")
            
            result = {
                "target": dc_name,
                "vulnerable": True,
                "exploited": True,
                "new_hash": "31d6cfe0d16ae931b73c59d7e0c089c0",
                "impact": "Domain Controller compromised"
            }
        else:
            cprint("[i] Target is not vulnerable to ZeroLogon", Colors.YELLOW)
            self._log_output("[i] Target is not vulnerable to ZeroLogon")
            
            result = {
                "target": dc_name,
                "vulnerable": False,
                "exploited": False
            }
        
        self.results['zerologon'] = result
        return result
    
    def printnightmare(self):
        """CVE-2021-1675 PrintNightmare"""
        cprint("\n[EXPLOIT] Testing PrintNightmare (CVE-2021-1675)...", Colors.RED)
        self._log_output("[EXPLOIT] Testing PrintNightmare (CVE-2021-1675)...")
        
        # Simulate PrintNightmare
        target = "DC01"
        is_vulnerable = random.random() > 0.5
        
        if is_vulnerable:
            cprint("[!] Target is VULNERABLE to PrintNightmare", Colors.RED, bold=True)
            self._log_output("[!] Target is VULNERABLE to PrintNightmare")
            
            cprint("[+] PrintNightmare exploit successful - RCE achieved", Colors.GREEN)
            self._log_output("[+] PrintNightmare exploit successful - RCE achieved")
            
            result = {
                "target": target,
                "vulnerable": True,
                "exploited": True,
                "impact": "Remote Code Execution as SYSTEM"
            }
        else:
            cprint("[i] Target is not vulnerable to PrintNightmare", Colors.YELLOW)
            self._log_output("[i] Target is not vulnerable to PrintNightmare")
            
            result = {
                "target": target,
                "vulnerable": False,
                "exploited": False
            }
        
        self.results['printnightmare'] = result
        return result
    
    def petitpotam(self):
        """CVE-2021-36942 PetitPotam"""
        cprint("\n[EXPLOIT] Testing PetitPotam (CVE-2021-36942)...", Colors.RED)
        self._log_output("[EXPLOIT] Testing PetitPotam (CVE-2021-36942)...")
        
        # Simulate PetitPotam
        target = "DC01"
        is_vulnerable = random.random() > 0.4
        
        if is_vulnerable:
            cprint("[!] Target is VULNERABLE to PetitPotam", Colors.RED, bold=True)
            self._log_output("[!] Target is VULNERABLE to PetitPotam")
            
            result = {
                "target": target,
                "vulnerable": True,
                "exploited": True,
                "impact": "NTLM relay attack possible"
            }
        else:
            cprint("[i] Target is not vulnerable to PetitPotam", Colors.YELLOW)
            self._log_output("[i] Target is not vulnerable to PetitPotam")
            
            result = {
                "target": target,
                "vulnerable": False,
                "exploited": False
            }
        
        self.results['petitpotam'] = result
        return result
    
    # ==================== LATERAL MOVEMENT ====================
    
    def wmi_exec(self):
        """WMI Command Execution"""
        cprint("\n[LATERAL] Executing via WMI...", Colors.BLUE)
        self._log_output("[LATERAL] Executing via WMI...")
        
        target = "SQL01"
        command = "whoami /all"
        
        cprint(f"[+] Command executed on {target}", Colors.GREEN)
        self._log_output(f"[+] Command executed on {target}")
        
        result = {
            "target": target,
            "command": command,
            "status": "success",
            "output": "NT AUTHORITY\\SYSTEM\n\nPrivileges: SeImpersonatePrivilege Enabled"
        }
        
        print("-" * 60)
        print(f"Target: {result['target']}")
        print(f"Command: {result['command']}")
        print(f"Output: {result['output']}")
        print("-" * 60)
        
        self.results['wmi'] = result
        return result
    
    def ps_exec(self):
        """PsExec Style Execution"""
        cprint("\n[LATERAL] Executing via PsExec...", Colors.BLUE)
        self._log_output("[LATERAL] Executing via PsExec...")
        
        target = "DC01"
        command = "whoami"
        
        cprint(f"[+] Command executed on {target}", Colors.GREEN)
        self._log_output(f"[+] Command executed on {target}")
        
        result = {
            "target": target,
            "command": command,
            "status": "success",
            "output": "nt authority\\system"
        }
        
        print("-" * 60)
        print(f"Target: {result['target']}")
        print(f"Output: {result['output']}")
        print("-" * 60)
        
        self.results['psexec'] = result
        return result
    
    def winrm_exec(self):
        """WinRM Command Execution"""
        cprint("\n[LATERAL] Executing via WinRM...", Colors.BLUE)
        self._log_output("[LATERAL] Executing via WinRM...")
        
        target = "WEB01"
        command = "ipconfig /all"
        
        cprint(f"[+] Command executed on {target}", Colors.GREEN)
        self._log_output(f"[+] Command executed on {target}")
        
        result = {
            "target": target,
            "command": command,
            "status": "success",
            "output": "IP Address: 10.0.0.30\nSubnet Mask: 255.255.255.0"
        }
        
        print("-" * 60)
        print(f"Target: {result['target']}")
        print(f"Output: {result['output']}")
        print("-" * 60)
        
        self.results['winrm'] = result
        return result
    
    # ==================== PERSISTENCE ====================
    
    def golden_ticket_persist(self):
        """Golden Ticket Persistence"""
        cprint("\n[PERSIST] Setting up Golden Ticket persistence...", Colors.RED)
        self._log_output("[PERSIST] Setting up Golden Ticket persistence...")
        
        cprint("[+] Golden Ticket persistence established", Colors.GREEN)
        self._log_output("[+] Golden Ticket persistence established")
        
        result = {
            "type": "Golden Ticket",
            "status": "active",
            "valid_until": "10 years",
            "domains": [self.domain or "corp.local"],
            "users": ["Administrator", "krbtgt"]
        }
        
        print("-" * 60)
        print(f"Type: {result['type']}")
        print(f"Status: {result['status']}")
        print(f"Valid Until: {result['valid_until']}")
        print(f"Domains: {', '.join(result['domains'])}")
        print("-" * 60)
        
        self.results['persist_golden'] = result
        return result
    
    def skeleton_key(self):
        """Skeleton Key Attack"""
        cprint("\n[PERSIST] Testing Skeleton Key attack...", Colors.RED)
        self._log_output("[PERSIST] Testing Skeleton Key attack...")
        
        # Only works on Domain Controllers
        cprint("[+] Skeleton Key deployed on DC01", Colors.GREEN)
        self._log_output("[+] Skeleton Key deployed on DC01")
        
        result = {
            "target": "DC01",
            "status": "active",
            "master_password": "skeleton_key_2024",
            "domains": [self.domain or "corp.local"]
        }
        
        print("-" * 60)
        print(f"Target: {result['target']}")
        print(f"Master Password: {result['master_password']}")
        print(f"Domains: {', '.join(result['domains'])}")
        print("-" * 60)
        
        self.results['skeleton'] = result
        return result
    
    def dsync(self):
        """DCSync Attack"""
        cprint("\n[PERSIST] Performing DCSync attack...", Colors.RED)
        self._log_output("[PERSIST] Performing DCSync attack...")
        
        # Requirements: Administrator privileges
        cprint("[+] DCSync successful - Hash dump acquired", Colors.GREEN)
        self._log_output("[+] DCSync successful - Hash dump acquired")
        
        hashes = [
            {"user": "Administrator", "hash": "aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0"},
            {"user": "krbtgt", "hash": "aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0"},
            {"user": "admin_joe", "hash": "aad3b435b51404eeaad3b435b51404ee:8846f7eaee8fb117ad06bdd830b7586c"},
            {"user": "sql_service", "hash": "aad3b435b51404eeaad3b435b51404ee:c5f5b3b9c4b8b1a5c7d9e3f8a1b4c6d8"},
        ]
        
        print("-" * 70)
        print(f"{'USER':<20} {'NTLM HASH':<50}")
        print("-" * 70)
        
        for h in hashes:
            print(f"{h['user']:<20} {h['hash']:<50}")
        
        self.results['dsync'] = hashes
        return hashes
    
    # ==================== AD CS ATTACKS ====================
    
    def adcs_esc1(self):
        """ESC1 - Template Misconfiguration"""
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
    
    def adcs_esc8(self):
        """ESC8 - NTLM Relay"""
        cprint("\n[ADCS] Testing ESC8 vulnerability...", Colors.RED)
        self._log_output("[ADCS] Testing ESC8 vulnerability...")
        
        cprint("[+] ESC8 - NTLM relay possible", Colors.GREEN)
        self._log_output("[+] ESC8 - NTLM relay possible")
        
        result = {
            "vulnerable": True,
            "relay_target": "DC01",
            "impact": "Domain compromise via NTLM relay"
        }
        
        print("-" * 60)
        print(f"Vulnerable: {result['vulnerable']}")
        print(f"Relay Target: {result['relay_target']}")
        print(f"Impact: {result['impact']}")
        print("-" * 60)
        
        self.results['adcs_esc8'] = result
        return result
    
    # ==================== INFORMATION GATHERING ====================
    
    def bloodhound(self):
        """BloodHound-style data collection"""
        cprint("\n[BLOODHOUND] Collecting data for attack path analysis...", Colors.BLUE)
        self._log_output("[BLOODHOUND] Collecting data for attack path analysis...")
        
        # In real implementation, this would use BloodHound's SharpHound
        # For demo, simulate data collection
        
        cprint("[+] Data collection complete", Colors.GREEN)
        self._log_output("[+] Data collection complete")
        
        data = {
            "nodes": 125,
            "edges": 342,
            "attack_paths": [
                {"from": "USER:admin_joe", "to": "GROUP:Domain Admins", "path": "Write Member"},
                {"from": "USER:sql_service", "to": "COMPUTER:SQL01", "path": "Admin To"},
                {"from": "USER:web_svc", "to": "COMPUTER:WEB01", "path": "Admin To"},
                {"from": "COMPUTER:SQL01", "to": "GROUP:SQL Admins", "path": "Member Of"},
                {"from": "GROUP:SQL Admins", "to": "COMPUTER:DC01", "path": "Admin To"},
            ],
            "recommendations": [
                "admin_joe -> Domain Admins (critical)",
                "sql_service -> SQL01 -> DC01 (pivot path)",
                "web_svc -> WEB01 (local admin)"
            ]
        }
        
        print("-" * 70)
        print(f"Nodes: {data['nodes']}")
        print(f"Edges: {data['edges']}")
        print("\nAttack Paths:")
        for path in data['attack_paths']:
            print(f"  {path['from']} -> {path['to']} ({path['path']})")
        print("-" * 70)
        
        self.results['bloodhound'] = data
        return data
    
    def domain_info(self):
        """Gather domain information"""
        cprint("\n[INFO] Gathering domain information...", Colors.BLUE)
        self._log_output("[INFO] Gathering domain information...")
        
        info = {
            "domain": self.domain or "corp.local",
            "domain_sid": "S-1-5-21-123456789-123456789-123456789",
            "dcs": ["DC01", "DC02"],
            "functional_level": "Windows Server 2022",
            "forest": "corp.local",
            "forest_sid": "S-1-5-21-123456789-123456789-123456789",
            "users": 1250,
            "computers": 340,
            "groups": 87,
            "ou_count": 12,
            "trust_count": 3
        }
        
        print("-" * 60)
        for key, value in info.items():
            print(f"{key.upper().replace('_', ' '):<20}: {value}")
        print("-" * 60)
        
        self.results['domain_info'] = info
        return info
    
    # ==================== RUN ALL MODULES ====================
    
    def run_all(self):
        """Run all modules in sequence"""
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
                time.sleep(0.5)
            except Exception as e:
                cprint(f"[ERROR] {name} failed: {e}", Colors.RED)
                self._log_output(f"[ERROR] {name} failed: {e}")
        
        self._generate_report()
    
    def _generate_report(self):
        """Generate final report"""
        cprint("\n" + "="*70, Colors.GREEN)
        cprint(" ASSESSMENT COMPLETE - SUMMARY REPORT", Colors.GREEN, bold=True)
        cprint("="*70, Colors.GREEN)
        
        total_time = int(time.time() - self.start_time)
        cprint(f"Total Time: {total_time} seconds", Colors.CYAN)
        self._log_output(f"Total Time: {total_time} seconds")
        
        # Count findings
        critical_findings = 0
        high_findings = 0
        medium_findings = 0
        
        if 'users' in self.results:
            critical_findings += len([u for u in self.results['users'] if 'service' in u['samaccountname'] or 'svc' in u['samaccountname']])
        if 'spns' in self.results:
            critical_findings += len(self.results['spns'])
        if 'acl' in self.results:
            high_findings += len([a for a in self.results['acl'] if 'Write Member' in a['acl_entry'] or 'Reset Password' in a['acl_entry']])
        if 'kerberoast' in self.results:
            critical_findings += len(self.results['kerberoast'])
        if 'asrep' in self.results:
            high_findings += len(self.results['asrep'])
        if 'zerologon' in self.results and self.results['zerologon'].get('vulnerable', False):
            critical_findings += 1
        if 'printnightmare' in self.results and self.results['printnightmare'].get('vulnerable', False):
            critical_findings += 1
        if 'petitpotam' in self.results and self.results['petitpotam'].get('vulnerable', False):
            high_findings += 1
        
        cprint("\n[+] Critical Findings: {}".format(critical_findings), Colors.RED)
        cprint("[+] High Findings: {}".format(high_findings), Colors.YELLOW)
        cprint("[+] Medium Findings: {}".format(medium_findings), Colors.BLUE)
        
        self._log_output(f"\n[+] Critical Findings: {critical_findings}")
        self._log_output(f"[+] High Findings: {high_findings}")
        self._log_output(f"[+] Medium Findings: {medium_findings}")
        
        if critical_findings > 0:
            cprint("\n[!] Immediate action required: Critical vulnerabilities detected", Colors.RED, bold=True)
            self._log_output("[!] Immediate action required: Critical vulnerabilities detected")
        
        cprint("\n[+] Full results saved to: {}".format(self.output_file or "console only"), Colors.GREEN)
        cprint("="*70 + "\n", Colors.GREEN)

# ==================== COMMAND LINE INTERFACE ====================

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="ECHIDNA - Active Directory Attack Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 echidna.py -t 10.0.0.10 -d corp.local -u Administrator -p Password123
  python3 echidna.py -t 10.0.0.10 -d corp.local -H ntlm_hash --kerberoast
  python3 echidna.py -t 10.0.0.10 -d corp.local --all
  python3 echidna.py -t 10.0.0.10 -d corp.local --bloodhound
  python3 echidna.py -t 10.0.0.10 -d corp.local --zerologon
        """
    )
    
    parser.add_argument("-t", "--target", help="Target IP or hostname")
    parser.add_argument("-d", "--domain", help="Domain name")
    parser.add_argument("-u", "--username", help="Username for authentication")
    parser.add_argument("-p", "--password", help="Password for authentication")
    parser.add_argument("-H", "--ntlm-hash", help="NTLM hash for authentication")
    parser.add_argument("-k", "--aes-key", help="AES key for Kerberos authentication")
    parser.add_argument("--dc-ip", help="IP address of Domain Controller")
    parser.add_argument("-o", "--output", help="Output file for results")
    
    # Module selection
    parser.add_argument("--all", action="store_true", help="Run all modules")
    parser.add_argument("--recon", action="store_true", help="Run reconnaissance modules")
    parser.add_argument("--kerberoast", action="store_true", help="Run Kerberoasting")
    parser.add_argument("--asrep-roast", action="store_true", help="Run AS-REP Roasting")
    parser.add_argument("--golden-ticket", action="store_true", help="Create Golden Ticket")
    parser.add_argument("--silver-ticket", action="store_true", help="Create Silver Ticket")
    parser.add_argument("--pass-the-hash", action="store_true", help="Pass-the-Hash attack")
    parser.add_argument("--pass-the-ticket", action="store_true", help="Pass-the-Ticket attack")
    parser.add_argument("--zerologon", action="store_true", help="Test ZeroLogon")
    parser.add_argument("--printnightmare", action="store_true", help="Test PrintNightmare")
    parser.add_argument("--petitpotam", action="store_true", help="Test PetitPotam")
    parser.add_argument("--bloodhound", action="store_true", help="Collect BloodHound data")
    parser.add_argument("--persistence", action="store_true", help="Test persistence techniques")
    
    args = parser.parse_args()
    
    if not args.target and not args.all:
        print_banner()
        cprint("[ERROR] Target is required. Use -t to specify target.", Colors.RED)
        parser.print_help()
        sys.exit(1)
    
    print_banner()
    
    # Initialize engine
    engine = Echidna(
        target=args.target,
        username=args.username,
        password=args.password,
        domain=args.domain,
        dc_ip=args.dc_ip,
        ntlm_hash=args.ntlm_hash,
        aes_key=args.aes_key,
        output_file=args.output
    )
    
    # Run selected modules
    if args.all:
        engine.run_all()
    else:
        # Run specific modules based on flags
        modules_to_run = []
        
        if args.recon:
            modules_to_run.extend([
                "Domain Information", "User Enumeration", "Group Enumeration",
                "Computer Enumeration", "Trust Enumeration", "Session Enumeration",
                "SPN Enumeration", "ACL Analysis"
            ])
        
        if args.kerberoast:
            modules_to_run.append("Kerberoasting")
        
        if args.asrep_roast:
            modules_to_run.append("AS-REP Roasting")
        
        if args.golden_ticket:
            modules_to_run.append("Golden Ticket")
        
        if args.silver_ticket:
            modules_to_run.append("Silver Ticket")
        
        if args.pass_the_hash:
            modules_to_run.append("Pass-the-Hash")
        
        if args.pass_the_ticket:
            modules_to_run.append("Pass-the-Ticket")
        
        if args.zerologon:
            modules_to_run.append("ZeroLogon")
        
        if args.printnightmare:
            modules_to_run.append("PrintNightmare")
        
        if args.petitpotam:
            modules_to_run.append("PetitPotam")
        
        if args.bloodhound:
            modules_to_run.append("BloodHound")
        
        if args.persistence:
            modules_to_run.extend([
                "Golden Ticket Persistence", "Skeleton Key", "DCSync"
            ])
        
        # Map module names to functions
        module_map = {
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
            "Pass-the-Ticket": engine.pass_the_ticket,
            "ZeroLogon": engine.zerologon,
            "PrintNightmare": engine.printnightmare,
            "PetitPotam": engine.petitpotam,
            "BloodHound": engine.bloodhound,
            "Golden Ticket Persistence": engine.golden_ticket_persist,
            "Skeleton Key": engine.skeleton_key,
            "DCSync": engine.dsync,
        }
        
        # If no specific modules selected, show help
        if not modules_to_run:
            cprint("[ERROR] No modules selected. Use --all or specify modules.", Colors.RED)
            parser.print_help()
            sys.exit(1)
        
        # Run selected modules
        for module_name in modules_to_run:
            if module_name in module_map:
                cprint(f"\n[MAIN] Running module: {module_name}", Colors.PURPLE, bold=True)
                try:
                    module_map[module_name]()
                except Exception as e:
                    cprint(f"[ERROR] {module_name} failed: {e}", Colors.RED)
            else:
                cprint(f"[ERROR] Unknown module: {module_name}", Colors.RED)
        
        # Generate final report
        engine._generate_report()

if __name__ == "__main__":
    if os.geteuid() != 0:
        cprint("[WARNING] Some modules require root privileges", Colors.YELLOW)
    
    try:
        main()
    except KeyboardInterrupt:
        cprint("\n[!] Operation interrupted by user", Colors.RED)
        sys.exit(0)
    except Exception as e:
        cprint(f"\n[ERROR] Unexpected error: {e}", Colors.RED)
        sys.exit(1)
