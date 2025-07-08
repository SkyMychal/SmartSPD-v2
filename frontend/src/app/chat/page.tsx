'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { 
  MessageCircle, 
  User, 
  Plus,
  Settings,
  Activity,
  Clock,
  CheckCircle,
  AlertTriangle
} from 'lucide-react';
import { toast } from 'sonner';

import ChatInterface from '@/components/chat/ChatInterface';
import ConversationList from '@/components/chat/ConversationList';

interface Conversation {
  id: string;
  member_id: string;
  title: string;
  status: string;
  messages: any[];
  created_at: string;
  updated_at: string;
}

interface HealthPlan {
  id: string;
  name: string;
  plan_number: string;
}

export default function ChatPage() {
  const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(null);
  const [showNewConversationDialog, setShowNewConversationDialog] = useState(false);
  const [healthPlans, setHealthPlans] = useState<HealthPlan[]>([]);
  const [chatStats, setChatStats] = useState({
    active_conversations: 0,
    total_messages: 0,
    average_response_time: 0
  });

  // New conversation form state
  const [newConversation, setNewConversation] = useState({
    member_id: '',
    health_plan_id: '',
    title: ''
  });

  useEffect(() => {
    loadHealthPlans();
    loadChatStats();
  }, []);

  const loadHealthPlans = async () => {
    try {
      // Get a test token if we don't have one
      let token = localStorage.getItem('auth_token');
      if (!token) {
        const tokenResponse = await fetch('http://localhost:8000/api/v1/auth/test-token');
        if (tokenResponse.ok) {
          const tokenData = await tokenResponse.json();
          token = tokenData.access_token;
          localStorage.setItem('auth_token', token);
        }
      }

      const response = await fetch('http://localhost:8000/api/v1/health-plans/?limit=100', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      if (response.ok) {
        const data = await response.json();
        setHealthPlans(data.health_plans || []);
        console.log('Loaded health plans:', data.health_plans);
      } else {
        console.error('Failed to load health plans:', response.status);
      }
    } catch (error) {
      console.error('Failed to load health plans:', error);
    }
  };

  const loadChatStats = async () => {
    try {
      // TODO: Implement chat stats endpoint
      setChatStats({
        active_conversations: 12,
        total_messages: 156,
        average_response_time: 2.3
      });
    } catch (error) {
      console.error('Failed to load chat stats:', error);
    }
  };

  const handleConversationSelect = async (conversation: Conversation) => {
    try {
      // Load full conversation with messages
      const response = await fetch(`/api/chat/conversations/${conversation.id}`);
      if (response.ok) {
        const fullConversation = await response.json();
        setSelectedConversation(fullConversation);
      } else {
        setSelectedConversation(conversation);
      }
    } catch (error) {
      console.error('Failed to load conversation:', error);
      setSelectedConversation(conversation);
    }
  };

  const handleNewConversation = () => {
    setShowNewConversationDialog(true);
  };

  const createNewConversation = async () => {
    if (!newConversation.member_id || !newConversation.title) {
      toast.error('Please fill in all required fields');
      return;
    }

    try {
      const response = await fetch('/api/chat/conversations', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newConversation)
      });

      if (!response.ok) {
        throw new Error('Failed to create conversation');
      }

      const conversation = await response.json();
      setSelectedConversation(conversation);
      setShowNewConversationDialog(false);
      setNewConversation({ member_id: '', health_plan_id: '', title: '' });
      toast.success('New conversation created');
    } catch (error) {
      console.error('Error creating conversation:', error);
      toast.error('Failed to create conversation');
    }
  };

  const handleConversationUpdate = (updatedConversation: Conversation) => {
    setSelectedConversation(updatedConversation);
    loadChatStats(); // Refresh stats
  };

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <h1 className="text-2xl font-semibold text-gray-900">Customer Service Chat</h1>
            <Badge variant="outline" className="text-sm">
              SmartSPD Assistant
            </Badge>
          </div>
          
          <div className="flex items-center space-x-4">
            {/* Quick Stats */}
            <div className="flex items-center space-x-6 text-sm text-gray-600">
              <div className="flex items-center space-x-1">
                <Activity className="w-4 h-4 text-green-500" />
                <span>{chatStats.active_conversations} active</span>
              </div>
              <div className="flex items-center space-x-1">
                <MessageCircle className="w-4 h-4 text-blue-500" />
                <span>{chatStats.total_messages} messages today</span>
              </div>
              <div className="flex items-center space-x-1">
                <Clock className="w-4 h-4 text-orange-500" />
                <span>{chatStats.average_response_time}s avg response</span>
              </div>
            </div>

            <Separator orientation="vertical" className="h-6" />

            <Button variant="outline" size="sm">
              <Settings className="w-4 h-4 mr-2" />
              Settings
            </Button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Conversations Sidebar */}
        <div className="w-80 border-r bg-white flex-shrink-0">
          <ConversationList
            selectedConversationId={selectedConversation?.id}
            onConversationSelect={handleConversationSelect}
            onNewConversation={handleNewConversation}
          />
        </div>

        {/* Chat Area */}
        <div className="flex-1 flex flex-col">
          {selectedConversation ? (
            <div className="flex-1 p-6">
              <ChatInterface
                conversation={selectedConversation}
                memberId={selectedConversation.member_id}
                healthPlanId={selectedConversation.health_plan_id}
                onConversationUpdate={handleConversationUpdate}
              />
            </div>
          ) : (
            <div className="flex-1 flex items-center justify-center bg-gray-50">
              <div className="text-center">
                <MessageCircle className="mx-auto h-16 w-16 text-gray-400 mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  Welcome to SmartSPD Chat
                </h3>
                <p className="text-gray-500 mb-6 max-w-md">
                  Select a conversation from the sidebar or start a new one to begin helping members with their health plan questions.
                </p>
                <Button onClick={handleNewConversation}>
                  <Plus className="w-4 h-4 mr-2" />
                  Start New Conversation
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* New Conversation Dialog */}
      <Dialog open={showNewConversationDialog} onOpenChange={setShowNewConversationDialog}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>Start New Conversation</DialogTitle>
            <DialogDescription>
              Create a new conversation with a member to help with their health plan questions.
            </DialogDescription>
          </DialogHeader>
          
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="member_id">Member ID *</Label>
              <Input
                id="member_id"
                value={newConversation.member_id}
                onChange={(e) => setNewConversation(prev => ({ ...prev, member_id: e.target.value }))}
                placeholder="Enter member ID"
              />
            </div>
            
            <div className="grid gap-2">
              <Label htmlFor="health_plan">Health Plan</Label>
              <Select
                value={newConversation.health_plan_id}
                onValueChange={(value) => setNewConversation(prev => ({ ...prev, health_plan_id: value }))}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select health plan" />
                </SelectTrigger>
                <SelectContent>
                  {healthPlans.map((plan) => (
                    <SelectItem key={plan.id} value={plan.id} className="py-3">
                      <div className="flex flex-col text-sm">
                        <span className="font-medium truncate max-w-[200px]">
                          {plan.name}
                        </span>
                        <span className="text-gray-500 text-xs">
                          Plan #{plan.plan_number}
                        </span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div className="grid gap-2">
              <Label htmlFor="title">Conversation Title *</Label>
              <Input
                id="title"
                value={newConversation.title}
                onChange={(e) => setNewConversation(prev => ({ ...prev, title: e.target.value }))}
                placeholder="Brief description of the inquiry"
              />
            </div>
          </div>
          
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowNewConversationDialog(false)}
            >
              Cancel
            </Button>
            <Button onClick={createNewConversation}>
              Start Conversation
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}