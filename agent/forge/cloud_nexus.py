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

class CloudNexus:
    """The Firestore bridge for global pattern synchronization."""
    
    def __init__(self, project_id: str, key_path: str):
        self.project_id = project_id
        self.key_path = key_path
        self._db = None
        
        self._initialize()

    def _initialize(self):
        try:
            if not firebase_admin._apps:
                cred = credentials.Certificate(self.key_path)
                firebase_admin.initialize_app(cred, {
                    'projectId': self.project_id,
                })
            self._db = firestore.client()
            logger.info(f"🌌 CloudNexus initialized for project: {self.project_id}")
        except Exception as e:
            logger.error(f"❌ CloudNexus initialization failed: {e}")
            raise

    async def share_shadow_map(self, service: str, base_url: str, intent_action: str):
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

    async def discover_global_patterns(self, service: str) -> Optional[Dict[str, Any]]:
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

    def verify_connectivity(self) -> bool:
        """Deterministic connection test."""
        try:
            test_ref = self._db.collection("SystemHealth").document("ping")
            test_ref.set({"last_ping": firestore.SERVER_TIMESTAMP})
            return True
        except Exception:
            return False
