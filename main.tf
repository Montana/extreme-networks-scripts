terraform {
  required_providers {
    http = {
      source  = "hashicorp/http"
      version = "~> 3.4.0"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.2.1"
    }
  }
}

variable "api_key" {
  description = "API key for ExtremeCloud IQ"
  type        = string
  sensitive   = true
}

variable "cloud_url" {
  description = "URL for ExtremeCloud IQ instance"
  type        = string
  default     = "https://api.extremecloudiq.com"
}

variable "network_policy" {
  description = "Network policy configuration"
  type = object({
    name        = string
    description = string
    ssids       = list(object({
      name     = string
      password = string
      security = string
    }))
  })
}

locals {
  headers = {
    "X-API-KEY"    = var.api_key
    "Content-Type" = "application/json"
  }
}

resource "null_resource" "create_network_policy" {
  provisioner "local-exec" {
    command = <<-EOF
      curl -s -X POST \
        "${var.cloud_url}/xapi/v1/network-policies" \
        -H "X-API-KEY: ${var.api_key}" \
        -H "Content-Type: application/json" \
        -d '{
          "name": "${var.network_policy.name}",
          "description": "${var.network_policy.description}"
        }'
    EOF
  }
}

resource "null_resource" "create_ssids" {
  depends_on = [null_resource.create_network_policy]
  
  count = length(var.network_policy.ssids)
  
  provisioner "local-exec" {
    command = <<-EOF
      curl -s -X POST \
        "${var.cloud_url}/xapi/v1/network-policies/${var.network_policy.name}/ssids" \
        -H "X-API-KEY: ${var.api_key}" \
        -H "Content-Type: application/json" \
        -d '{
          "name": "${var.network_policy.ssids[count.index].name}",
          "password": "${var.network_policy.ssids[count.index].password}",
          "security": "${var.network_policy.ssids[count.index].security}"
        }'
    EOF
  }
}

output "network_policy" {
  value = var.network_policy.name
  description = "Created network policy name"
}

output "ssids" {
  value = [for ssid in var.network_policy.ssids : ssid.name]
  description = "Created SSIDs"
}
