'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';
import api from '@/lib/api';
import { useAuthStore } from '@/store/authStore';
import { Analysis } from '@/types';
import { formatDistanceToNow } from 'date-fns';

export default function ResultsPage() {
  const router = useRouter();
  const params = useParams();
  const documentId = params.id as string;
  const { logout } = useAuthStore();

  const [document, setDocument] = useState<any>(null);
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [askQuestion, setAskQuestion] = useState('');
  const [questionLoading, setQuestionLoading] = useState(false);
  const [answer, setAnswer] = useState('');

  useEffect(() => {
    fetchDocument();
  }, [documentId]);

  const fetchDocument = async () => {
    try {
      const response = await api.get(`/document/${documentId}`);
      setDocument(response.data);
      setAnalysis(response.data.analysis);
    } catch (err: any) {
      if (err.response?.status === 401) {
        logout();
        router.push('/login');
      } else if (err.response?.status === 404) {
        setError('Document not found');
      } else {
        setError('Failed to load analysis');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleAskQuestion = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!askQuestion.trim()) return;

    setQuestionLoading(true);
    setAnswer('');

    try {
      const response = await api.post('/ask-question', {
        document_id: documentId,
        question: askQuestion,
        language: analysis?.language || 'en',
      });
      setAnswer(response.data.answer);
    } catch (err: any) {
      setAnswer('Failed to get answer. Please try again.');
    } finally {
      setQuestionLoading(false);
    }
  };

  const getRiskColor = (score: number) => {
    if (score <= 3) return 'text-green-600 bg-green-100';
    if (score <= 6) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const getRiskLevelColor = (level: string) => {
    switch (level) {
      case 'low':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'high':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getAssessmentColor = (assessment: string) => {
    switch (assessment) {
      case 'favorable':
        return 'bg-green-100 text-green-800';
      case 'neutral':
        return 'bg-gray-100 text-gray-800';
      case 'needs_attention':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading analysis...</p>
        </div>
      </div>
    );
  }

  if (error || !document) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="text-6xl mb-4">❌</div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">{error || 'Not Found'}</h2>
          <Link href="/dashboard" className="text-blue-600 hover:text-blue-700">
            Return to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  if (!analysis) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="text-6xl mb-4">⏳</div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Analysis Pending</h2>
          <p className="text-gray-600 mb-4">This document hasn't been analyzed yet.</p>
          <Link href="/dashboard" className="text-blue-600 hover:text-blue-700">
            Return to Dashboard
          </Link>
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
            <Link href="/dashboard" className="text-2xl font-bold text-blue-600">
              LegalLens
            </Link>
            <Link
              href="/dashboard"
              className="text-sm text-gray-700 hover:text-blue-600 font-medium"
            >
              ← Back to Dashboard
            </Link>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="container mx-auto px-6 py-8 max-w-6xl">
        {/* Document Header */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{document.filename}</h1>
              <p className="text-gray-600 mt-1">
                Analyzed {formatDistanceToNow(new Date(document.analyzed_at), { addSuffix: true })}
              </p>
            </div>
            <div className="text-right">
              <div className="text-sm text-gray-600 mb-1">Document Type</div>
              <div className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
                {analysis.document_type.replace('_', ' ').toUpperCase()}
              </div>
            </div>
          </div>
        </div>

        {/* Risk Score */}
        <div className="bg-white rounded-lg shadow-md p-8 mb-6">
          <div className="text-center">
            <h2 className="text-lg font-semibold text-gray-700 mb-4">Contract Risk Score</h2>
            <div
              className={`inline-flex items-center justify-center w-32 h-32 rounded-full text-5xl font-bold ${getRiskColor(
                analysis.contract_risk_score
              )}`}
            >
              {analysis.contract_risk_score}
              <span className="text-2xl">/10</span>
            </div>
            <p className="text-gray-600 mt-4">
              {analysis.contract_risk_score <= 3
                ? 'Low Risk - Generally safe'
                : analysis.contract_risk_score <= 6
                ? 'Medium Risk - Review carefully'
                : 'High Risk - Seek legal advice'}
            </p>
          </div>
        </div>

        {/* Summary */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">📋 Summary</h2>
          <p className="text-gray-700 leading-relaxed">{analysis.summary}</p>
        </div>

        {/* Risk Alerts */}
        {analysis.risk_alerts && analysis.risk_alerts.length > 0 && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 mb-6">
            <h2 className="text-xl font-bold text-red-900 mb-4">⚠️ Risk Alerts</h2>
            <ul className="space-y-2">
              {analysis.risk_alerts.map((alert, index) => (
                <li key={index} className="flex items-start">
                  <span className="text-red-600 mr-2">•</span>
                  <span className="text-red-800">{alert}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Key Clauses */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">📄 Key Clauses</h2>
          <div className="space-y-4">
            {analysis.key_clauses.map((clause, index) => (
              <div
                key={index}
                className={`border-l-4 p-4 rounded ${getRiskLevelColor(clause.risk_level)}`}
              >
                <div className="flex justify-between items-start mb-2">
                  <h3 className="font-semibold">{clause.title}</h3>
                  <span className="text-xs px-2 py-1 rounded-full bg-white">
                    {clause.risk_level.toUpperCase()}
                  </span>
                </div>
                <p className="text-sm">{clause.details}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Financial Obligations */}
        {analysis.financial_obligations && analysis.financial_obligations.length > 0 && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">💰 Financial Obligations</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {analysis.financial_obligations.map((obligation, index) => (
                <div key={index} className="bg-green-50 border border-green-200 p-3 rounded">
                  <span className="font-mono text-green-800">{obligation}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Negotiation Points */}
        {analysis.negotiation_points && analysis.negotiation_points.length > 0 && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">💡 Negotiation Suggestions</h2>
            <ul className="space-y-3">
              {analysis.negotiation_points.map((point, index) => (
                <li key={index} className="flex items-start">
                  <span className="text-blue-600 mr-2">✓</span>
                  <span className="text-gray-700">{point}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Clause Comparisons */}
        {analysis.clause_comparisons && analysis.clause_comparisons.length > 0 && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">📊 Market Comparison</h2>
            <div className="space-y-4">
              {analysis.clause_comparisons.map((comparison, index) => (
                <div key={index} className="border border-gray-200 p-4 rounded">
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="font-semibold text-gray-900">{comparison.clause_title}</h3>
                    <span
                      className={`text-xs px-2 py-1 rounded-full ${getAssessmentColor(
                        comparison.assessment
                      )}`}
                    >
                      {comparison.assessment.replace('_', ' ').toUpperCase()}
                    </span>
                  </div>
                  <div className="grid md:grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="text-gray-600 font-medium">Market Standard:</p>
                      <p className="text-gray-700">{comparison.market_standard}</p>
                    </div>
                    <div>
                      <p className="text-gray-600 font-medium">Your Document:</p>
                      <p className="text-gray-700">{comparison.document_value}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Legal Terms Dictionary */}
        {analysis.legal_terms_dictionary && analysis.legal_terms_dictionary.length > 0 && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">📖 Legal Terms Explained</h2>
            <div className="grid md:grid-cols-2 gap-4">
              {analysis.legal_terms_dictionary.map((term, index) => (
                <div key={index} className="border border-gray-200 p-4 rounded">
                  <h3 className="font-semibold text-blue-600 mb-1">{term.term}</h3>
                  <p className="text-sm text-gray-700">{term.plain_explanation}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Ask Questions */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">❓ Ask a Question</h2>
          <form onSubmit={handleAskQuestion} className="space-y-4">
            <div>
              <textarea
                value={askQuestion}
                onChange={(e) => setAskQuestion(e.target.value)}
                placeholder="Ask anything about this document..."
                rows={3}
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <button
              type="submit"
              disabled={questionLoading || !askQuestion.trim()}
              className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {questionLoading ? 'Getting Answer...' : 'Ask Question'}
            </button>
          </form>

          {answer && (
            <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <p className="text-sm font-semibold text-blue-900 mb-1">Answer:</p>
              <p className="text-blue-800">{answer}</p>
            </div>
          )}
        </div>

        {/* Disclaimer */}
        <div className="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg text-sm text-yellow-800">
          <strong>⚠️ Important:</strong> This AI analysis is for informational purposes only and not
          legal advice. Consult a qualified lawyer for legal matters.
        </div>
      </main>
    </div>
  );
}
