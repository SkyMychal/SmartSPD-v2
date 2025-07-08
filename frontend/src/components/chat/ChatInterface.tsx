'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { 
  Send, 
  Bot, 
  User, 
  Clock, 
  CheckCircle, 
  AlertCircle,
  Lightbulb,
  Copy,
  ThumbsUp,
  ThumbsDown
} from 'lucide-react';
import { toast } from 'sonner';

interface Message {
  id: string;
  content: string;
  message_type: 'user' | 'assistant' | 'system';
  sender_id?: string;
  created_at: string;
  metadata?: {
    confidence_score?: number;
    query_intent?: string;
    source_documents?: Array<{
      type: string;
      document_id: string;
      page_number?: number;
      section_title?: string;
    }>;
    processing_time?: number;
  };
}

interface Conversation {
  id: string;
  member_id: string;
  title: string;
  status: string;
  messages: Message[];
  created_at: string;
  updated_at: string;
}

interface ChatQueryResponse {
  answer: string;
  confidence_score: number;
  query_intent: string;
  source_documents: Array<any>;
  related_topics: string[];
  follow_up_suggestions: string[];
  processing_time: number;
  conversation_id?: string;
}

interface ChatInterfaceProps {
  conversation?: Conversation;
  memberId?: string;
  healthPlanId?: string;
  onConversationUpdate?: (conversation: Conversation) => void;
}

export default function ChatInterface({ 
  conversation, 
  memberId, 
  healthPlanId,
  onConversationUpdate 
}: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>(conversation?.messages || []);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [currentConversationId, setCurrentConversationId] = useState(conversation?.id);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Load query suggestions on mount
  useEffect(() => {
    loadSuggestions();
  }, [healthPlanId]);

  const loadSuggestions = async () => {
    try {
      const response = await fetch(`/api/chat/suggestions?health_plan_id=${healthPlanId}&limit=5`);
      if (response.ok) {
        const data = await response.json();
        setSuggestions(data.suggestions);
      }
    } catch (error) {
      console.error('Failed to load suggestions:', error);
    }
  };

  const sendMessage = async (messageText?: string) => {
    const text = messageText || inputMessage.trim();
    if (!text || isLoading) return;

    setIsLoading(true);
    setInputMessage('');

    // Add user message to UI immediately
    const userMessage: Message = {
      id: `temp-${Date.now()}`,
      content: text,
      message_type: 'user',
      created_at: new Date().toISOString()
    };
    setMessages(prev => [...prev, userMessage]);

    try {
      const response = await fetch('/api/chat/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: text,
          conversation_id: currentConversationId,
          member_id: memberId,
          health_plan_id: healthPlanId
        })
      });

      if (!response.ok) {
        throw new Error('Failed to send message');
      }

      const data: ChatQueryResponse = await response.json();

      // Update conversation ID if this is a new conversation
      if (data.conversation_id && !currentConversationId) {
        setCurrentConversationId(data.conversation_id);
      }

      // Add AI response to messages
      const aiMessage: Message = {
        id: `ai-${Date.now()}`,
        content: data.answer,
        message_type: 'assistant',
        created_at: new Date().toISOString(),
        metadata: {
          confidence_score: data.confidence_score,
          query_intent: data.query_intent,
          source_documents: data.source_documents,
          processing_time: data.processing_time
        }
      };

      setMessages(prev => [...prev, aiMessage]);

      // Update suggestions with follow-up questions
      if (data.follow_up_suggestions && data.follow_up_suggestions.length > 0) {
        setSuggestions(data.follow_up_suggestions);
      }

    } catch (error) {
      console.error('Error sending message:', error);
      toast.error('Failed to send message. Please try again.');
      
      // Remove the temporary user message on error
      setMessages(prev => prev.slice(0, -1));
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard');
  };

  const getConfidenceColor = (score: number) => {
    if (score >= 0.8) return 'bg-green-100 text-green-800';
    if (score >= 0.6) return 'bg-yellow-100 text-yellow-800';
    return 'bg-red-100 text-red-800';
  };

  const formatProcessingTime = (time: number) => {
    return time < 1 ? `${Math.round(time * 1000)}ms` : `${time.toFixed(1)}s`;
  };

  return (
    <div className="flex flex-col h-full max-h-[800px]">
      {/* Chat Header */}
      <Card className="mb-4">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg">
              {conversation?.title || 'New Conversation'}
            </CardTitle>
            <div className="flex items-center space-x-2">
              {conversation?.status && (
                <Badge variant={conversation.status === 'active' ? 'default' : 'secondary'}>
                  {conversation.status}
                </Badge>
              )}
              {memberId && (
                <Badge variant="outline">
                  Member: {memberId}
                </Badge>
              )}
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Messages Area */}
      <Card className="flex-1 flex flex-col">
        <ScrollArea className="flex-1 p-4">
          <div className="space-y-4">
            {messages.length === 0 && (
              <div className="text-center text-gray-500 py-8">
                <Bot className="mx-auto h-12 w-12 mb-4 text-gray-400" />
                <p className="text-lg font-medium mb-2">Ready to help!</p>
                <p>Ask me anything about the member's health plan benefits.</p>
              </div>
            )}

            {messages.map((message, index) => (
              <div
                key={message.id}
                className={`flex items-start space-x-3 ${
                  message.message_type === 'user' ? 'justify-end' : 'justify-start'
                }`}
              >
                {message.message_type !== 'user' && (
                  <Avatar className="w-8 h-8">
                    <AvatarFallback>
                      {message.message_type === 'assistant' ? (
                        <Bot className="w-4 h-4" />
                      ) : (
                        <AlertCircle className="w-4 h-4" />
                      )}
                    </AvatarFallback>
                  </Avatar>
                )}

                <div
                  className={`max-w-[80%] rounded-lg px-4 py-2 ${
                    message.message_type === 'user'
                      ? 'bg-blue-600 text-white'
                      : message.message_type === 'assistant'
                      ? 'bg-gray-100 border'
                      : 'bg-yellow-50 border border-yellow-200'
                  }`}
                >
                  <div className="whitespace-pre-wrap">{message.content}</div>
                  
                  {/* AI Message Metadata */}
                  {message.message_type === 'assistant' && message.metadata && (
                    <div className="mt-3 pt-3 border-t border-gray-200 space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <div className="flex items-center space-x-2">
                          <Badge 
                            className={getConfidenceColor(message.metadata.confidence_score || 0)}
                            variant="secondary"
                          >
                            {Math.round((message.metadata.confidence_score || 0) * 100)}% confident
                          </Badge>
                          {message.metadata.query_intent && (
                            <Badge variant="outline">
                              {message.metadata.query_intent}
                            </Badge>
                          )}
                        </div>
                        <div className="flex items-center space-x-1 text-gray-500">
                          <Clock className="w-3 h-3" />
                          <span>{formatProcessingTime(message.metadata.processing_time || 0)}</span>
                        </div>
                      </div>

                      {/* Source Documents */}
                      {message.metadata.source_documents && message.metadata.source_documents.length > 0 && (
                        <div className="text-xs text-gray-600">
                          <div className="font-medium mb-1">Sources:</div>
                          <div className="space-y-1">
                            {message.metadata.source_documents.slice(0, 3).map((source, idx) => (
                              <div key={idx} className="flex items-center space-x-1">
                                <CheckCircle className="w-3 h-3 text-green-500" />
                                <span>
                                  {source.section_title || 'Plan Document'}
                                  {source.page_number && ` (Page ${source.page_number})`}
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Action Buttons */}
                      <div className="flex items-center space-x-2">
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => copyToClipboard(message.content)}
                          className="h-6 px-2 text-xs"
                        >
                          <Copy className="w-3 h-3 mr-1" />
                          Copy
                        </Button>
                        <Button size="sm" variant="ghost" className="h-6 px-2 text-xs">
                          <ThumbsUp className="w-3 h-3" />
                        </Button>
                        <Button size="sm" variant="ghost" className="h-6 px-2 text-xs">
                          <ThumbsDown className="w-3 h-3" />
                        </Button>
                      </div>
                    </div>
                  )}

                  <div className="text-xs text-gray-500 mt-2">
                    {new Date(message.created_at).toLocaleTimeString()}
                  </div>
                </div>

                {message.message_type === 'user' && (
                  <Avatar className="w-8 h-8">
                    <AvatarFallback>
                      <User className="w-4 h-4" />
                    </AvatarFallback>
                  </Avatar>
                )}
              </div>
            ))}

            {isLoading && (
              <div className="flex items-start space-x-3">
                <Avatar className="w-8 h-8">
                  <AvatarFallback>
                    <Bot className="w-4 h-4" />
                  </AvatarFallback>
                </Avatar>
                <div className="bg-gray-100 border rounded-lg px-4 py-2 max-w-[80%]">
                  <div className="flex items-center space-x-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                    <span className="text-gray-600">AI is thinking...</span>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </ScrollArea>

        <Separator />

        {/* Suggestions */}
        {suggestions.length > 0 && (
          <div className="p-4 border-t bg-gray-50">
            <div className="flex items-center space-x-2 mb-3">
              <Lightbulb className="w-4 h-4 text-yellow-600" />
              <span className="text-sm font-medium text-gray-700">Suggested questions:</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {suggestions.slice(0, 3).map((suggestion, index) => (
                <Button
                  key={index}
                  variant="outline"
                  size="sm"
                  onClick={() => sendMessage(suggestion)}
                  disabled={isLoading}
                  className="text-xs h-7"
                >
                  {suggestion}
                </Button>
              ))}
            </div>
          </div>
        )}

        {/* Input Area */}
        <div className="p-4 border-t">
          <div className="flex space-x-2">
            <Input
              ref={inputRef}
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask about health plan benefits..."
              disabled={isLoading}
              className="flex-1"
            />
            <Button
              onClick={() => sendMessage()}
              disabled={isLoading || !inputMessage.trim()}
              size="sm"
            >
              <Send className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}