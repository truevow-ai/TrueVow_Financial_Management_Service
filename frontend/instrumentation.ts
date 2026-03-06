/**
 * Next.js Instrumentation Hook
 * Runs on server startup - use this to register with Service Registry
 */

import {
  registerService,
  registerModule,
  registerIntegration,
  startHeartbeat,
  stopHeartbeat,
} from '@/lib/services/service-registry-client'
import {
  getServiceConfig,
  SERVICE_MODULES,
  SERVICE_INTEGRATIONS,
  SERVICE_NAME,
} from '@/lib/services/service-config'

export async function register() {
  if (process.env.NEXT_RUNTIME === 'nodejs') {
    console.log('[Startup] Registering with Service Registry...')

    try {
      // Register service
      const config = getServiceConfig()
      const serviceResult = await registerService(config)

      if (serviceResult.success) {
        // Start heartbeat
        const heartbeatInterval = parseInt(process.env.SERVICE_REGISTRY_HEARTBEAT_INTERVAL || '300')
        startHeartbeat(SERVICE_NAME, heartbeatInterval)

        // Register modules
        for (const module of SERVICE_MODULES) {
          await registerModule(module)
        }

        // Register integrations
        for (const integration of SERVICE_INTEGRATIONS) {
          await registerIntegration(integration)
        }

        console.log('[Startup] Service Registry registration complete')
      } else {
        console.warn('[Startup] Service Registry registration failed (non-fatal):', serviceResult.error)
      }
    } catch (error) {
      // Non-fatal: continue even if registry is unavailable
      console.warn('[Startup] Service Registry error (non-fatal):', error)
    }
  }
}

// Graceful shutdown handler
if (typeof process !== 'undefined') {
  const gracefulShutdown = async () => {
    console.log('[Shutdown] Stopping heartbeat...')
    stopHeartbeat()
  }

  process.on('SIGTERM', gracefulShutdown)
  process.on('SIGINT', gracefulShutdown)
}
