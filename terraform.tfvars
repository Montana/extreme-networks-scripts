extreme_host     = "extreme-switch.example.com"
extreme_username = "admin"
extreme_password = "securepassword"

extreme_vlans = [
  {
    id          = 10
    name        = "DATA-VLAN"
    description = "Data traffic VLAN"
  },
  {
    id          = 20
    name        = "VOICE-VLAN"
    description = "Voice traffic VLAN"
  },
  {
    id          = 30
    name        = "MGMT-VLAN"
    description = "Management VLAN"
  }
]

extreme_ports = [
  {
    port        = "1/1"
    description = "Server Port"
    vlan        = 10
    admin_state = "enabled"
  },
  {
    port        = "1/2"
    description = "Phone Port"
    vlan        = 20
    admin_state = "enabled"
  },
  {
    port        = "1/3"
    description = "Management Port"
    vlan        = 30
    admin_state = "enabled"
  }
]
