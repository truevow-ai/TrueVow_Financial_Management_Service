'use client'

import { useUser } from '@clerk/nextjs'

export default function TestClerkPage() {
  const { isLoaded, isSignedIn, user } = useUser()

  if (!isLoaded) {
    return <div>Loading...</div>
  }

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">Clerk Authentication Test</h1>
      
      {isSignedIn ? (
        <div className="space-y-4">
          <div className="p-4 bg-green-50 rounded-lg">
            <h2 className="text-lg font-semibold text-green-800">✅ User is signed in</h2>
            <p className="text-green-700">Welcome, {user?.firstName || user?.emailAddresses[0]?.emailAddress}!</p>
            <p className="text-sm text-green-600">User ID: {user?.id}</p>
          </div>
          
          <div className="p-4 bg-blue-50 rounded-lg">
            <h3 className="font-medium text-blue-800">User Details:</h3>
            <pre className="text-sm text-blue-700 mt-2 bg-white p-2 rounded">
              {JSON.stringify({
                id: user?.id,
                firstName: user?.firstName,
                lastName: user?.lastName,
                email: user?.emailAddresses[0]?.emailAddress,
                createdAt: user?.createdAt,
              }, null, 2)}
            </pre>
          </div>
        </div>
      ) : (
        <div className="p-4 bg-yellow-50 rounded-lg">
          <h2 className="text-lg font-semibold text-yellow-800">⚠️ User is not signed in</h2>
          <p className="text-yellow-700">Please sign in to test authentication.</p>
        </div>
      )}
    </div>
  )
}