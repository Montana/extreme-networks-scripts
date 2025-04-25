#!/usr/bin/env python3

import requests
import json
import argparse
import sys
import logging
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class ExtremeNetworksController:
    def __init__(self, host, username, password, port=443, use_https=True):
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.protocol = "https" if use_https else "http"
        self.base_url = f"{self.protocol}://{self.host}:{self.port}"
        self.token = None
        self.logger = self._setup_logger()
        
    def _setup_logger(self):
        logger = logging.getLogger("ExtremeNetworksController")
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger
        
    def authenticate(self):
        auth_url = f"{self.base_url}/auth/token/"
        payload = {"username": self.username, "password": self.password}
        try:
            response = requests.post(
                auth_url,
                headers={"Content-Type": "application/json"},
                json=payload,
                verify=False
            )
            if response.status_code == 200:
                self.token = response.json().get("token")
                self.logger.info("Authentication successful")
                return True
            else:
                self.logger.error(f"Authentication failed: {response.text}")
                return False
        except Exception as e:
            self.logger.error(f"Error during authentication: {str(e)}")
            return False
    
    def get_headers(self):
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if self.token:
            headers["X-Auth-Token"] = self.token
        return headers
    
    def get_vlans(self):
        if not self.token and not self.authenticate():
            return None
        url = f"{self.base_url}/restconf/data/openconfig-vlan:vlans"
        try:
            response = requests.get(url, headers=self.get_headers(), verify=False)
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"Failed to get VLANs: {response.text}")
                return None
        except Exception as e:
            self.logger.error(f"Error getting VLANs: {str(e)}")
            return None
            
    def create_vlan(self, vlan_id, vlan_name, description=None):
        if not self.token and not self.authenticate():
            return False
        url = f"{self.base_url}/restconf/data/openconfig-vlan:vlans"
        vlan_data = {
            "openconfig-vlan:vlans": {
                "vlan": [
                    {
                        "vlan-id": vlan_id,
                        "config": {
                            "vlan-id": vlan_id,
                            "name": vlan_name
                        }
                    }
                ]
            }
        }
        if description:
            vlan_data["openconfig-vlan:vlans"]["vlan"][0]["config"]["description"] = description
        try:
            response = requests.post(url, headers=self.get_headers(), json=vlan_data, verify=False)
            if response.status_code in [200, 201, 204]:
                self.logger.info(f"VLAN {vlan_id} created successfully")
                return True
            else:
                self.logger.error(f"Failed to create VLAN {vlan_id}: {response.text}")
                return False
        except Exception as e:
            self.logger.error(f"Error creating VLAN {vlan_id}: {str(e)}")
            return False
    
    def delete_vlan(self, vlan_id):
        if not self.token and not self.authenticate():
            return False
        url = f"{self.base_url}/restconf/data/openconfig-vlan:vlans/vlan={vlan_id}"
        try:
            response = requests.delete(url, headers=self.get_headers(), verify=False)
            if response.status_code in [200, 204]:
                self.logger.info(f"VLAN {vlan_id} deleted successfully")
                return True
            else:
                self.logger.error(f"Failed to delete VLAN {vlan_id}: {response.text}")
                return False
        except Exception as e:
            self.logger.error(f"Error deleting VLAN {vlan_id}: {str(e)}")
            return False
    
    def get_interfaces(self):
        if not self.token and not self.authenticate():
            return None
        url = f"{self.base_url}/restconf/data/openconfig-interfaces:interfaces"
        try:
            response = requests.get(url, headers=self.get_headers(), verify=False)
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"Failed to get interfaces: {response.text}")
                return None
        except Exception as e:
            self.logger.error(f"Error getting interfaces: {str(e)}")
            return None
    
    def configure_interface(self, interface_name, admin_status="up", description=None, mtu=None):
        if not self.token and not self.authenticate():
            return False
        url = f"{self.base_url}/restconf/data/openconfig-interfaces:interfaces/interface={interface_name}"
        interface_data = {
            "openconfig-interfaces:interface": [
                {
                    "name": interface_name,
                    "config": {
                        "name": interface_name,
                        "enabled": True if admin_status.lower() == "up" else False
                    }
                }
            ]
        }
        if description:
            interface_data["openconfig-interfaces:interface"][0]["config"]["description"] = description
        if mtu:
            interface_data["openconfig-interfaces:interface"][0]["config"]["mtu"] = int(mtu)
        try:
            response = requests.patch(url, headers=self.get_headers(), json=interface_data, verify=False)
            if response.status_code in [200, 204]:
                self.logger.info(f"Interface {interface_name} configured successfully")
                return True
            else:
                self.logger.error(f"Failed to configure interface {interface_name}: {response.text}")
                return False
        except Exception as e:
            self.logger.error(f"Error configuring interface {interface_name}: {str(e)}")
            return False
    
    def add_vlan_to_interface(self, interface_name, vlan_id, tagged=True):
        if not self.token and not self.authenticate():
            return False
        url = f"{self.base_url}/restconf/data/openconfig-interfaces:interfaces/interface={interface_name}/openconfig-if-ethernet:ethernet/openconfig-vlan:switched-vlan"
        vlan_mode = "TRUNK" if tagged else "ACCESS"
        vlan_data = {
            "openconfig-vlan:switched-vlan": {
                "config": {
                    "interface-mode": vlan_mode
                }
            }
        }
        if tagged:
            vlan_data["openconfig-vlan:switched-vlan"]["config"]["trunk-vlans"] = [vlan_id]
        else:
            vlan_data["openconfig-vlan:switched-vlan"]["config"]["access-vlan"] = vlan_id
        try:
            response = requests.patch(url, headers=self.get_headers(), json=vlan_data, verify=False)
            if response.status_code in [200, 204]:
                vlan_type = "tagged" if tagged else "untagged"
                self.logger.info(f"Added VLAN {vlan_id} as {vlan_type} to interface {interface_name}")
                return True
            else:
                self.logger.error(f"Failed to add VLAN {vlan_id} to interface {interface_name}: {response.text}")
                return False
        except Exception as e:
            self.logger.error(f"Error adding VLAN {vlan_id} to interface {interface_name}: {str(e)}")
            return False
    
    def execute_cli_command(self, command):
        if not self.token and not self.authenticate():
            return None
        url = f"{self.base_url}/jsonrpc"
        payload = {
            "method": "cli",
            "params": [command],
            "id": 1,
            "jsonrpc": "2.0"
        }
        try:
            response = requests.post(url, headers=self.get_headers(), json=payload, verify=False)
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"Failed to execute command '{command}': {response.text}")
                return None
        except Exception as e:
            self.logger.error(f"Error executing command '{command}': {str(e)}")
            return None
    
    def configure_ospf(self, process_id, networks):
        if not self.token and not self.authenticate():
            return False
        url = f"{self.base_url}/restconf/data/openconfig-network-instance:network-instances/network-instance=default/protocols/protocol=OSPF,{process_id}"
        ospf_data = {
            "openconfig-network-instance:protocol": [
                {
                    "identifier": "OSPF",
                    "name": str(process_id),
                    "config": {
                        "identifier": "OSPF",
                        "name": str(process_id)
                    },
                    "ospf": {
                        "global": {
                            "config": {
                                "router-id": networks[0]["network"].split("/")[0]
                            }
                        },
                        "areas": {
                            "area": []
                        }
                    }
                }
            ]
        }
        area_networks = {}
        for network in networks:
            area = network["area"]
            if area not in area_networks:
                area_networks[area] = []
            area_networks[area].append(network["network"])
        for area, nets in area_networks.items():
            area_data = {
                "identifier": int(area),
                "config": {
                    "identifier": int(area)
                },
                "interfaces": {
                    "interface": []
                }
            }
            for net in nets:
                net_addr = net.split("/")[0]
                area_data["interfaces"]["interface"].append({
                    "id": f"network_{net_addr.replace('.', '_')}",
                    "config": {
                        "id": f"network_{net_addr.replace('.', '_')}",
                        "network": net
                    }
                })
            ospf_data["openconfig-network-instance:protocol"][0]["ospf"]["areas"]["area"].append(area_data)
        try:
            response = requests.put(url, headers=self.get_headers(), json=ospf_data, verify=False)
            if response.status_code in [200, 201, 204]:
                self.logger.info(f"OSPF process {process_id} configured successfully")
                return True
            else:
                self.logger.error(f"Failed to configure OSPF: {response.text}")
                return False
        except Exception as e:
            self.logger.error(f"Error configuring OSPF: {str(e)}")
            return False
    
    def save_configuration(self):
        result = self.execute_cli_command("save configuration")
        if result and "error" not in result:
            self.logger.info("Configuration saved successfully")
            return True
        else:
            self.logger.error("Failed to save configuration")
            return False

def main():
    parser = argparse.ArgumentParser(description="Extreme Networks Switch Controller")
    parser.add_argument("--host", required=True, help="Switch IP address or hostname")
    parser.add_argument("--username", required=True, help="Switch username")
    parser.add_argument("--password", required=True, help="Switch password")
    parser.add_argument("--port", type=int, default=443, help="HTTP/HTTPS port (default: 443)")
    parser.add_argument("--no-https", action="store_true", help="Use HTTP instead of HTTPS")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    vlan_parser = subparsers.add_parser("vlan", help="VLAN operations")
    vlan_subparsers = vlan_parser.add_subparsers(dest="vlan_action", help="VLAN action")
    vlan_list_parser = vlan_subparsers.add_parser("list", help="List all VLANs")
    vlan_create_parser = vlan_subparsers.add_parser("create", help="Create a VLAN")
    vlan_create_parser.add_argument("--id", type=int, required=True, help="VLAN ID (1-4094)")
    vlan_create_parser.add_argument("--name", required=True, help="VLAN name")
    vlan_create_parser.add_argument("--description", help="VLAN description")
    vlan_delete_parser = vlan_subparsers.add_parser("delete", help="Delete a VLAN")
    vlan_delete_parser.add_argument("--id", type=int, required=True, help="VLAN ID to delete")
    
    interface_parser = subparsers.add_parser("interface", help="Interface operations")
    interface_subparsers = interface_parser.add_subparsers(dest="interface_action", help="Interface action")
    interface_list_parser = interface_subparsers.add_parser("list", help="List all interfaces")
    interface_config_parser = interface_subparsers.add_parser("configure", help="Configure an interface")
    interface_config_parser.add_argument("--name", required=True, help="Interface name")
    interface_config_parser.add_argument("--status", choices=["up", "down"], default="up", help="Administrative status")
    interface_config_parser.add_argument("--description", help="Interface description")
    interface_config_parser.add_argument("--mtu", type=int, help="Interface MTU")
    interface_vlan_parser = interface_subparsers.add_parser("add-vlan", help="Add VLAN to interface")
    interface_vlan_parser.add_argument("--name", required=True, help="Interface name")
    interface_vlan_parser.add_argument("--vlan-id", type=int, required=True, help="VLAN ID to add")
    interface_vlan_parser.add_argument("--tagged", action="store_true", default=True, help="Add as tagged VLAN (default)")
    interface_vlan_parser.add_argument("--untagged", action="store_true", help="Add as untagged VLAN")
    
    cli_parser = subparsers.add_parser("cli", help="Execute CLI command")
    cli_parser.add_argument("--command", required=True, help="CLI command to execute")
    save_parser = subparsers.add_parser("save", help="Save configuration")
    
    args = parser.parse_args()
    controller = ExtremeNetworksController(args.host, args.username, args.password, args.port, not args.no_https)
    if not controller.authenticate():
        sys.exit(1)
    
    if args.command == "vlan":
        if args.vlan_action == "list":
            vlans = controller.get_vlans()
            if vlans:
                print(json.dumps(vlans, indent=2))
        elif args.vlan_action == "create":
            success = controller.create_vlan(args.id, args.name, args.description)
            if not success:
                sys.exit(1)
        elif args.vlan_action == "delete":
            success = controller.delete_vlan(args.id)
            if not success:
                sys.exit(1)
    elif args.command == "interface":
        if args.interface_action == "list":
            interfaces = controller.get_interfaces()
            if interfaces:
                print(json.dumps(interfaces, indent=2))
        elif args.interface_action == "configure":
            success = controller.configure_interface(args.name, args.status, args.description, args.mtu)
            if not success:
                sys.exit(1)
        elif args.interface_action == "add-vlan":
            tagged = not args.untagged if args.untagged else args.tagged
            success = controller.add_vlan_to_interface(args.name, args.vlan_id, tagged)
            if not success:
                sys.exit(1)
    elif args.command == "cli":
        result = controller.execute_cli_command(args.command)
        if result:
            print(json.dumps(result, indent=2))
        else:
            sys.exit(1)
    elif args.command == "save":
        success = controller.save_configuration()
        if not success:
            sys.exit(1)

if __name__ == "__main__":
    main()
