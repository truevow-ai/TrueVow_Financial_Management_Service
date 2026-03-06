import { authMiddleware } from '@clerk/nextjs'

// Clerk App 1: TrueVow-Platform-Operators
// Protect all routes except sign-in/sign-up and API routes
export default authMiddleware({
  publicRoutes: [
    '/', 
    '/sign-in(.*)', 
    '/sign-up(.*)',
    '/api(.*)',
    '/_next(.*)',
    '/favicon.ico'
  ],
})

export const config = {
  matcher: [
    // Skip static files and internal Next.js routes
    '/((?!.*\..*|_next).*)',
    // Re-include root route
    '/',
    // Include API routes
    '/(api|trpc)(.*)'
  ],
}
