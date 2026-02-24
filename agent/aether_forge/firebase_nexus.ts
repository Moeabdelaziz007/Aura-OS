/**
 * 🌌 AetherOS — Firebase CloudNexus (Firebase SDK Migration)
 * ===================================================
 * Firebase SDK بديلاً لـ Google Cloud SDK
 * Connects the local AetherForge to Firestore for collective intelligence.
 */

import * as admin from 'firebase-admin';
import { logger } from 'firebase-functions';

interface ExecutionLog {
  agentId: string;
  taskType: string;
  parameters: any;
  status: 'running' | 'completed' | 'failed';
  startTime: admin.firestore.FieldValue;
  endTime?: admin.firestore.FieldValue;
  result?: any;
  error?: any;
  userId: string;
  memoryUsage?: any;
  cpuUsage?: any;
  executionTime?: number;
}

interface SwarmPattern {
  patternId: string;
  patternType: string;
  successRate: number;
  averageExecutionTime: number;
  usageCount: number;
  lastUsed: admin.firestore.FieldValue;
  metadata: any;
}

interface TelemetryData {
  timestamp: admin.firestore.FieldValue;
  metricType: string;
  value: number;
  metadata?: any;
}

export class AetherFirebaseNexus {
  private db: admin.firestore.Firestore;
  private projectId: string;
  
  constructor(projectId?: string) {
    this.projectId = projectId || process.env.FIREBASE_PROJECT_ID || 'aether-os-firebase';
    
    // Initialize Firebase Admin if not already initialized
    if (!admin.apps.length) {
      try {
        const serviceAccountPath = process.env.FIREBASE_SERVICE_ACCOUNT_PATH;
        if (serviceAccountPath) {
          admin.initializeApp({
            credential: admin.credential.cert(serviceAccountPath),
            databaseURL: `https://${this.projectId}.firebaseio.com`
          });
        } else {
          // Use default credentials
          admin.initializeApp({
            databaseURL: `https://${this.projectId}.firebaseio.com`
          });
        }
        logger.info('✅ Firebase Admin initialized successfully');
      } catch (error) {
        logger.error('❌ Firebase Admin initialization failed:', error);
        throw error;
      }
    }
    
    this.db = admin.firestore();
    logger.info(`🌌 FirebaseNexus: Connected to project ${this.projectId}`);
  }

  /**
   * 🔥 Store swarm execution data in Firestore
   */
  async storeExecution(executionLog: ExecutionLog): Promise<string> {
    try {
      const docRef = await this.db.collection('swarm_executions').add(executionLog);
      logger.info(`📊 Execution stored: ${docRef.id}`);
      return docRef.id;
    } catch (error) {
      logger.error('❌ Failed to store execution:', error);
      throw error;
    }
  }

  /**
   * 📈 Update execution status
   */
  async updateExecutionStatus(
    executionId: string, 
    status: 'completed' | 'failed', 
    result?: any, 
    error?: any
  ): Promise<void> {
    try {
      const updateData: any = {
        status,
        endTime: admin.firestore.FieldValue.serverTimestamp()
      };

      if (result) updateData.result = result;
      if (error) updateData.error = error;

      await this.db.collection('swarm_executions').doc(executionId).update(updateData);
      logger.info(`✅ Execution ${executionId} updated to ${status}`);
    } catch (error) {
      logger.error(`❌ Failed to update execution ${executionId}:`, error);
      throw error;
    }
  }

  /**
   * 🧠 Store successful patterns for machine learning
   */
  async storePattern(pattern: SwarmPattern): Promise<string> {
    try {
      const docRef = await this.db.collection('swarm_patterns').add(pattern);
      logger.info(`🧠 Pattern stored: ${docRef.id}`);
      return docRef.id;
    } catch (error) {
      logger.error('❌ Failed to store pattern:', error);
      throw error;
    }
  }

  /**
   * 🔍 Retrieve patterns by type with success rate filtering
   */
  async getPatternsByType(
    patternType: string, 
    minSuccessRate: number = 0.8, 
    limit: number = 10
  ): Promise<SwarmPattern[]> {
    try {
      const snapshot = await this.db
        .collection('swarm_patterns')
        .where('patternType', '==', patternType)
        .where('successRate', '>=', minSuccessRate)
        .orderBy('successRate', 'desc')
        .limit(limit)
        .get();

      const patterns: SwarmPattern[] = [];
      snapshot.forEach(doc => {
        patterns.push({ id: doc.id, ...doc.data() } as SwarmPattern);
      });

      logger.info(`🔍 Retrieved ${patterns.length} patterns of type ${patternType}`);
      return patterns;
    } catch (error) {
      logger.error(`❌ Failed to retrieve patterns for ${patternType}:`, error);
      throw error;
    }
  }

  /**
   * 📊 Store telemetry data
   */
  async storeTelemetry(telemetryData: TelemetryData): Promise<string> {
    try {
      const docRef = await this.db.collection('telemetry').add(telemetryData);
      logger.debug(`📊 Telemetry stored: ${docData.ref.id}`);
      return docRef.id;
    } catch (error) {
      logger.error('❌ Failed to store telemetry:', error);
      throw error;
    }
  }

  /**
   * 📈 Get telemetry data for time range
   */
  async getTelemetry(
    metricType: string, 
    startTime: Date, 
    endTime: Date
  ): Promise<TelemetryData[]> {
    try {
      const snapshot = await this.db
        .collection('telemetry')
        .where('metricType', '==', metricType)
        .where('timestamp', '>=', startTime)
        .where('timestamp', '<=', endTime)
        .orderBy('timestamp', 'desc')
        .get();

      const telemetry: TelemetryData[] = [];
      snapshot.forEach(doc => {
        telemetry.push({ id: doc.id, ...doc.data() } as TelemetryData);
      });

      return telemetry;
    } catch (error) {
      logger.error(`❌ Failed to retrieve telemetry for ${metricType}:`, error);
      throw error;
    }
  }

  /**
   * 🔄 Real-time pattern updates based on execution results
   */
  async updatePatternStats(
    patternId: string, 
    executionTime: number, 
    success: boolean
  ): Promise<void> {
    try {
      const patternRef = this.db.collection('swarm_patterns').doc(patternId);
      
      await this.db.runTransaction(async (transaction) => {
        const doc = await transaction.get(patternRef);
        
        if (!doc.exists) {
          logger.warn(`⚠️ Pattern ${patternId} not found`);
          return;
        }

        const data = doc.data() as SwarmPattern;
        const newUsageCount = data.usageCount + 1;
        const newSuccessRate = success ? 
          ((data.successRate * data.usageCount) + 1) / newUsageCount :
          (data.successRate * data.usageCount) / newUsageCount;
        
        const newAverageExecutionTime = 
          ((data.averageExecutionTime * data.usageCount) + executionTime) / newUsageCount;

        transaction.update(patternRef, {
          successRate: newSuccessRate,
          usageCount: newUsageCount,
          averageExecutionTime: newAverageExecutionTime,
          lastUsed: admin.firestore.FieldValue.serverTimestamp()
        });
      });

      logger.info(`🔄 Pattern ${patternId} stats updated`);
    } catch (error) {
      logger.error(`❌ Failed to update pattern stats for ${patternId}:`, error);
      throw error;
    }
  }

  /**
   * 🧬 Get evolutionary insights
   */
  async getEvolutionaryInsights(): Promise<any> {
    try {
      // Get patterns with highest improvement rate
      const improvingPatterns = await this.db
        .collection('swarm_patterns')
        .where('successRate', '>', 0.9)
        .orderBy('successRate', 'desc')
        .limit(5)
        .get();

      // Get recently successful executions
      const recentSuccesses = await this.db
        .collection('swarm_executions')
        .where('status', '==', 'completed')
        .where('startTime', '>', admin.firestore.Timestamp.fromDate(new Date(Date.now() - 24 * 60 * 60 * 1000)))
        .orderBy('startTime', 'desc')
        .limit(10)
        .get();

      const insights = {
        topPatterns: improvingPatterns.docs.map(doc => ({ id: doc.id, ...doc.data() })),
        recentSuccesses: recentSuccesses.docs.map(doc => ({ id: doc.id, ...doc.data() })),
        timestamp: admin.firestore.FieldValue.serverTimestamp()
      };

      return insights;
    } catch (error) {
      logger.error('❌ Failed to get evolutionary insights:', error);
      throw error;
    }
  }

  /**
   * 🏥 Health check for Firebase connection
   */
  async healthCheck(): Promise<boolean> {
    try {
      const healthDoc = {
        timestamp: admin.firestore.FieldValue.serverTimestamp(),
        status: 'healthy',
        projectId: this.projectId
      };

      await this.db.collection('health_checks').add(healthDoc);
      logger.info('🏥 FirebaseNexus health check passed');
      return true;
    } catch (error) {
      logger.error('❌ FirebaseNexus health check failed:', error);
      return false;
    }
  }

  /**
   * 📊 Batch operations for performance optimization
   */
  async batchStoreExecutions(executions: ExecutionLog[]): Promise<string[]> {
    try {
      const batch = this.db.batch();
      const docRefs: admin.firestore.DocumentReference[] = [];

      executions.forEach(execution => {
        const docRef = this.db.collection('swarm_executions').doc();
        batch.set(docRef, execution);
        docRefs.push(docRef);
      });

      await batch.commit();
      
      const ids = docRefs.map(ref => ref.id);
      logger.info(`📊 Batch stored ${executions.length} executions`);
      return ids;
    } catch (error) {
      logger.error('❌ Batch execution storage failed:', error);
      throw error;
    }
  }
}

// Export singleton instance
export const firebaseNexus = new AetherFirebaseNexus();