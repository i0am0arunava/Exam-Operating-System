#!/usr/bin/env python3
"""
Network Device Mapper
Demonstrates various approaches to finding and mapping devices on a network
"""

import socket
import subprocess
import ipaddress
import json
from typing import Dict, List, Tuple
import requests

class NetworkMapper:
    def __init__(self):
        self.devices = []
        
    def get_local_ip(self) -> str:
        """Get the local IP address of this machine"""
        try:
            # Create a socket to determine local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception as e:
            return f"Error: {e}"
    
    def get_network_range(self, ip: str, subnet_mask: str = "255.255.255.0") -> str:
        """Calculate network range from IP and subnet mask"""
        try:
            # For /24 network (most common home networks)
            network = ipaddress.IPv4Network(f"{ip}/24", strict=False)
            return str(network)
        except Exception as e:
            return f"Error: {e}"
    
    def scan_network_ping(self, network_range: str, timeout: int = 1) -> List[str]:
        """
        Scan network using ping (works on most systems)
        Note: This is a simple demonstration - full network scanning requires root/admin
        """
        active_hosts = []
        
        try:
            network = ipaddress.IPv4Network(network_range)
            print(f"Scanning network: {network_range}")
            print("Note: This is a basic ping scan. For complete results, use tools like nmap with appropriate permissions.\n")
            
            # Scan a small range for demonstration (first 10 IPs)
            for i, ip in enumerate(network.hosts()):
                if i >= 10:  # Limit for demo
                    print("(Limiting to first 10 IPs for demo...)")
                    break
                    
                # Ping the host
                try:
                    # Platform-specific ping command
                    import platform
                    param = '-n' if platform.system().lower() == 'windows' else '-c'
                    command = ['ping', param, '1', '-W', str(timeout), str(ip)]
                    
                    result = subprocess.run(
                        command,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        timeout=timeout + 1
                    )
                    
                    if result.returncode == 0:
                        active_hosts.append(str(ip))
                        print(f"✓ Found: {ip}")
                    else:
                        print(f"✗ No response: {ip}")
                        
                except subprocess.TimeoutExpired:
                    print(f"✗ Timeout: {ip}")
                except Exception as e:
                    print(f"✗ Error checking {ip}: {e}")
                    
        except Exception as e:
            print(f"Error during scan: {e}")
            
        return active_hosts
    
    def get_hostname(self, ip: str) -> str:
        """Try to resolve hostname from IP"""
        try:
            hostname = socket.gethostbyaddr(ip)[0]
            return hostname
        except:
            return "Unknown"
    
    def get_geolocation_from_ip(self, ip: str) -> Dict:
        """
        Get approximate geolocation from IP address
        Note: This works for PUBLIC IPs only, not local network IPs
        """
        if ipaddress.ip_address(ip).is_private:
            return {
                "ip": ip,
                "type": "private",
                "coordinates": None,
                "note": "Private IP - no public geolocation available"
            }
        
        try:
            # Using a free IP geolocation API
            response = requests.get(f"http://ip-api.com/json/{ip}", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return {
                    "ip": ip,
                    "type": "public",
                    "coordinates": {
                        "latitude": data.get("lat"),
                        "longitude": data.get("lon")
                    },
                    "city": data.get("city"),
                    "region": data.get("regionName"),
                    "country": data.get("country"),
                    "isp": data.get("isp")
                }
        except Exception as e:
            return {"ip": ip, "error": str(e)}
        
        return {"ip": ip, "error": "Could not fetch geolocation"}
    
    def calculate_network_distance(self, target_ip: str, max_hops: int = 30) -> List[Dict]:
        """
        Calculate network distance (hops) to a target using traceroute
        """
        hops = []
        
        try:
            import platform
            
            # Platform-specific traceroute command
            if platform.system().lower() == 'windows':
                command = ['tracert', '-h', str(max_hops), target_ip]
            else:
                command = ['traceroute', '-m', str(max_hops), target_ip]
            
            print(f"\nTracing route to {target_ip}...")
            print("Note: This requires network tools to be installed\n")
            
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=60,
                text=True
            )
            
            if result.returncode == 0:
                print(result.stdout)
                return [{"route": "See output above"}]
            else:
                print(f"Traceroute not available or failed: {result.stderr}")
                return [{"error": "Traceroute not available"}]
                
        except FileNotFoundError:
            print("Traceroute tool not found on system")
            return [{"error": "Traceroute not installed"}]
        except Exception as e:
            print(f"Error running traceroute: {e}")
            return [{"error": str(e)}]
    
    def create_network_graph_data(self, active_hosts: List[str]) -> Dict:
        """
        Create graph data structure for network visualization
        """
        nodes = []
        edges = []
        
        # Get local IP as central node
        local_ip = self.get_local_ip()
        
        # Add local machine as central node
        nodes.append({
            "id": local_ip,
            "label": f"This Device\n{local_ip}",
            "type": "local",
            "hostname": socket.gethostname()
        })
        
        # Add discovered devices
        for ip in active_hosts:
            hostname = self.get_hostname(ip)
            nodes.append({
                "id": ip,
                "label": f"{hostname}\n{ip}",
                "type": "discovered",
                "hostname": hostname
            })
            
            # Create edge from local to discovered device
            edges.append({
                "from": local_ip,
                "to": ip,
                "label": "same network"
            })
        
        return {
            "nodes": nodes,
            "edges": edges,
            "network_info": {
                "local_ip": local_ip,
                "total_devices": len(nodes),
                "network_type": "Local Area Network (LAN)"
            }
        }


def main():
    print("=" * 60)
    print("NETWORK DEVICE MAPPER")
    print("=" * 60)
    
    mapper = NetworkMapper()
    
    # 1. Get local network information
    print("\n1. LOCAL NETWORK INFORMATION")
    print("-" * 60)
    local_ip = mapper.get_local_ip()
    print(f"Your IP Address: {local_ip}")
    
    network_range = mapper.get_network_range(local_ip)
    print(f"Network Range: {network_range}")
    
    # 2. Scan for active devices
    print("\n2. SCANNING FOR DEVICES ON LOCAL NETWORK")
    print("-" * 60)
    active_hosts = mapper.scan_network_ping(network_range)
    
    print(f"\n✓ Found {len(active_hosts)} active devices")
    
    # 3. Get hostnames
    print("\n3. DEVICE DETAILS")
    print("-" * 60)
    for ip in active_hosts:
        hostname = mapper.get_hostname(ip)
        print(f"IP: {ip:15} | Hostname: {hostname}")
    
    # 4. Create network graph
    print("\n4. NETWORK TOPOLOGY GRAPH DATA")
    print("-" * 60)
    graph_data = mapper.create_network_graph_data(active_hosts)
    print(json.dumps(graph_data, indent=2))
    
    # 5. Geolocation example (for public IP)
    print("\n5. GEOLOCATION (PUBLIC IP EXAMPLE)")
    print("-" * 60)
    print("Checking your public IP location...")
    try:
        public_ip_response = requests.get("https://api.ipify.org", timeout=5)
        public_ip = public_ip_response.text
        print(f"Your public IP: {public_ip}")
        
        location = mapper.get_geolocation_from_ip(public_ip)
        print(json.dumps(location, indent=2))
    except Exception as e:
        print(f"Could not fetch public IP: {e}")
    
    # 6. Network distance example
    print("\n6. NETWORK DISTANCE EXAMPLE")
    print("-" * 60)
    print("Example: Measuring hops to Google DNS (8.8.8.8)")
    mapper.calculate_network_distance("8.8.8.8", max_hops=15)
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"""
Key Points:
1. LOCAL NETWORK DEVICES: Can be discovered via ping/ARP scanning
   - Geographic coordinates: NOT available (they're on your local network)
   - Network distance: 0 hops (same LAN segment)
   
2. REMOTE DEVICES (Internet): 
   - Geographic coordinates: Available via IP geolocation APIs
   - Network distance: Measured in hops via traceroute
   
3. For production use:
   - Use nmap for comprehensive network scanning
   - Use SNMP for managed network devices
   - Use network management tools for enterprise networks
    """)


if __name__ == "__main__":
    main()