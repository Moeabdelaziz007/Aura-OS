# ☁️ terraform/main.tf: Zero-Trust Swarm Provisioning
# Pillar: QuantumWeaver (Swarm Infrastructure)

provider "google" {
  project = var.project_id
  region  = "us-central1"
}

# 🛠️ Cloud Run Job: The QuantumWeaver Swarm Node
resource "google_cloud_run_v2_job" "swarm_node" {
  name     = "alpha-quantum-swarm-node"
  location = "us-central1"

  template {
    template {
      containers {
        image = "gcr.io/${var.project_id}/auraos-swarm-node:latest"
        
        resources {
          limits = {
            cpu    = "2"
            memory = "4Gi"
          }
        }

        # Environment Variables for Cognitive State Handover
        env {
          name  = "AURA_DNA_VERSION"
          value = "0.2.0"
        }
      }

      # High-Concurrency Parallelism
      parallelism = 50 
      task_count  = 100
      
      # Persistence & Security
      service_account = google_service_account.swarm_sa.email
    }
  }
}

# 🛡️ Least-Privilege Service Account
resource "google_service_account" "swarm_sa" {
  account_id   = "auraos-swarm-worker"
  display_name = "AuraOS Swarm Worker"
}

# IAM: Only allow Cloud Run Job execution permissions
resource "google_project_iam_member" "swarm_log_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.swarm_sa.email}"
}

# Variable Definitions
variable "project_id" {
  description = "Google Cloud Project ID"
  type        = str
}
