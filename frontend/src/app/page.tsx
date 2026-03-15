import Link from 'next/link';

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white">
      <nav className="container mx-auto px-6 py-4">
        <div className="flex justify-between items-center">
          <div className="text-2xl font-bold text-blue-600">LegalLens</div>
          <div className="space-x-4">
            <Link href="/login" className="text-gray-700 hover:text-blue-600">
              Login
            </Link>
            <Link
              href="/register"
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
            >
              Get Started
            </Link>
          </div>
        </div>
      </nav>

      <main className="container mx-auto px-6 py-16">
        <div className="text-center max-w-4xl mx-auto">
          <h1 className="text-5xl font-bold text-gray-900 mb-6">
            Understand Your Legal Documents with AI
          </h1>
          <p className="text-xl text-gray-600 mb-8">
            Upload any legal document and get instant analysis in plain language.
            Perfect for rental agreements, employment contracts, and more.
          </p>
          <Link
            href="/register"
            className="inline-block bg-blue-600 text-white px-8 py-4 rounded-lg text-lg font-semibold hover:bg-blue-700"
          >
            Analyze Your First Document Free
          </Link>
        </div>

        <div className="grid md:grid-cols-3 gap-8 mt-16">
          <div className="text-center p-6">
            <div className="text-4xl mb-4">📄</div>
            <h3 className="text-xl font-semibold mb-2">Upload Document</h3>
            <p className="text-gray-600">
              PDF, DOCX, or image files supported
            </p>
          </div>
          <div className="text-center p-6">
            <div className="text-4xl mb-4">🤖</div>
            <h3 className="text-xl font-semibold mb-2">AI Analysis</h3>
            <p className="text-gray-600">
              Get plain-language explanations and risk alerts
            </p>
          </div>
          <div className="text-center p-6">
            <div className="text-4xl mb-4">✅</div>
            <h3 className="text-xl font-semibold mb-2">Make Informed Decisions</h3>
            <p className="text-gray-600">
              Understand clauses and negotiate better terms
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
