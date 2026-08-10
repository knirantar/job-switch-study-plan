terraform {
  required_version = ">= 1.6.0, < 2.0.0"
}

locals {
  required_tags = {
    environment = var.environment
    owner       = var.owner
    data_class  = var.data_class
    managed_by  = "terraform"
    cost_center = var.cost_center
  }
  services = {
    api    = { replicas = 4, critical = true }
    worker = { replicas = 2, critical = false }
  }
}

# terraform_data is built into Terraform, so this lab validates without
# downloading a cloud provider or creating billable infrastructure.
resource "terraform_data" "service" {
  for_each = local.services
  input = {
    name     = each.key
    replicas = each.value.replicas
    tags     = local.required_tags
  }

  lifecycle {
    precondition {
      condition     = each.value.replicas >= (each.value.critical ? 3 : 1)
      error_message = "Critical services require at least three replicas."
    }
  }
}

check "regulated_production_classification" {
  assert {
    condition     = var.environment != "prod" || contains(["confidential", "restricted"], var.data_class)
    error_message = "Production must declare confidential or restricted data classification."
  }
}

output "service_plan" {
  value = { for name, resource in terraform_data.service : name => resource.output }
}
