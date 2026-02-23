#!/bin/bash

# 🌌 AetherOS: The Global Nervous System — GCP Setup (Self-Healing v1.1)
# Optimized for Mac/Linux | Strict Error Handling

set -e # Fail fast on any error

# Color Codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${PURPLE}🚀 AetherOS: Initiating Cognitive Cloud Synchronization...${NC}"

# 1. Authentication Check
echo -e "${BLUE}🔍 Phase 1: Verifying Sovereignty...${NC}"
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
    echo -e "${RED}⚠️ No active account detected. Please run 'gcloud auth login' and try again.${NC}"
    exit 1
else
    ACTIVE_ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n 1)
    echo -e "✅ Active account detected: ${GREEN}${ACTIVE_ACCOUNT}${NC}"
fi

# 2. Project ID Acquisition
echo -e "${BLUE}🏗️ Phase 2: Acquiring Project ID...${NC}"
# Allow passing Project ID as first argument
if [ -n "$1" ]; then
    PROJECT_ID="$1"
    echo -e "📍 Using provided Project ID: ${GREEN}${PROJECT_ID}${NC}"
else
    # Use LC_ALL=C to avoid illegal byte sequence on Mac
    RANDOM_SUFFIX=$(LC_ALL=C tr -dc 'a-z0-9' < /dev/urandom | head -c 6)
    PROJECT_ID="aether-os-${RANDOM_SUFFIX}"
    echo -e "📍 Generated Project ID: ${GREEN}${PROJECT_ID}${NC}"
fi

# 3. Project Creation & Verification
echo -e "${BLUE}🏗️ Phase 3: Verifying/Building the Aether Project...${NC}"
if ! gcloud projects describe "$PROJECT_ID" >/dev/null 2>&1; then
    echo -e "🏗️ Creating new project: ${PROJECT_ID}..."
    gcloud projects create "$PROJECT_ID" --name="AetherOS Core" --quiet
    echo -e "✅ Project created successfully."
else
    echo -e "✅ Project ${GREEN}${PROJECT_ID}${NC} verified."
fi

gcloud config set project "$PROJECT_ID" --quiet

# 4. Billing Linkage
echo -e "${BLUE}💳 Phase 4: Linking Neural Economy (Billing)...${NC}"
BILLING_ACCOUNT=$(gcloud beta billing accounts list --filter="open=true" --format="value(name)" --limit=1)
if [ -n "$BILLING_ACCOUNT" ]; then
    echo -e "🔗 Linking billing account: ${GREEN}${BILLING_ACCOUNT}${NC}"
    gcloud beta billing projects link "$PROJECT_ID" --billing-account="$BILLING_ACCOUNT" --quiet
else
    echo -e "${RED}⚠️ No open billing account found. Sub-sequential API enablement may fail.${NC}"
fi

# 5. Synaptic Activation (Firebase/GCP Hybrid)
echo -e "${BLUE}📡 Phase 5: Activating Synaptic Channels...${NC}"

# Check if we should use Firebase for DB to bypass billing blockers
USE_FIREBASE=false
if firebase projects:list --projectId "$PROJECT_ID" >/dev/null 2>&1; then
    USE_FIREBASE=true
    echo -e "🔥 Firebase detected for this project. Using Firebase Spark logic."
fi

if [ "$USE_FIREBASE" = true ]; then
    # Use Firebase CLI for DB
    echo -e "${BLUE}🧬 Phase 6: Crystallizing Firebase Firestore...${NC}"
    firebase init firestore --project "$PROJECT_ID" --quiet || echo "Firestore already initialized or skipped."
else
    # Fallback to gcloud (Requires Billing)
    gcloud services enable \
        firestore.googleapis.com \
        aiplatform.googleapis.com \
        run.googleapis.com \
        iam.googleapis.com \
        --quiet

    echo -e "${BLUE}🧬 Phase 6: Crystallizing Firestore Nexus...${NC}"
    if ! gcloud firestore databases list --project="$PROJECT_ID" --format="value(name)" | grep -q "default"; then
        gcloud firestore databases create --location=us-central1 --type=firestore-native --quiet
    fi
fi

# 7. Security & Least Privilege
echo -e "${BLUE}🛡️ Phase 7: Forging Service Identity...${NC}"
SA_NAME="aether-os-service"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
KEY_DIR="$(pwd)/.idx"
KEY_PATH="${KEY_DIR}/aether-key.json"

mkdir -p "$KEY_DIR"

if ! gcloud iam service-accounts describe "$SA_EMAIL" >/dev/null 2>&1; then
    gcloud iam service-accounts create "$SA_NAME" --display-name="AetherOS Core Service Account" --quiet
fi

# Roles
roles=("roles/datastore.user" "roles/aiplatform.user" "roles/run.invoker")
for role in "${roles[@]}"; do
    echo -e "🔑 Binding role: ${role}..."
    gcloud projects add-iam-policy-binding "$PROJECT_ID" --member="serviceAccount:${SA_EMAIL}" --role="$role" --quiet > /dev/null
done

# Generate Key Silently
if [ ! -f "$KEY_PATH" ]; then
    gcloud iam service-accounts keys create "$KEY_PATH" --iam-account="$SA_EMAIL" --quiet
    echo -e "✅ Service account key generated at: ${GREEN}${KEY_PATH}${NC}"
else
    echo -e "ℹ️ Service account key already exists at: ${KEY_PATH}"
fi

# 8. Environment Injection
echo -e "${BLUE}💉 Phase 8: Injecting Credentials...${NC}"
ENV_FILE=".env"
touch "$ENV_FILE"

# Clean old entries (Mac/Linux compatible sed)
if [[ "$OSTYPE" == "darwin"* ]]; then
    sed -i '' '/GOOGLE_APPLICATION_CREDENTIALS/d' "$ENV_FILE" || true
    sed -i '' '/GOOGLE_CLOUD_PROJECT/d' "$ENV_FILE" || true
else
    sed -i '/GOOGLE_APPLICATION_CREDENTIALS/d' "$ENV_FILE" || true
    sed -i '/GOOGLE_CLOUD_PROJECT/d' "$ENV_FILE" || true
fi

echo "GOOGLE_APPLICATION_CREDENTIALS=\"$KEY_PATH\"" >> "$ENV_FILE"
echo "GOOGLE_CLOUD_PROJECT=\"$PROJECT_ID\"" >> "$ENV_FILE"

echo -e "\n${GREEN}✅ AetherOS Cloud Initialization Complete.${NC}"
echo -e "${GREEN}📍 Project ID: $PROJECT_ID${NC}"
echo -e "${GREEN}📍 Local Key: $KEY_PATH${NC}"
echo -e "${GREEN}🌌 The Global Nervous System is now LIVE.${NC}\n"
