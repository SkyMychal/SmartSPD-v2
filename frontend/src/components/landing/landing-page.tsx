'use client';

import { Button } from '@/components/ui/button';
import { ArrowRight, Brain, MessageCircle, BarChart3, Shield, Zap, Users } from 'lucide-react';
import Link from 'next/link';

export function LandingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-sm border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-lg flex items-center justify-center">
                <Brain className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">SmartSPD</h1>
                <p className="text-xs text-gray-500">Powered by Onyx AI</p>
              </div>
            </div>
            <Link href="/login">
              <Button className="bg-blue-600 hover:bg-blue-700">
                Sign In
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="py-20 lg:py-32">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h1 className="text-4xl lg:text-6xl font-bold text-gray-900 mb-6">
              AI-Powered Health Plan
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-indigo-600">
                {' '}Assistant
              </span>
            </h1>
            <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
              Transform your TPA customer service operations with intelligent document processing, 
              instant benefit lookups, and expert-level responses powered by advanced AI.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link href="/login">
                <Button size="lg" className="bg-blue-600 hover:bg-blue-700">
                  Get Started
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
              </Link>
              <Button variant="outline" size="lg">
                Watch Demo
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl lg:text-4xl font-bold text-gray-900 mb-4">
              Everything you need for modern TPA operations
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              From document processing to customer service, SmartSPD streamlines every aspect 
              of health plan administration.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            <FeatureCard
              icon={<Brain className="w-8 h-8 text-blue-600" />}
              title="Intelligent Document Processing"
              description="Automatically extract and understand complex health plan documents, SPDs, and BPS files with AI-powered analysis."
            />
            <FeatureCard
              icon={<MessageCircle className="w-8 h-8 text-green-600" />}
              title="Real-Time Customer Support"
              description="Instant, accurate answers to member questions with copy-paste ready responses for your agents."
            />
            <FeatureCard
              icon={<BarChart3 className="w-8 h-8 text-purple-600" />}
              title="Advanced Analytics"
              description="Comprehensive dashboards and insights to optimize your customer service performance and member satisfaction."
            />
            <FeatureCard
              icon={<Shield className="w-8 h-8 text-red-600" />}
              title="Enterprise Security"
              description="HIPAA-compliant with role-based access control, audit logging, and complete data isolation per TPA."
            />
            <FeatureCard
              icon={<Zap className="w-8 h-8 text-yellow-600" />}
              title="Lightning Fast"
              description="Sub-second response times with confidence scoring and source attribution for every answer."
            />
            <FeatureCard
              icon={<Users className="w-8 h-8 text-indigo-600" />}
              title="Multi-Tenant Architecture"
              description="Complete TPA isolation with custom branding, user management, and scalable infrastructure."
            />
          </div>
        </div>
      </section>

      {/* Benefits Section */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="text-3xl lg:text-4xl font-bold text-gray-900 mb-6">
                Revolutionize your customer service
              </h2>
              <div className="space-y-6">
                <BenefitItem
                  title="90% Faster Response Times"
                  description="Transform complex benefit questions into instant, accurate answers"
                />
                <BenefitItem
                  title="99.9% Accuracy"
                  description="Knowledge graph and vector search ensure precise benefit matching"
                />
                <BenefitItem
                  title="50% Cost Reduction"
                  description="Reduce training time and improve agent productivity dramatically"
                />
                <BenefitItem
                  title="Enterprise Ready"
                  description="Scales from small TPAs to large enterprises with thousands of plans"
                />
              </div>
            </div>
            <div className="bg-white p-8 rounded-2xl shadow-xl">
              <div className="bg-gray-900 rounded-lg p-4 text-green-400 font-mono text-sm">
                <div className="mb-2">$ SmartSPD Query Engine</div>
                <div className="mb-4">━━━━━━━━━━━━━━━━━━━━━━━━━━━</div>
                <div className="mb-2">
                  <span className="text-blue-400">Member:</span> What's my deductible for specialists?
                </div>
                <div className="mb-2">
                  <span className="text-yellow-400">Processing...</span> 
                  <span className="animate-pulse">▊</span>
                </div>
                <div className="mb-2">
                  <span className="text-green-400">SmartSPD:</span> Your specialist deductible is $500 individual / $1,000 family. 
                  After meeting this deductible, you pay 20% coinsurance.
                </div>
                <div className="text-gray-500 text-xs mt-2">
                  ✓ Source: SPD Section 4.2 | Confidence: 98%
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-gradient-to-r from-blue-600 to-indigo-600">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl lg:text-4xl font-bold text-white mb-6">
            Ready to transform your TPA operations?
          </h2>
          <p className="text-xl text-blue-100 mb-8 max-w-2xl mx-auto">
            Join leading TPAs who are already using SmartSPD to deliver exceptional customer service.
          </p>
          <Link href="/login">
            <Button size="lg" variant="secondary" className="bg-white text-blue-600 hover:bg-gray-100">
              Start Your Free Trial
              <ArrowRight className="ml-2 h-5 w-5" />
            </Button>
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div className="col-span-1 md:col-span-2">
              <div className="flex items-center space-x-3 mb-4">
                <div className="w-8 h-8 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-lg flex items-center justify-center">
                  <Brain className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h3 className="text-lg font-bold">SmartSPD</h3>
                  <p className="text-sm text-gray-400">Powered by Onyx AI</p>
                </div>
              </div>
              <p className="text-gray-400 max-w-md">
                The leading AI-powered health plan assistant for TPA customer service operations.
              </p>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Product</h4>
              <ul className="space-y-2 text-gray-400">
                <li><a href="#" className="hover:text-white">Features</a></li>
                <li><a href="#" className="hover:text-white">Pricing</a></li>
                <li><a href="#" className="hover:text-white">Security</a></li>
                <li><a href="#" className="hover:text-white">API</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Support</h4>
              <ul className="space-y-2 text-gray-400">
                <li><a href="#" className="hover:text-white">Documentation</a></li>
                <li><a href="#" className="hover:text-white">Help Center</a></li>
                <li><a href="#" className="hover:text-white">Contact</a></li>
                <li><a href="#" className="hover:text-white">Status</a></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-800 mt-8 pt-8 text-center text-gray-400">
            <p>&copy; 2024 SmartSPD by Onyx AI. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}

function FeatureCard({ icon, title, description }: {
  icon: React.ReactNode;
  title: string;
  description: string;
}) {
  return (
    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
      <div className="mb-4">{icon}</div>
      <h3 className="text-xl font-semibold text-gray-900 mb-2">{title}</h3>
      <p className="text-gray-600">{description}</p>
    </div>
  );
}

function BenefitItem({ title, description }: {
  title: string;
  description: string;
}) {
  return (
    <div className="flex items-start space-x-3">
      <div className="w-6 h-6 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
        <div className="w-2 h-2 bg-green-600 rounded-full" />
      </div>
      <div>
        <h4 className="font-semibold text-gray-900 mb-1">{title}</h4>
        <p className="text-gray-600">{description}</p>
      </div>
    </div>
  );
}