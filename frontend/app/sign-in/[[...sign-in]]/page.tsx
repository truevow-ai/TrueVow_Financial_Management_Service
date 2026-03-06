import { SignIn } from '@clerk/nextjs'

export default function SignInPage() {
  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-50">
      <div className="w-full max-w-md p-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">TrueVow Financial Management</h1>
          <p className="text-gray-600 mt-2">Sign in to access the financial management system</p>
        </div>
        <SignIn 
          appearance={{
            elements: {
              card: 'shadow-lg border border-gray-200',
              headerTitle: 'text-2xl font-bold text-gray-900',
              headerSubtitle: 'text-gray-600',
            }
          }}
          redirectUrl="/"
        />
      </div>
    </div>
  )
}
