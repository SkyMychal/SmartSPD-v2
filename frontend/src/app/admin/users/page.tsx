'use client';

import { useState, useEffect } from 'react';
import { 
  Users, 
  Plus,
  Search,
  Filter,
  Edit,
  Trash2,
  MoreHorizontal,
  UserCheck,
  UserX,
  Key,
  Eye,
  EyeOff
} from 'lucide-react';

interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  tpa_id: string;
  is_active: boolean;
  last_login_at?: string;
  created_at: string;
}

interface TPA {
  id: string;
  name: string;
  slug: string;
}

export default function AdminUsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [tpas, setTPAs] = useState<TPA[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedTPA, setSelectedTPA] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [showUserMenu, setShowUserMenu] = useState<string | null>(null);

  useEffect(() => {
    fetchUsers();
    fetchTPAs();
  }, [searchTerm, selectedTPA, statusFilter]);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      
      if (searchTerm) params.append('search', searchTerm);
      if (selectedTPA) params.append('tpa_id', selectedTPA);
      if (statusFilter) params.append('is_active', statusFilter);
      
      const response = await fetch(`/api/v1/admin/users?${params}`);
      if (!response.ok) throw new Error('Failed to fetch users');
      
      const data = await response.json();
      setUsers(data);
    } catch (error) {
      console.error('Failed to fetch users:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchTPAs = async () => {
    try {
      const response = await fetch('/api/v1/admin/tpas');
      if (!response.ok) throw new Error('Failed to fetch TPAs');
      
      const data = await response.json();
      setTPAs(data);
    } catch (error) {
      console.error('Failed to fetch TPAs:', error);
    }
  };

  const toggleUserStatus = async (userId: string) => {
    try {
      const response = await fetch(`/api/v1/admin/users/${userId}/toggle-status`, {
        method: 'POST',
      });
      
      if (!response.ok) throw new Error('Failed to toggle user status');
      
      fetchUsers(); // Refresh the list
      setShowUserMenu(null);
    } catch (error) {
      console.error('Failed to toggle user status:', error);
    }
  };

  const deleteUser = async (userId: string) => {
    if (!confirm('Are you sure you want to delete this user? This action cannot be undone.')) {
      return;
    }

    try {
      const response = await fetch(`/api/v1/admin/users/${userId}`, {
        method: 'DELETE',
      });
      
      if (!response.ok) throw new Error('Failed to delete user');
      
      fetchUsers(); // Refresh the list
      setShowUserMenu(null);
    } catch (error) {
      console.error('Failed to delete user:', error);
    }
  };

  const resetPassword = async (userId: string) => {
    const newPassword = prompt('Enter new password for this user:');
    if (!newPassword) return;

    try {
      const response = await fetch(`/api/v1/admin/users/${userId}/reset-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ new_password: newPassword }),
      });
      
      if (!response.ok) throw new Error('Failed to reset password');
      
      alert('Password reset successfully');
      setShowUserMenu(null);
    } catch (error) {
      console.error('Failed to reset password:', error);
    }
  };

  const getRoleBadge = (role: string) => {
    const roleConfig = {
      tpa_admin: { color: 'bg-red-100 text-red-800', label: 'Admin' },
      cs_manager: { color: 'bg-purple-100 text-purple-800', label: 'Manager' },
      cs_agent: { color: 'bg-blue-100 text-blue-800', label: 'Agent' },
      member: { color: 'bg-green-100 text-green-800', label: 'Member' },
      readonly: { color: 'bg-gray-100 text-gray-800', label: 'Read Only' }
    };

    const config = roleConfig[role as keyof typeof roleConfig] || roleConfig.readonly;
    
    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${config.color}`}>
        {config.label}
      </span>
    );
  };

  const getStatusBadge = (isActive: boolean) => {
    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${
        isActive 
          ? 'bg-green-100 text-green-800' 
          : 'bg-red-100 text-red-800'
      }`}>
        {isActive ? 'Active' : 'Inactive'}
      </span>
    );
  };

  return (
    <div className="p-4 sm:p-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center mb-6 gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-gray-900">User Management</h1>
          <p className="text-sm sm:text-base text-gray-600">Manage user accounts across all TPAs</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 w-full sm:w-auto"
        >
          <Plus className="w-4 h-4" />
          <span>Add User</span>
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              type="text"
              placeholder="Search users..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          
          <select
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={selectedTPA}
            onChange={(e) => setSelectedTPA(e.target.value)}
          >
            <option value="">All TPAs</option>
            {tpas.map((tpa) => (
              <option key={tpa.id} value={tpa.id}>{tpa.name}</option>
            ))}
          </select>
          
          <select
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="">All Status</option>
            <option value="true">Active</option>
            <option value="false">Inactive</option>
          </select>
          
          <div className="sm:col-span-2 lg:col-span-1">
            <button
              onClick={fetchUsers}
              className="w-full sm:w-auto px-3 py-2 border border-gray-300 rounded-md hover:bg-gray-50 flex items-center justify-center"
            >
              <Filter className="w-4 h-4 mr-2" />
              <span className="sm:hidden">Apply Filters</span>
            </button>
          </div>
        </div>
      </div>

      {/* Users Table - Desktop */}
      <div className="hidden lg:block bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  User
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  TPA
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Role
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Last Login
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Created
                </th>
                <th className="relative px-6 py-3">
                  <span className="sr-only">Actions</span>
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {loading ? (
                <tr>
                  <td colSpan={7} className="px-6 py-4 text-center">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mx-auto"></div>
                  </td>
                </tr>
              ) : users.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-4 text-center text-gray-500">
                    No users found
                  </td>
                </tr>
              ) : (
                users.map((user) => {
                  const tpa = tpas.find(t => t.id === user.tpa_id);
                  return (
                    <tr key={user.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <div className="text-sm font-medium text-gray-900">
                            {user.first_name} {user.last_name}
                          </div>
                          <div className="text-sm text-gray-500">{user.email}</div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {tpa?.name || 'Unknown'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {getRoleBadge(user.role)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {getStatusBadge(user.is_active)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {user.last_login_at 
                          ? new Date(user.last_login_at).toLocaleDateString()
                          : 'Never'
                        }
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(user.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium relative">
                        <button
                          onClick={() => setShowUserMenu(showUserMenu === user.id ? null : user.id)}
                          className="text-gray-400 hover:text-gray-600"
                        >
                          <MoreHorizontal className="w-4 h-4" />
                        </button>
                        
                        {showUserMenu === user.id && (
                          <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg z-10 border">
                            <div className="py-1">
                              <button
                                onClick={() => toggleUserStatus(user.id)}
                                className="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 w-full text-left"
                              >
                                {user.is_active ? (
                                  <>
                                    <UserX className="w-4 h-4" />
                                    Deactivate
                                  </>
                                ) : (
                                  <>
                                    <UserCheck className="w-4 h-4" />
                                    Activate
                                  </>
                                )}
                              </button>
                              <button
                                onClick={() => resetPassword(user.id)}
                                className="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 w-full text-left"
                              >
                                <Key className="w-4 h-4" />
                                Reset Password
                              </button>
                              <button
                                onClick={() => setSelectedUser(user)}
                                className="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 w-full text-left"
                              >
                                <Edit className="w-4 h-4" />
                                Edit User
                              </button>
                              <button
                                onClick={() => deleteUser(user.id)}
                                className="flex items-center gap-2 px-4 py-2 text-sm text-red-600 hover:bg-red-50 w-full text-left"
                              >
                                <Trash2 className="w-4 h-4" />
                                Delete
                              </button>
                            </div>
                          </div>
                        )}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Users List - Mobile */}
      <div className="lg:hidden bg-white rounded-lg shadow divide-y divide-gray-200">
        {loading ? (
          <div className="p-6 text-center">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mx-auto"></div>
          </div>
        ) : users.length === 0 ? (
          <div className="p-6 text-center text-gray-500">
            No users found
          </div>
        ) : (
          users.map((user) => {
            const tpa = tpas.find(t => t.id === user.tpa_id);
            return (
              <div key={user.id} className="p-4 hover:bg-gray-50">
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-3 mb-2">
                      <div className="flex-1 min-w-0">
                        <h3 className="text-sm font-medium text-gray-900 truncate">
                          {user.first_name} {user.last_name}
                        </h3>
                        <p className="text-sm text-gray-500 truncate">{user.email}</p>
                      </div>
                      <div className="flex-shrink-0">
                        {getStatusBadge(user.is_active)}
                      </div>
                    </div>
                    
                    <div className="flex flex-wrap items-center gap-2 mb-3">
                      {getRoleBadge(user.role)}
                      <span className="px-2 py-1 text-xs font-medium rounded-full bg-gray-100 text-gray-800">
                        {tpa?.name || 'Unknown TPA'}
                      </span>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-2 text-xs text-gray-500">
                      <div>
                        <span className="font-medium">Last Login:</span><br/>
                        {user.last_login_at 
                          ? new Date(user.last_login_at).toLocaleDateString()
                          : 'Never'
                        }
                      </div>
                      <div>
                        <span className="font-medium">Created:</span><br/>
                        {new Date(user.created_at).toLocaleDateString()}
                      </div>
                    </div>
                  </div>
                  
                  <div className="ml-4 flex-shrink-0 relative">
                    <button
                      onClick={() => setShowUserMenu(showUserMenu === user.id ? null : user.id)}
                      className="p-2 text-gray-400 hover:text-gray-600 rounded-full hover:bg-gray-100"
                    >
                      <MoreHorizontal className="w-5 h-5" />
                    </button>
                    
                    {showUserMenu === user.id && (
                      <div className="absolute right-0 top-10 w-48 bg-white rounded-md shadow-lg z-10 border">
                        <div className="py-1">
                          <button
                            onClick={() => toggleUserStatus(user.id)}
                            className="flex items-center gap-2 px-4 py-3 text-sm text-gray-700 hover:bg-gray-100 w-full text-left"
                          >
                            {user.is_active ? (
                              <>
                                <UserX className="w-4 h-4" />
                                Deactivate
                              </>
                            ) : (
                              <>
                                <UserCheck className="w-4 h-4" />
                                Activate
                              </>
                            )}
                          </button>
                          <button
                            onClick={() => resetPassword(user.id)}
                            className="flex items-center gap-2 px-4 py-3 text-sm text-gray-700 hover:bg-gray-100 w-full text-left"
                          >
                            <Key className="w-4 h-4" />
                            Reset Password
                          </button>
                          <button
                            onClick={() => setSelectedUser(user)}
                            className="flex items-center gap-2 px-4 py-3 text-sm text-gray-700 hover:bg-gray-100 w-full text-left"
                          >
                            <Edit className="w-4 h-4" />
                            Edit User
                          </button>
                          <button
                            onClick={() => deleteUser(user.id)}
                            className="flex items-center gap-2 px-4 py-3 text-sm text-red-600 hover:bg-red-50 w-full text-left"
                          >
                            <Trash2 className="w-4 h-4" />
                            Delete
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Summary */}
      <div className="mt-4 text-sm text-gray-600 text-center">
        Showing {users.length} users
      </div>
    </div>
  );
}