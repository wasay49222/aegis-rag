/* eslint-disable react-hooks/set-state-in-effect */
'use client';

import { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { 
  Shield, 
  AlertTriangle, 
  Eye, 
  FileText, 
  Lock,
  Search,
  Filter,
  RefreshCw
} from 'lucide-react';
import { api, type AuditLog, type AuditStats } from '@/lib/api';

export default function AuditLogsPage() {
  const [filter, setFilter] = useState('');
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [stats, setStats] = useState<AuditStats>({
    pii_redactions: 0,
    injections_blocked: 0,
    hallucinations: 0,
    documents: 0
  });
  const [loading, setLoading] = useState(true);

  const fetchAuditData = useCallback(async () => {
    try {
      const [logsResponse, statsResponse] = await Promise.all([
        api.getAuditLogs(),
        api.getAuditStats()
      ]);
      setLogs(logsResponse);
      setStats(statsResponse);
    } catch (error) {
      console.error('Failed to fetch audit data:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAuditData();
  }, [fetchAuditData]);

  const getEventIcon = (eventType: string) => {
    switch (eventType) {
      case 'PII_REDACTED': return <Lock className="h-4 w-4 text-amber-400" />;
      case 'INJECTION_BLOCKED': return <Shield className="h-4 w-4 text-red-400" />;
      case 'HALLUCINATION_FLAGGED': return <AlertTriangle className="h-4 w-4 text-orange-400" />;
      case 'DOCUMENT_INGESTED': return <FileText className="h-4 w-4 text-teal-400" />;
      default: return <Eye className="h-4 w-4 text-slate-400" />;
    }
  };

  const getEventColor = (eventType: string) => {
    switch (eventType) {
      case 'PII_REDACTED': return 'bg-amber-500/10 text-amber-400 border border-amber-500/20';
      case 'INJECTION_BLOCKED': return 'bg-red-500/10 text-red-400 border border-red-500/20';
      case 'HALLUCINATION_FLAGGED': return 'bg-orange-500/10 text-orange-400 border border-orange-500/20';
      case 'DOCUMENT_INGESTED': return 'bg-teal-500/10 text-teal-400 border border-teal-500/20';
      default: return 'bg-slate-500/10 text-slate-400 border border-slate-500/20';
    }
  };

  const filteredLogs = logs.filter(log =>
    log.event_type.toLowerCase().includes(filter.toLowerCase()) ||
    log.user_id.toLowerCase().includes(filter.toLowerCase())
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <RefreshCw className="h-8 w-8 animate-spin text-teal-400" />
        <span className="ml-3 text-slate-400">Loading audit logs...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-slate-100">Audit Logs</h1>
          <p className="text-slate-500 mt-1">Immutable security and compliance records</p>
        </div>
        <Button 
          onClick={fetchAuditData}
          variant="outline"
          size="sm"
          className="border-slate-700 text-slate-300"
        >
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="border-slate-800 bg-[#0d1527]">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <Lock className="h-5 w-5 text-amber-400" />
              <div>
                <p className="text-xs text-slate-400">PII Redactions</p>
                <p className="text-2xl font-bold text-slate-100">{stats.pii_redactions}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="border-slate-800 bg-[#0d1527]">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <Shield className="h-5 w-5 text-red-400" />
              <div>
                <p className="text-xs text-slate-400">Injections Blocked</p>
                <p className="text-2xl font-bold text-slate-100">{stats.injections_blocked}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="border-slate-800 bg-[#0d1527]">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <AlertTriangle className="h-5 w-5 text-orange-400" />
              <div>
                <p className="text-xs text-slate-400">Hallucinations</p>
                <p className="text-2xl font-bold text-slate-100">{stats.hallucinations}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="border-slate-800 bg-[#0d1527]">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <FileText className="h-5 w-5 text-teal-400" />
              <div>
                <p className="text-xs text-slate-400">Documents</p>
                <p className="text-2xl font-bold text-slate-100">{stats.documents}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filter */}
      <Card className="border-slate-800 bg-[#0d1527]">
        <CardContent className="pt-6">
          <div className="flex gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
              <input
                type="text"
                placeholder="Search by event type or user ID..."
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                className="w-full bg-[#111827] border border-slate-800 rounded-lg pl-10 pr-4 py-2 text-sm text-slate-100 focus:outline-none focus:border-teal-500"
              />
            </div>
            <Button variant="outline" className="border-slate-800 text-slate-300">
              <Filter className="h-4 w-4 mr-2" />
              Filter
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Logs List */}
      <Card className="border-slate-800 bg-[#0d1527]">
        <CardHeader>
          <CardTitle className="text-slate-200">Recent Events</CardTitle>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[500px]">
            <div className="space-y-3">
              {filteredLogs.length === 0 ? (
                <div className="text-center py-12 text-slate-500">
                  <Eye className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>No audit logs found</p>
                  <p className="text-sm mt-1">Events will appear here as they occur</p>
                </div>
              ) : (
                filteredLogs.map((log) => (
                  <div
                    key={log.id}
                    className="p-4 bg-[#111b33] border border-slate-800 rounded-xl"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex gap-3 w-full">
                        <div className="p-2 bg-slate-800 rounded-lg h-fit">
                          {getEventIcon(log.event_type)}
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center gap-2 flex-wrap">
                            <Badge className={getEventColor(log.event_type)}>
                              {log.event_type}
                            </Badge>
                            <span className="text-xs text-slate-500">
                              {new Date(log.created_at).toLocaleString()}
                            </span>
                          </div>
                          <p className="text-sm text-slate-300 mt-2">
                            User: <code className="text-teal-400">{log.user_id}</code>
                          </p>
                          {log.details && (
                            <pre className="text-xs text-slate-400 mt-2 bg-slate-900/50 p-2 rounded overflow-x-auto">
                              {JSON.stringify(log.details, null, 2)}
                            </pre>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
}