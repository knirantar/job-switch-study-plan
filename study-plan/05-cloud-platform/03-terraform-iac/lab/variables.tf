variable "environment" {
  type        = string
  description = "Short environment identity."
  default     = "dev"
  validation {
    condition     = contains(["dev", "test", "prod"], var.environment)
    error_message = "environment must be dev, test, or prod."
  }
}

variable "owner" {
  type        = string
  description = "Accountable team slug."
  default     = "platform-engineering"
  validation {
    condition     = length(trimspace(var.owner)) >= 3
    error_message = "owner must name an accountable team."
  }
}

variable "data_class" {
  type        = string
  description = "Governance classification, not raw sensitive data."
  default     = "internal"
  validation {
    condition     = contains(["public", "internal", "confidential", "restricted"], var.data_class)
    error_message = "Unsupported data classification."
  }
}

variable "cost_center" {
  type        = string
  description = "FinOps allocation code."
  default     = "CC-2401"
  validation {
    condition     = can(regex("^CC-[0-9]{4}$", var.cost_center))
    error_message = "cost_center must match CC-NNNN."
  }
}
