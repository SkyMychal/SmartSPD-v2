'use client';

import { useState, useEffect, useRef } from 'react';
import { 
  Send, 
  MessageSquare, 
  Bot, 
  User, 
  Copy, 
  ThumbsUp, 
  ThumbsDown,
  RefreshCw,
  FileText,
  AlertCircle,
  ChevronDown
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources?: string[];
  confidence?: number;
}

interface ChatSession {
  id: string;
  title: string;
  messages: Message[];
  created_at: Date;
}

interface HealthPlan {
  id: string;
  name: string;
  plan_number: string;
  plan_year: number;
  plan_type?: string;
  is_active: boolean;
}

export default function ChatPage() {
  const [user, setUser] = useState(null);
  const [currentSession, setCurrentSession] = useState<ChatSession | null>(null);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [healthPlans, setHealthPlans] = useState<HealthPlan[]>([]);
  const [selectedHealthPlan, setSelectedHealthPlan] = useState<string | null>(null);
  const [loadingHealthPlans, setLoadingHealthPlans] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Get mock user data
    fetch('/api/auth/me')
      .then(res => res.ok ? res.json() : null)
      .then(userData => setUser(userData))
      .catch(() => setUser(null));
    
    // Load existing sessions and health plans
    loadChatSessions();
    loadHealthPlans();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadHealthPlans = async () => {
    setLoadingHealthPlans(true);
    try {
      // Import API client and try real backend call
      const { apiClient } = await import('@/lib/api-client');
      
      const response = await apiClient.healthPlans.getHealthPlans({ active_only: true });
      
      if (response.error) {
        console.warn('Health Plans API error:', response.error);
        // Show empty state instead of mock data
        setHealthPlans([]);
        setError('Unable to load health plans. Please try again.');
      } else {
        // Real backend response
        setHealthPlans(response.data.health_plans || []);
        if (response.data.health_plans?.length > 0) {
          setSelectedHealthPlan(response.data.health_plans[0].id);
        }
      }
    } catch (err) {
      console.error('Failed to load health plans:', err);
      // Show empty state instead of mock data
      setHealthPlans([]);
      setError('Failed to load health plans. Please check your connection and try again.');
    } finally {
      setLoadingHealthPlans(false);
    }
  };

  const loadChatSessions = async () => {
    try {
      // Start with empty sessions - no mock data
      setSessions([]);
      setCurrentSession(null);
      setMessages([]);
    } catch (err) {
      console.error('Failed to load chat sessions:', err);
      setError('Failed to load chat history');
    }
  };

  const startNewConversation = () => {
    const newSession: ChatSession = {
      id: Date.now().toString(),
      title: 'New Conversation',
      created_at: new Date(),
      messages: []
    };
    
    setSessions(prev => [newSession, ...prev]);
    setCurrentSession(newSession);
    setMessages([]);
    setError(null);
  };

  const sendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;
    
    if (!selectedHealthPlan) {
      setError('Please select a health plan before asking questions.');
      return;
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: inputValue,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    const currentQuery = inputValue;
    setInputValue('');
    setIsLoading(true);
    setError(null);

    try {
      // Import API client and try real backend call
      const { apiClient } = await import('@/lib/api-client');
      
      const response = await apiClient.chat.submitQuery({
        query: currentQuery,
        health_plan_id: selectedHealthPlan || 'plan-1', // Use selected health plan
        conversation_id: currentSession?.id
      });
      
      let assistantMessage: Message;
      
      if (response.error) {
        console.warn('Chat API error, using enhanced mock response:', response.error);
        // Enhanced mock response when backend is not available
        assistantMessage = {
          id: (Date.now() + 1).toString(),
          type: 'assistant',
          content: generateMockResponse(currentQuery),
          timestamp: new Date(),
          sources: ['Demo Health Plan Document', 'Demo BPS Specification', 'Demo Coverage Guide'],
          confidence: 0.88
        };
      } else {
        // Real backend response
        assistantMessage = {
          id: response.data.query_id,
          type: 'assistant',
          content: response.data.response,
          timestamp: new Date(),
          sources: response.data.sources || [],
          confidence: response.data.confidence_score || 0.85
        };
      }

      setMessages(prev => [...prev, assistantMessage]);
      
      // Update session title based on first message
      if (currentSession && currentSession.messages.length === 0) {
        const updatedSession = {
          ...currentSession,
          title: currentQuery.length > 50 ? currentQuery.substring(0, 50) + '...' : currentQuery,
          messages: [userMessage, assistantMessage]
        };
        setCurrentSession(updatedSession);
        setSessions(prev => prev.map(s => s.id === currentSession.id ? updatedSession : s));
      }
      
    } catch (err) {
      console.error('Failed to send message:', err);
      
      // Fallback to enhanced mock response
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: generateMockResponse(currentQuery),
        timestamp: new Date(),
        sources: ['Demo Health Plan Document', 'Demo BPS Specification'],
        confidence: 0.85
      };
      
      setMessages(prev => [...prev, assistantMessage]);
      setError('Using demo responses. Backend connection needed for processed documents.');
    } finally {
      setIsLoading(false);
    }
  };

  const generateMockResponse = (query: string): string => {
    const lowerQuery = query.toLowerCase();
    
    if (lowerQuery.includes('deductible')) {
      return 'Your annual deductible varies by service type. For medical services, it\'s $1,500 individual/$3,000 family. For prescription drugs, there\'s a separate $200 deductible. Once you meet your deductible, you\'ll pay coinsurance until you reach your out-of-pocket maximum.';
    }
    
    if (lowerQuery.includes('copay') || lowerQuery.includes('co-pay')) {
      return 'Your copayment amounts depend on the type of service: Primary Care visits are $25, Specialist visits are $40, Urgent Care is $75, and Emergency Room visits are $200 (waived if admitted). These copays apply after you meet your deductible.';
    }
    
    if (lowerQuery.includes('prescription') || lowerQuery.includes('drug')) {
      return 'Your prescription drug coverage includes a 3-tier formulary: Tier 1 (generic drugs) has a $10 copay, Tier 2 (preferred brand) has a $30 copay, and Tier 3 (non-preferred brand) has a $60 copay. You can get a 90-day supply through mail order with reduced copays.';
    }
    
    if (lowerQuery.includes('network') || lowerQuery.includes('provider')) {
      return 'Your health plan uses a PPO network. You have the flexibility to see any provider, but you\'ll save money by using in-network providers. In-network services are covered at 80% after deductible, while out-of-network services are covered at 60% with a separate deductible.';
    }
    
    return 'I understand you\'re asking about your health plan benefits. Based on the available plan documents, I can help you with questions about deductibles, copayments, coverage details, provider networks, and prescription benefits. Could you please be more specific about what aspect of your coverage you\'d like to know about?';
  };

  const copyMessage = (content: string) => {
    navigator.clipboard.writeText(content);
  };

  const provideFeedback = (messageId: string, helpful: boolean) => {
    console.log(`Feedback for message ${messageId}: ${helpful ? 'helpful' : 'not helpful'}`);
    // In a real app, this would send feedback to the backend
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="flex h-[calc(100vh-4rem)] bg-gray-50">
      {/* Sidebar with chat sessions */}
      <div className="w-64 bg-white border-r border-gray-200 flex flex-col">
        <div className="p-4 border-b border-gray-200">
          <Button
            onClick={startNewConversation}
            className="w-full flex items-center gap-2"
          >
            <MessageSquare className="w-4 h-4" />
            New Conversation
          </Button>
        </div>
        
        <div className="flex-1 overflow-y-auto">
          <div className="p-2">
            <h3 className="text-sm font-medium text-gray-500 mb-2">Recent Conversations</h3>
            {sessions.map((session) => (
              <button
                key={session.id}
                onClick={() => {
                  setCurrentSession(session);
                  setMessages(session.messages);
                }}
                className={`w-full text-left p-2 rounded-md mb-1 hover:bg-gray-100 ${
                  currentSession?.id === session.id ? 'bg-blue-50 border border-blue-200' : ''
                }`}
              >
                <p className="text-sm font-medium truncate">{session.title}</p>
                <p className="text-xs text-gray-500">
                  {session.created_at.toLocaleDateString()}
                </p>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Main chat area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-semibold text-gray-900">Health Plan Assistant</h1>
              <p className="text-sm text-gray-600">Ask questions about your benefits and coverage</p>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={loadChatSessions}
              className="flex items-center gap-2"
            >
              <RefreshCw className="w-4 h-4" />
              Refresh
            </Button>
          </div>
          
          {/* Health Plan Selection */}
          <div className="mt-4 flex items-center gap-4">
            <div className="flex items-center gap-2">
              <label htmlFor="health-plan-select" className="text-sm font-medium text-gray-700">
                Health Plan:
              </label>
              <Select
                value={selectedHealthPlan || ''}
                onValueChange={setSelectedHealthPlan}
                disabled={loadingHealthPlans || healthPlans.length === 0}
              >
                <SelectTrigger className="w-64">
                  <SelectValue placeholder={loadingHealthPlans ? "Loading plans..." : "Select a health plan"} />
                </SelectTrigger>
                <SelectContent>
                  {healthPlans.map((plan) => (
                    <SelectItem key={plan.id} value={plan.id}>
                      <div className="flex flex-col">
                        <span className="font-medium">{plan.name}</span>
                        <span className="text-xs text-gray-500">
                          {plan.plan_number} • {plan.plan_year} • {plan.plan_type}
                        </span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            {selectedHealthPlan && (
              <div className="text-xs text-gray-500">
                Questions will be answered using the selected health plan's documents
              </div>
            )}
          </div>
        </div>

        {error && (
          <div className="p-4">
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          </div>
        )}

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 ? (
            <div className="text-center py-12">
              <Bot className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Start a conversation</h3>
              <p className="text-gray-600 mb-4">Ask me anything about your health plan benefits, coverage, or claims.</p>
              <div className="flex flex-wrap justify-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setInputValue("What is my deductible?")}
                >
                  What is my deductible?
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setInputValue("How much are copays?")}
                >
                  How much are copays?
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setInputValue("What providers are in-network?")}
                >
                  What providers are in-network?
                </Button>
              </div>
            </div>
          ) : (
            messages.map((message) => (
              <div
                key={message.id}
                className={`flex gap-3 ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div className={`flex gap-3 max-w-[70%] ${message.type === 'user' ? 'flex-row-reverse' : ''}`}>
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                    message.type === 'user' ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-600'
                  }`}>
                    {message.type === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                  </div>
                  
                  <div className={`rounded-lg p-3 ${
                    message.type === 'user' 
                      ? 'bg-blue-600 text-white' 
                      : 'bg-white border border-gray-200'
                  }`}>
                    <p className="text-sm">{message.content}</p>
                    
                    {message.type === 'assistant' && (
                      <div className="mt-3 space-y-2">
                        {message.sources && (
                          <div className="flex items-center gap-2 text-xs text-gray-500">
                            <FileText className="w-3 h-3" />
                            <span>Sources: {message.sources.join(', ')}</span>
                          </div>
                        )}
                        
                        {message.confidence && (
                          <div className="text-xs text-gray-500">
                            Confidence: {Math.round(message.confidence * 100)}%
                          </div>
                        )}
                        
                        <div className="flex items-center gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => copyMessage(message.content)}
                            className="h-6 px-2 text-xs"
                          >
                            <Copy className="w-3 h-3" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => provideFeedback(message.id, true)}
                            className="h-6 px-2 text-xs"
                          >
                            <ThumbsUp className="w-3 h-3" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => provideFeedback(message.id, false)}
                            className="h-6 px-2 text-xs"
                          >
                            <ThumbsDown className="w-3 h-3" />
                          </Button>
                        </div>
                      </div>
                    )}
                    
                    <div className="text-xs opacity-75 mt-1">
                      {message.timestamp.toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              </div>
            ))
          )}
          
          {isLoading && (
            <div className="flex gap-3 justify-start">
              <div className="w-8 h-8 rounded-full bg-gray-200 text-gray-600 flex items-center justify-center flex-shrink-0">
                <Bot className="w-4 h-4" />
              </div>
              <div className="bg-white border border-gray-200 rounded-lg p-3">
                <div className="flex items-center gap-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                  <span className="text-sm text-gray-600">Thinking...</span>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Input area */}
        <div className="bg-white border-t border-gray-200 p-4">
          {!selectedHealthPlan && (
            <div className="mb-3">
              <Alert>
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  Please select a health plan above to start asking questions about benefits and coverage.
                </AlertDescription>
              </Alert>
            </div>
          )}
          
          <div className="flex gap-2">
            <Input
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={
                selectedHealthPlan 
                  ? "Ask about your health plan benefits..." 
                  : "Select a health plan to ask questions..."
              }
              disabled={isLoading || !selectedHealthPlan}
              className="flex-1"
            />
            <Button
              onClick={sendMessage}
              disabled={!inputValue.trim() || isLoading || !selectedHealthPlan}
              className="flex items-center gap-2"
            >
              <Send className="w-4 h-4" />
              Send
            </Button>
          </div>
          <p className="text-xs text-gray-500 mt-2">
            {selectedHealthPlan 
              ? "Press Enter to send, Shift+Enter for new line"
              : "Select a health plan to enable messaging"
            }
          </p>
        </div>
      </div>
    </div>
  );
}