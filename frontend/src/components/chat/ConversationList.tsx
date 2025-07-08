'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { 
  MessageCircle, 
  Clock, 
  User, 
  Search,
  Filter,
  Plus,
  AlertCircle,
  CheckCircle,
  ArrowUpDown
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

interface Conversation {
  id: string;
  member_id: string;
  title: string;
  status: 'active' | 'resolved' | 'escalated';
  priority: 'low' | 'normal' | 'high';
  message_count: number;
  last_message_at?: string;
  created_at: string;
  updated_at: string;
  agent_id?: string;
}

interface ConversationListProps {
  selectedConversationId?: string;
  onConversationSelect: (conversation: Conversation) => void;
  onNewConversation: () => void;
}

export default function ConversationList({
  selectedConversationId,
  onConversationSelect,
  onNewConversation
}: ConversationListProps) {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [sortBy, setSortBy] = useState<string>('updated_at');
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);

  useEffect(() => {
    loadConversations();
  }, [statusFilter, sortBy]);

  useEffect(() => {
    if (searchQuery) {
      const timeoutId = setTimeout(() => {
        searchConversations();
      }, 300);
      return () => clearTimeout(timeoutId);
    } else {
      loadConversations();
    }
  }, [searchQuery]);

  const loadConversations = async (pageNum = 1) => {
    try {
      setLoading(pageNum === 1);
      
      const params = new URLSearchParams({
        skip: ((pageNum - 1) * 20).toString(),
        limit: '20',
        ...(statusFilter !== 'all' && { status: statusFilter })
      });

      const response = await fetch(`/api/chat/conversations?${params}`);
      if (!response.ok) throw new Error('Failed to load conversations');

      const data = await response.json();
      
      if (pageNum === 1) {
        setConversations(data.conversations);
      } else {
        setConversations(prev => [...prev, ...data.conversations]);
      }
      
      setHasMore(data.conversations.length === 20);
      setPage(pageNum);
    } catch (error) {
      console.error('Error loading conversations:', error);
    } finally {
      setLoading(false);
    }
  };

  const searchConversations = async () => {
    // TODO: Implement search API endpoint
    // For now, filter locally
    loadConversations();
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <MessageCircle className="w-4 h-4 text-blue-500" />;
      case 'resolved':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'escalated':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      default:
        return <MessageCircle className="w-4 h-4 text-gray-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-blue-100 text-blue-800';
      case 'resolved':
        return 'bg-green-100 text-green-800';
      case 'escalated':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return 'bg-red-100 text-red-800';
      case 'normal':
        return 'bg-blue-100 text-blue-800';
      case 'low':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const filteredConversations = conversations.filter(conv =>
    conv.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    conv.member_id.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Conversations</CardTitle>
          <Button
            onClick={onNewConversation}
            size="sm"
            className="h-8"
          >
            <Plus className="w-4 h-4 mr-1" />
            New
          </Button>
        </div>

        {/* Search and Filters */}
        <div className="space-y-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <Input
              placeholder="Search conversations..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>

          <div className="flex space-x-2">
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="resolved">Resolved</SelectItem>
                <SelectItem value="escalated">Escalated</SelectItem>
              </SelectContent>
            </Select>

            <Select value={sortBy} onValueChange={setSortBy}>
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Sort by" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="updated_at">Last Updated</SelectItem>
                <SelectItem value="created_at">Created Date</SelectItem>
                <SelectItem value="message_count">Message Count</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </CardHeader>

      <Separator />

      <ScrollArea className="flex-1">
        <div className="p-4 space-y-2">
          {loading && conversations.length === 0 ? (
            <div className="space-y-2">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="animate-pulse">
                  <div className="h-20 bg-gray-200 rounded-lg"></div>
                </div>
              ))}
            </div>
          ) : filteredConversations.length === 0 ? (
            <div className="text-center py-8">
              <MessageCircle className="mx-auto h-12 w-12 text-gray-400 mb-4" />
              <p className="text-gray-500 font-medium">No conversations found</p>
              <p className="text-gray-400 text-sm">
                {searchQuery ? 'Try adjusting your search' : 'Start a new conversation to get started'}
              </p>
            </div>
          ) : (
            filteredConversations.map((conversation) => (
              <div
                key={conversation.id}
                onClick={() => onConversationSelect(conversation)}
                className={`p-3 rounded-lg border cursor-pointer transition-colors hover:bg-gray-50 ${
                  selectedConversationId === conversation.id
                    ? 'bg-blue-50 border-blue-200'
                    : 'border-gray-200'
                }`}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    {getStatusIcon(conversation.status)}
                    <h3 className="font-medium text-sm truncate flex-1">
                      {conversation.title}
                    </h3>
                  </div>
                  <div className="flex items-center space-x-1">
                    <Badge 
                      className={`text-xs ${getStatusColor(conversation.status)}`}
                      variant="secondary"
                    >
                      {conversation.status}
                    </Badge>
                    {conversation.priority === 'high' && (
                      <Badge 
                        className={`text-xs ${getPriorityColor(conversation.priority)}`}
                        variant="secondary"
                      >
                        {conversation.priority}
                      </Badge>
                    )}
                  </div>
                </div>

                <div className="flex items-center justify-between text-xs text-gray-500">
                  <div className="flex items-center space-x-3">
                    <div className="flex items-center space-x-1">
                      <User className="w-3 h-3" />
                      <span>{conversation.member_id}</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <MessageCircle className="w-3 h-3" />
                      <span>{conversation.message_count}</span>
                    </div>
                  </div>
                  <div className="flex items-center space-x-1">
                    <Clock className="w-3 h-3" />
                    <span>
                      {formatDistanceToNow(
                        new Date(conversation.last_message_at || conversation.updated_at),
                        { addSuffix: true }
                      )}
                    </span>
                  </div>
                </div>
              </div>
            ))
          )}

          {/* Load More Button */}
          {hasMore && !loading && filteredConversations.length > 0 && (
            <div className="pt-4">
              <Button
                onClick={() => loadConversations(page + 1)}
                variant="outline"
                className="w-full"
                size="sm"
              >
                Load More
              </Button>
            </div>
          )}
        </div>
      </ScrollArea>
    </Card>
  );
}