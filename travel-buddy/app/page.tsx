import Link from "next/link"

export default function HomePage() {
  return (
    <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-blue-500 to-indigo-700">
      <div className="bg-white/90 backdrop-blur-md shadow-2xl rounded-2xl p-10 w-[380px] text-center">
        <h1 className="text-3xl font-bold mb-2">Travel Buddy</h1>
        <p className="text-gray-500 mb-6">Plan smarter routes across the city</p>
        <Link
          href="/dashboard"
          className="bg-black text-white rounded-lg p-3 hover:bg-gray-800 transition inline-block"
        >
          Go to Dashboard
        </Link>
      </div>
    </div>
  )
}