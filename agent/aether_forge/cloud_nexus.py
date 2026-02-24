"""
AetherOS — CloudNexus (Global Nervous System Bridge)
===================================================
Connects the local AetherForge to Firestore for collective intelligence.
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional

import firebase_admin
from firebase_admin import credentials, firestore

logger = logging.getLogger("aether.cloud_nexus")

class AetherCloudNexus:
    """The Firestore bridge for global pattern synchronization."""
    
    def __init__(self, project_id: Optional[str] = None, key_path: Optional[str] = None):
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
        self.key_path = key_path or os.getenv("FIREBASE_SERVICE_ACCOUNT")
        self._db = None
        
        if self.project_id and self.key_path:
            self._initialize()
        else:
            logger.warning("⚠️ CloudNexus: Missing credentials. Operating in Offline/Passive mode.")

    def _initialize(self):
        try:
            if not firebase_admin._apps:
                cred = None
                # Method 1: File-based Service Account
                if self.key_path and os.path.exists(self.key_path) and os.path.getsize(self.key_path) > 0:
                    logger.info(f"🔑 CloudNexus: Initializing via Service Account File: {self.key_path}")
                    cred = credentials.Certificate(self.key_path)
                
                # Method 2: Fallback to Environment Variable (Production-Grade)
                elif os.getenv("FIREBASE_CRED_JSON"):
                    logger.info("🔑 CloudNexus: Initializing via FIREBASE_CRED_JSON environment variable.")
                    import json
                    cred_dict = json.loads(os.getenv("FIREBASE_CRED_JSON"))
                    cred = credentials.Certificate(cred_dict)
                
                # Method 3: Fallback to Default Credentials (GCP Auth)
                else:
                    logger.warning("⚠️ No service account file or ENV found. Attempting Application Default Credentials...")
                    try:
                        cred = credentials.ApplicationDefault()
                    except Exception:
                        logger.error("❌ All credential methods failed. CloudNexus remains OFFLINE.")
                        return

                firebase_admin.initialize_app(cred, {
                    'projectId': self.project_id,
                })
            self._db = firestore.client()
            logger.info(f"🌌 CloudNexus initialized for project: {self.project_id}")
        except Exception as e:
            logger.error(f"❌ CloudNexus initialization failed: {e}")
            # Do NOT raise here, just stay offline to prevent orchestrator crash
            self._db = None

    async def aether_share_shadow_map(self, service: str, base_url: str, intent_action: str):
        """Register a shadow map in the global 'SharedShadowMaps' collection."""
        if not self._db: return
        
        try:
            doc_ref = self._db.collection("SharedShadowMaps").document(service)
            doc_ref.set({
                "service": service,
                "base_url": base_url,
                "intent_action": intent_action,
                "last_witnessed": firestore.SERVER_TIMESTAMP,
                "sovereignty_level": "VERIFIED"
            }, merge=True)
            logger.info(f"📡 Shadow Map shared globally for {service}")
        except Exception as e:
            logger.error(f"❌ Failed to share shadow map: {e}")

    async def aether_discover_global_patterns(self, service: str) -> Optional[Dict[str, Any]]:
        """Retrieve verified API contracts from the collective intelligence pool."""
        if not self._db: return None
        
        try:
            doc = self._db.collection("SharedShadowMaps").document(service).get()
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            logger.error(f"❌ Global pattern discovery failed: {e}")
            return None

    async def aether_get_agent_context(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Fetch persistent DNA for a specific NanoAgent."""
        if not self._db: return None
        try:
            doc = self._db.collection("AgentDNA").document(agent_id).get()
            return doc.to_dict() if doc.exists else None
        except Exception as e:
            logger.error(f"❌ Failed to fetch agent context: {e}")
            return None

    async def aether_update_agent_context(self, agent_id: str, context: Dict[str, Any]):
        """Persist final state changes for a NanoAgent."""
        if not self._db: return
        try:
            self._db.collection("AgentDNA").document(agent_id).set(context, merge=True)
        except Exception as e:
            logger.error(f"❌ Failed to update agent context: {e}")

    def verify_connectivity(self) -> bool:
        """Deterministic connection test."""
        try:
            test_ref = self._db.collection("SystemHealth").document("ping")
            test_ref.set({"last_ping": firestore.SERVER_TIMESTAMP})
            return True
        except Exception:
            return False
