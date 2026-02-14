import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Shield, CheckCircle, AlertTriangle, FileText, Database, Lock } from 'lucide-react';
import { apiService } from '@/lib/api-service';

interface ComplianceStatus {
  dpa_2019_status: string;
  last_audit: string;
  next_review: string;
  certificate_valid: boolean;
  data_sovereignty: string;
  encryption_standards: {
    at_rest: string;
    in_transit: string;
  };
}

interface ComplianceMetrics {
  audit_score: number;
  data_protection_score: number;
  security_measures_score: number;
  privacy_controls_score: number;
  overall_compliance: number;
}

const ComplianceDashboard: React.FC = () => {
  const [complianceStatus, setComplianceStatus] = useState<ComplianceStatus | null>(null);
  const [metrics, setMetrics] = useState<ComplianceMetrics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchComplianceData();
  }, []);

  const fetchComplianceData = async () => {
    try {
      const statusResponse = await apiService.get('/training/compliance');
      setComplianceStatus(statusResponse.data);

      // Mock metrics for now - in production, these would come from the API
      setMetrics({
        audit_score: 98,
        data_protection_score: 95,
        security_measures_score: 99,
        privacy_controls_score: 97,
        overall_compliance: 97.3
      });
    } catch (error) {
      console.error('Failed to fetch compliance data:', error);
    } finally {
      setLoading(false);
    }
  };

  const conductAudit = async () => {
    try {
      const response = await apiService.post('/training/compliance/audit');
      if (response.data.status === 'completed') {
        fetchComplianceData(); // Refresh data
      }
    } catch (error) {
      console.error('Failed to conduct audit:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">DPA 2019 Compliance</h1>
          <p className="text-gray-600 mt-1">Data Protection Act 2019 - Section 31 Assessment</p>
        </div>
        <button
          onClick={conductAudit}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          <FileText className="h-4 w-4" />
          Conduct Audit
        </button>
      </div>

      {/* Compliance Status Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5 text-green-600" />
            Compliance Status
          </CardTitle>
        </CardHeader>
        <CardContent>
          {complianceStatus && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <Badge className={complianceStatus.certificate_valid ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}>
                    {complianceStatus.dpa_2019_status}
                  </Badge>
                  {complianceStatus.certificate_valid && (
                    <CheckCircle className="h-4 w-4 text-green-600" />
                  )}
                </div>
                <p className="text-sm text-gray-600">Certificate Valid: {complianceStatus.certificate_valid ? 'Yes' : 'No'}</p>
              </div>
              
              <div className="space-y-2">
                <p className="text-sm font-medium">Data Sovereignty</p>
                <div className="flex items-center gap-2">
                  <Database className="h-4 w-4 text-blue-600" />
                  <span className="text-sm">{complianceStatus.data_sovereignty}</span>
                </div>
              </div>
              
              <div className="space-y-2">
                <p className="text-sm font-medium">Encryption Standards</p>
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <Lock className="h-3 w-3 text-gray-600" />
                    <span className="text-xs">At Rest: {complianceStatus.encryption_standards.at_rest}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Lock className="h-3 w-3 text-gray-600" />
                    <span className="text-xs">In Transit: {complianceStatus.encryption_standards.in_transit}</span>
                  </div>
                </div>
              </div>
              
              <div className="space-y-2">
                <p className="text-sm font-medium">Last Audit</p>
                <p className="text-sm text-gray-600">{new Date(complianceStatus.last_audit).toLocaleDateString()}</p>
              </div>
              
              <div className="space-y-2">
                <p className="text-sm font-medium">Next Review</p>
                <p className="text-sm text-gray-600">{new Date(complianceStatus.next_review).toLocaleDateString()}</p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Compliance Metrics */}
      {metrics && (
        <Card>
          <CardHeader>
            <CardTitle>Compliance Metrics</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Audit Score</span>
                  <span className="text-sm font-bold">{metrics.audit_score}%</span>
                </div>
                <Progress value={metrics.audit_score} className="h-2" />
              </div>
              
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Data Protection</span>
                  <span className="text-sm font-bold">{metrics.data_protection_score}%</span>
                </div>
                <Progress value={metrics.data_protection_score} className="h-2" />
              </div>
              
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Security Measures</span>
                  <span className="text-sm font-bold">{metrics.security_measures_score}%</span>
                </div>
                <Progress value={metrics.security_measures_score} className="h-2" />
              </div>
              
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Privacy Controls</span>
                  <span className="text-sm font-bold">{metrics.privacy_controls_score}%</span>
                </div>
                <Progress value={metrics.privacy_controls_score} className="h-2" />
              </div>
              
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Overall Compliance</span>
                  <span className="text-lg font-bold text-green-600">{metrics.overall_compliance}%</span>
                </div>
                <Progress value={metrics.overall_compliance} className="h-3" />
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Compliance Requirements */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            DPA 2019 Requirements Status
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[
              { requirement: "Lawful Processing", status: "compliant", description: "All data processing has legal basis" },
              { requirement: "Data Minimization", status: "compliant", description: "Only essential data collected" },
              { requirement: "Purpose Limitation", status: "compliant", description: "Data used only for stated purposes" },
              { requirement: "Accuracy & Updates", status: "compliant", description: "Data verification mechanisms in place" },
              { requirement: "Storage Limitation", status: "compliant", description: "Defined retention periods" },
              { requirement: "Security Measures", status: "compliant", description: "AES-256 and TLS 1.3 implemented" },
              { requirement: "Data Subject Rights", status: "compliant", description: "All rights mechanisms implemented" },
              { requirement: "Cross-Border Transfer", status: "compliant", description: "Data remains in Kenya only" }
            ].map((item, index) => (
              <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                <div className="flex-1">
                  <p className="font-medium">{item.requirement}</p>
                  <p className="text-sm text-gray-600">{item.description}</p>
                </div>
                <Badge className={item.status === 'compliant' ? "bg-green-100 text-green-800" : "bg-yellow-100 text-yellow-800"}>
                  {item.status === 'compliant' ? 'Compliant' : 'In Progress'}
                </Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ComplianceDashboard;
