'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import api from '@/lib/api';
import { useAuthStore } from '@/store/authStore';
import { Document, User } from '@/types';
import { formatDistanceToNow } from 'date-fns';

export default function DashboardPage() {
  const router = useRouter();
  const { user, setUser, logout } = useAuthStore();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchUserAndDocuments();
  }, []);

  const fetchUserAndDocuments = async () => {
    try {
      // Fetch user data
      const userResponse = await api.get<User>('/auth/me');
      setUser(userResponse.data);

      // Fetch documents
      const docsResponse = await api.get('/documents');
      setDocuments(docsResponse.data.documents || []);
    } catch (err: any) {
      if (err.response?.status === 401) {
        logout();
        router.push('/login');
      } else {
        setError('Failed to load dashboard');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
    router.push('/');
  };

  const getSubscriptionBadge = (tier: string) => {
    const badges = {
      free: 'bg-gray-100 text-gray-800',
      starter: 'bg-blue-100 text-blue-800',
      pro: 'bg-purple-100 text-purple-800',
    };
    return badges[tier as keyof typeof badges] || badges.free;
  };

  const getRemainingDocuments = () => {
    if (!user) return 0;
    if (user.subscription_tier === 'pro') return '∞';
    if (user.subscription_tier === 'starter') return 5 - user.documents_analyzed;
    return 1 - user.documents_analyzed; // free
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white shadow-sm">
        <div className="container mx-auto px-6 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-8">
              <Link href="/dashboard" className="text-2xl font-bold text-blue-600">
                LegalLens
              </Link>
              <div className="hidden md:flex space-x-4">
                <Link
                  href="/dashboard"
                  className="text-gray-700 hover:text-blue-600 font-medium"
                >
                  Dashboard
                </Link>
                <Link
                  href="/upload"
                  className="text-gray-700 hover:text-blue-600 font-medium"
                >
                  Upload
                </Link>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600">{user?.email}</span>
              <button
                onClick={handleLogout}
                className="text-sm text-gray-700 hover:text-red-600 font-medium"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="container mx-auto px-6 py-8">
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        {/* User Info Card */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                Welcome back{user?.full_name ? `, ${user.full_name}` : ''}!
              </h1>
              <p className="text-gray-600 mt-1">{user?.email}</p>
            </div>
            <span
              className={`px-3 py-1 rounded-full text-sm font-medium ${getSubscriptionBadge(
                user?.subscription_tier || 'free'
              )}`}
            >
              {user?.subscription_tier?.toUpperCase()}
            </span>
          </div>

          <div className="grid md:grid-cols-3 gap-6 mt-6">
            <div className="border-l-4 border-blue-500 pl-4">
              <p className="text-sm text-gray-600">Documents Analyzed</p>
              <p className="text-3xl font-bold text-gray-900">{user?.documents_analyzed || 0}</p>
            </div>
            <div className="border-l-4 border-green-500 pl-4">
              <p className="text-sm text-gray-600">Remaining This Month</p>
              <p className="text-3xl font-bold text-gray-900">{getRemainingDocuments()}</p>
            </div>
            <div className="border-l-4 border-purple-500 pl-4">
              <p className="text-sm text-gray-600">Member Since</p>
              <p className="text-lg font-semibold text-gray-900">
                {user?.created_at
                  ? new Date(user.created_at).toLocaleDateString('en-US', {
                      month: 'short',
                      year: 'numeric',
                    })
                  : '-'}
              </p>
            </div>
          </div>

          {user?.subscription_tier === 'free' && user.documents_analyzed >= 1 && (
            <div className="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <p className="text-sm text-yellow-800">
                <strong>Upgrade to analyze more documents!</strong> Get 5 documents with Starter
                (₹99) or unlimited with Pro (₹499/month).
              </p>
            </div>
          )}
        </div>

        {/* Quick Actions */}
        <div className="grid md:grid-cols-2 gap-6 mb-8">
          <Link
            href="/upload"
            className="bg-blue-600 text-white p-6 rounded-lg shadow-md hover:bg-blue-700 transition-colors"
          >
            <div className="text-3xl mb-2">📄</div>
            <h3 className="text-xl font-semibold mb-1">Upload New Document</h3>
            <p className="text-blue-100">Analyze rental agreements, contracts, and more</p>
          </Link>

          <div className="bg-gradient-to-br from-purple-600 to-blue-600 text-white p-6 rounded-lg shadow-md">
            <div className="text-3xl mb-2">🎁</div>
            <h3 className="text-xl font-semibold mb-1">Upgrade Your Plan</h3>
            <p className="text-purple-100">Get more analyses and advanced features</p>
          </div>
        </div>

        {/* Documents List */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Your Documents</h2>

          {documents.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-6xl mb-4">📄</div>
              <p className="text-gray-600 mb-4">No documents yet</p>
              <Link
                href="/upload"
                className="inline-block bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700"
              >
                Upload Your First Document
              </Link>
            </div>
          ) : (
            <div className="space-y-4">
              {documents.map((doc) => (
                <div
                  key={doc.document_id}
                  className="border border-gray-200 rounded-lg p-4 hover:border-blue-300 transition-colors"
                >
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <h3 className="font-semibold text-gray-900">{doc.filename}</h3>
                      <p className="text-sm text-gray-600 mt-1">
                        Uploaded {formatDistanceToNow(new Date(doc.uploaded_at), { addSuffix: true })}
                      </p>
                    </div>
                    <div className="flex items-center space-x-2">
                      {doc.analyzed_at ? (
                        <span className="px-3 py-1 bg-green-100 text-green-800 text-sm rounded-full">
                          Analyzed
                        </span>
                      ) : (
                        <span className="px-3 py-1 bg-yellow-100 text-yellow-800 text-sm rounded-full">
                          Pending
                        </span>
                      )}
                      <Link
                        href={`/results/${doc.document_id}`}
                        className="text-blue-600 hover:text-blue-700 font-medium text-sm"
                      >
                        View →
                      </Link>
                    </div>
                  </div>
                  {doc.expires_at && (
                    <p className="text-xs text-gray-500 mt-2">
                      Expires {formatDistanceToNow(new Date(doc.expires_at), { addSuffix: true })}
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
