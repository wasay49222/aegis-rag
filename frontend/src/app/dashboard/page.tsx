/* eslint-disable react-hooks/set-state-in-effect */
'use client';

import { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { 
  Shield, 
  AlertTriangle, 
  Lock, 
  FileText, 
  TrendingUp,
  RefreshCw,
  CheckCircle,
  MessageSquare,
  Activity
} from 'lucide-react';
import { api, type DashboardStats, type RecentActivity } from '@/lib/api';
import { useRouter } from 'next/navigation';

export default function DashboardPage() {
  const router = useRouter();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recentActivity, setRecentActivity] = useState<RecentActivity[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchDashboardData = useCallback(async () => {
    try {
      const [statsData, activityData] = await Promise.all([
        api.getDashboardStats(),
        api.getRecentActivity(5)
      ]);
      setStats(statsData);
      setRecentActivity(activityData);
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <RefreshCw className="h-8 w-8 animate-spin text-teal-400" />
        <span className="ml-3 text-slate-400">Loading dashboard...</span>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <AlertTriangle className="h-12 w-12 text-red-400 mx-auto mb-4" />
          <p className="text-slate-400">Failed to load dashboard data</p>
          <Button 
            onClick={fetchDashboardData}
            className="mt-4"
            variant="outline"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry
          </Button>
        </div>
      </div>
    );
  }

  const getEventIcon = (eventType: string) => {
    switch (eventType) {
      case 'PII_REDACTED': return <Lock className="h-4 w-4 text-amber-400" />;
      case 'INJECTION_BLOCKED': return <Shield className="h-4 w-4 text-red-400" />;
      case 'HALLUCINATION_FLAGGED': return <AlertTriangle className="h-4 w-4 text-orange-400" />;
      case 'QUERY_EXECUTED': return <MessageSquare className="h-4 w-4 text-teal-400" />;
      case 'DOCUMENT_INGESTED': return <FileText className="h-4 w-4 text-blue-400" />;
      default: return <Activity className="h-4 w-4 text-slate-400" />;
    }
  };

  const getEventColor = (eventType: string) => {
    switch (eventType) {
      case 'PII_REDACTED': return 'bg-amber-500/10 text-amber-400 border border-amber-500/20';
      case 'INJECTION_BLOCKED': return 'bg-red-500/10 text-red-400 border border-red-500/20';
      case 'HALLUCINATION_FLAGGED': return 'bg-orange-500/10 text-orange-400 border border-orange-500/20';
      case 'QUERY_EXECUTED': return 'bg-teal-500/10 text-teal-400 border border-teal-500/20';
      case 'DOCUMENT_INGESTED': return 'bg-blue-500/10 text-blue-400 border border-blue-500/20';
      default: return 'bg-slate-500/10 text-slate-400 border border-slate-500/20';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-slate-100">
            Aegis-RAG: Enterprise Secure Agentic AI
          </h1>
          <p className="text-slate-500 mt-1">
            Real-time security monitoring and multi-agent workflow validation
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Badge className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <CheckCircle className="h-3 w-3 mr-1" />
            SOC2 Compliant
          </Badge>
          <Button 
            onClick={fetchDashboardData}
            variant="outline"
            size="sm"
            className="border-slate-700 text-slate-300"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Security Guardrails */}
      <Card className="border-slate-800 bg-[#0d1527]">
        <CardHeader>
          <CardTitle className="text-slate-200 flex items-center gap-2">
            <Shield className="h-5 w-5 text-teal-400" />
            System Security Guardrails
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 bg-[#111b33] border border-slate-800 rounded-xl">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-slate-400">PII Redactions</p>
                  <p className="text-2xl font-bold text-teal-400 mt-1">
                    {stats.security.pii_redactions}
                  </p>
                  <p className="text-xs text-slate-500 mt-1">Last 30 days</p>
                </div>
                <Lock className="h-8 w-8 text-teal-400/20" />
              </div>
            </div>

            <div className="p-4 bg-[#111b33] border border-slate-800 rounded-xl">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-slate-400">Injections Blocked</p>
                  <p className="text-2xl font-bold text-red-400 mt-1">
                    {stats.security.injections_blocked}
                  </p>
                  <p className="text-xs text-slate-500 mt-1">Last 30 days</p>
                </div>
                <Shield className="h-8 w-8 text-red-400/20" />
              </div>
            </div>

            <div className="p-4 bg-[#111b33] border border-slate-800 rounded-xl">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-slate-400">Hallucination Prevention</p>
                  <div className="flex items-center gap-2 mt-1">
                    <p className="text-2xl font-bold text-amber-400">
                      {stats.security.hallucinations}
                    </p>
                    <Badge className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-xs">
                      Active
                    </Badge>
                  </div>
                  <p className="text-xs text-slate-500 mt-1">Last 30 days</p>
                </div>
                <AlertTriangle className="h-8 w-8 text-amber-400/20" />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* MLOps Performance & Stats Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* MLOps Performance */}
        <Card className="border-slate-800 bg-[#0d1527]">
          <CardHeader>
            <CardTitle className="text-slate-200 flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-blue-400" />
              RAG MLOps Performance
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-[#111b33] border border-slate-800 rounded-xl">
                <span className="text-sm text-slate-300">Faithfulness</span>
                <div className="flex items-center gap-2">
                  <span className="text-xl font-bold text-emerald-400">
                    {stats.mlops.faithfulness}
                  </span>
                  <Badge className="bg-emerald-500/10 text-emerald-400 text-xs">
                    Good
                  </Badge>
                </div>
              </div>

              <div className="flex items-center justify-between p-4 bg-[#111b33] border border-slate-800 rounded-xl">
                <span className="text-sm text-slate-300">Answer Relevance</span>
                <div className="flex items-center gap-2">
                  <span className="text-xl font-bold text-emerald-400">
                    {stats.mlops.answer_relevance}
                  </span>
                  <Badge className="bg-emerald-500/10 text-emerald-400 text-xs">
                    Good
                  </Badge>
                </div>
              </div>

              <div className="flex items-center justify-between p-4 bg-[#111b33] border border-slate-800 rounded-xl">
                <span className="text-sm text-slate-300">Context Precision</span>
                <div className="flex items-center gap-2">
                  <span className="text-xl font-bold text-blue-400">
                    {stats.mlops.context_precision}
                  </span>
                  <Badge className="bg-blue-500/10 text-blue-400 text-xs">
                    Good
                  </Badge>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Quick Stats */}
        <Card className="border-slate-800 bg-[#0d1527]">
          <CardHeader>
            <CardTitle className="text-slate-200 flex items-center gap-2">
              <Activity className="h-5 w-5 text-purple-400" />
              Quick Stats
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-[#111b33] border border-slate-800 rounded-xl">
                <div className="flex items-center gap-3">
                  <FileText className="h-5 w-5 text-blue-400" />
                  <span className="text-sm text-slate-300">Documents</span>
                </div>
                <span className="text-xl font-bold text-slate-100">
                  {stats.documents}
                </span>
              </div>

              <div className="flex items-center justify-between p-4 bg-[#111b33] border border-slate-800 rounded-xl">
                <div className="flex items-center gap-3">
                  <MessageSquare className="h-5 w-5 text-teal-400" />
                  <span className="text-sm text-slate-300">Queries</span>
                </div>
                <span className="text-xl font-bold text-slate-100">
                  {stats.queries}
                </span>
              </div>

              <div className="p-4 bg-[#111b33] border border-slate-800 rounded-xl">
                <p className="text-xs text-slate-400 mb-2">System Status</p>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />
                  <span className="text-sm text-emerald-400 font-medium">
                    All systems operational
                  </span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Activity */}
      <Card className="border-slate-800 bg-[#0d1527]">
        <CardHeader>
          <CardTitle className="text-slate-200">Recent Activity</CardTitle>
        </CardHeader>
        <CardContent>
          {recentActivity.length === 0 ? (
            <div className="text-center py-8 text-slate-500">
              <Activity className="h-12 w-12 mx-auto mb-3 opacity-50" />
              <p>No recent activity</p>
            </div>
          ) : (
            <div className="space-y-3">
              {recentActivity.map((activity) => (
                <div
                  key={activity.id}
                  className="flex items-center justify-between p-4 bg-[#111b33] border border-slate-800 rounded-xl"
                >
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-slate-800 rounded-lg">
                      {getEventIcon(activity.event_type)}
                    </div>
                    <div>
                      <Badge className={getEventColor(activity.event_type)}>
                        {activity.event_type}
                      </Badge>
                      <p className="text-xs text-slate-500 mt-1">
                        {new Date(activity.created_at).toLocaleString()}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <Card className="border-slate-800 bg-[#0d1527]">
        <CardHeader>
          <CardTitle className="text-slate-200">Quick Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <Button 
              onClick={() => router.push('/documents')}
              className="bg-teal-600 hover:bg-teal-700"
            >
              <FileText className="h-4 w-4 mr-2" />
              Upload Document
            </Button>
            <Button 
              onClick={() => router.push('/query')}
              variant="outline" 
              className="border-slate-700 text-slate-300"
            >
              <MessageSquare className="h-4 w-4 mr-2" />
              Ask a Question
            </Button>
            <Button 
              onClick={() => router.push('/audit')}
              variant="outline" 
              className="border-slate-700 text-slate-300"
            >
              <Shield className="h-4 w-4 mr-2" />
              View Audit Logs
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}