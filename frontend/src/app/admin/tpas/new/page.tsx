'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { 
  ArrowLeft, 
  Save, 
  Building2, 
  Globe, 
  FileText, 
  Settings, 
  AlertCircle 
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface TPAFormData {
  name: string;
  slug: string;
  description: string;
  website: string;
  contact_email: string;
  contact_phone: string;
  address: {
    street: string;
    city: string;
    state: string;
    zip_code: string;
    country: string;
  };
  settings: {
    max_users: number;
    max_documents: number;
    storage_limit_gb: number;
    api_rate_limit: number;
  };
  is_active: boolean;
}

export default function NewTPAPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  
  const [formData, setFormData] = useState<TPAFormData>({
    name: '',
    slug: '',
    description: '',
    website: '',
    contact_email: '',
    contact_phone: '',
    address: {
      street: '',
      city: '',
      state: '',
      zip_code: '',
      country: 'US'
    },
    settings: {
      max_users: 100,
      max_documents: 1000,
      storage_limit_gb: 10,
      api_rate_limit: 1000
    },
    is_active: true
  });

  const handleInputChange = (field: string, value: any) => {
    if (field.includes('.')) {
      const [parent, child] = field.split('.');
      setFormData(prev => ({
        ...prev,
        [parent]: {
          ...prev[parent as keyof TPAFormData],
          [child]: value
        }
      }));
    } else {
      setFormData(prev => ({
        ...prev,
        [field]: value
      }));
    }
  };

  const generateSlug = (name: string) => {
    return name
      .toLowerCase()
      .replace(/[^a-z0-9\s-]/g, '')
      .replace(/\s+/g, '-')
      .replace(/-+/g, '-')
      .trim();
  };

  const handleNameChange = (value: string) => {
    handleInputChange('name', value);
    if (!formData.slug || formData.slug === generateSlug(formData.name)) {
      handleInputChange('slug', generateSlug(value));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      // Import API client
      const { apiClient } = await import('@/lib/api-client');
      
      const response = await apiClient.admin.createTpa(formData);
      
      if (response.error) {
        setError(response.error);
        return;
      }
      
      setSuccess(true);
      setTimeout(() => {
        router.push('/admin/tpas');
      }, 2000);
      
    } catch (err) {
      console.error('Failed to create TPA:', err);
      setError('Failed to create TPA. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="p-6">
        <Alert className="max-w-md mx-auto">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            TPA created successfully! Redirecting to TPA management...
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <Button
          variant="outline"
          size="sm"
          onClick={() => router.back()}
          className="flex items-center gap-2"
        >
          <ArrowLeft className="w-4 h-4" />
          Back
        </Button>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Create New TPA</h1>
          <p className="text-gray-600">Add a new Third Party Administrator to the system</p>
        </div>
      </div>

      {error && (
        <Alert variant="destructive" className="mb-6">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Basic Information */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Building2 className="w-5 h-5" />
              Basic Information
            </CardTitle>
            <CardDescription>
              Essential details about the TPA organization
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="name">TPA Name *</Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) => handleNameChange(e.target.value)}
                  placeholder="e.g., Acme Benefits Corp"
                  required
                />
              </div>
              <div>
                <Label htmlFor="slug">URL Slug *</Label>
                <Input
                  id="slug"
                  value={formData.slug}
                  onChange={(e) => handleInputChange('slug', e.target.value)}
                  placeholder="acme-benefits-corp"
                  required
                />
                <p className="text-sm text-gray-500 mt-1">
                  Used in URLs and API endpoints. Must be unique.
                </p>
              </div>
            </div>
            
            <div>
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                value={formData.description}
                onChange={(e) => handleInputChange('description', e.target.value)}
                placeholder="Brief description of the TPA..."
                rows={3}
              />
            </div>
          </CardContent>
        </Card>

        {/* Contact Information */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Globe className="w-5 h-5" />
              Contact Information
            </CardTitle>
            <CardDescription>
              Primary contact details for the TPA
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="website">Website</Label>
                <Input
                  id="website"
                  type="url"
                  value={formData.website}
                  onChange={(e) => handleInputChange('website', e.target.value)}
                  placeholder="https://www.example.com"
                />
              </div>
              <div>
                <Label htmlFor="contact_email">Contact Email *</Label>
                <Input
                  id="contact_email"
                  type="email"
                  value={formData.contact_email}
                  onChange={(e) => handleInputChange('contact_email', e.target.value)}
                  placeholder="contact@example.com"
                  required
                />
              </div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="contact_phone">Contact Phone</Label>
                <Input
                  id="contact_phone"
                  type="tel"
                  value={formData.contact_phone}
                  onChange={(e) => handleInputChange('contact_phone', e.target.value)}
                  placeholder="(555) 123-4567"
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Address */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="w-5 h-5" />
              Address
            </CardTitle>
            <CardDescription>
              Physical business address
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="street">Street Address</Label>
              <Input
                id="street"
                value={formData.address.street}
                onChange={(e) => handleInputChange('address.street', e.target.value)}
                placeholder="123 Main Street"
              />
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <Label htmlFor="city">City</Label>
                <Input
                  id="city"
                  value={formData.address.city}
                  onChange={(e) => handleInputChange('address.city', e.target.value)}
                  placeholder="New York"
                />
              </div>
              <div>
                <Label htmlFor="state">State/Province</Label>
                <Input
                  id="state"
                  value={formData.address.state}
                  onChange={(e) => handleInputChange('address.state', e.target.value)}
                  placeholder="NY"
                />
              </div>
              <div>
                <Label htmlFor="zip_code">ZIP/Postal Code</Label>
                <Input
                  id="zip_code"
                  value={formData.address.zip_code}
                  onChange={(e) => handleInputChange('address.zip_code', e.target.value)}
                  placeholder="10001"
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* System Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Settings className="w-5 h-5" />
              System Settings
            </CardTitle>
            <CardDescription>
              Resource limits and configuration
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="max_users">Maximum Users</Label>
                <Input
                  id="max_users"
                  type="number"
                  min="1"
                  value={formData.settings.max_users}
                  onChange={(e) => handleInputChange('settings.max_users', parseInt(e.target.value))}
                />
              </div>
              <div>
                <Label htmlFor="max_documents">Maximum Documents</Label>
                <Input
                  id="max_documents"
                  type="number"
                  min="1"
                  value={formData.settings.max_documents}
                  onChange={(e) => handleInputChange('settings.max_documents', parseInt(e.target.value))}
                />
              </div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="storage_limit_gb">Storage Limit (GB)</Label>
                <Input
                  id="storage_limit_gb"
                  type="number"
                  min="1"
                  value={formData.settings.storage_limit_gb}
                  onChange={(e) => handleInputChange('settings.storage_limit_gb', parseInt(e.target.value))}
                />
              </div>
              <div>
                <Label htmlFor="api_rate_limit">API Rate Limit (requests/hour)</Label>
                <Input
                  id="api_rate_limit"
                  type="number"
                  min="100"
                  value={formData.settings.api_rate_limit}
                  onChange={(e) => handleInputChange('settings.api_rate_limit', parseInt(e.target.value))}
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Form Actions */}
        <div className="flex justify-end gap-3 pt-6 border-t">
          <Button
            type="button"
            variant="outline"
            onClick={() => router.back()}
            disabled={loading}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            disabled={loading || !formData.name || !formData.contact_email}
            className="flex items-center gap-2"
          >
            {loading ? (
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
            ) : (
              <Save className="w-4 h-4" />
            )}
            {loading ? 'Creating...' : 'Create TPA'}
          </Button>
        </div>
      </form>
    </div>
  );
}