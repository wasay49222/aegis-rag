// src/app/query/page.tsx
'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Send, Shield, AlertTriangle, FileText } from 'lucide-react';
import { api, type QueryResponse } from '@/lib/api';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  sources?: string[];
  pii_redacted?: number;
  blocked?: boolean;
}

export default function QueryPage() {
  // Lazy initialization: runs only once on the client, avoiding useEffect setState warnings
  const [messages, setMessages] = useState<Message[]>(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('aegis_query_messages');
      if (saved) {
        try {
          return JSON.parse(saved);
        } catch (e) {
          console.error('Failed to load messages:', e);
        }
      }
    }
    return [];
  });

  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [documentId, setDocumentId] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || loading) return;

    const userMessage: Message = { role: 'user', content: question };
    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    setLoading(true);

    try {
      const response: QueryResponse = await api.query({
        question: question,
        document_id: documentId || undefined
      });

      const assistantMessage: Message = {
        role: 'assistant',
        content: response.answer,
        sources: response.sources,
        pii_redacted: response.pii_redacted_count,
        blocked: response.blocked
      };

      const updatedMessages = [...newMessages, assistantMessage];
      setMessages(updatedMessages);
      localStorage.setItem('aegis_query_messages', JSON.stringify(updatedMessages));
      setQuestion('');
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : 'Failed to get response';
      const errorMessage: Message = { role: 'assistant', content: `Error: ${message}` };
      const updatedMessages = [...newMessages, errorMessage];
      setMessages(updatedMessages);
      localStorage.setItem('aegis_query_messages', JSON.stringify(updatedMessages));
    } finally {
      setLoading(false);
    }
  };

  const clearConversation = () => {
    setMessages([]);
    localStorage.removeItem('aegis_query_messages');
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-slate-100">Query</h1>
          <p className="text-slate-500 mt-1">Ask questions about your documents</p>
        </div>
        {messages.length > 0 && (
          <Button 
            onClick={clearConversation}
            variant="outline"
            className="border-slate-700 text-slate-400 hover:text-red-400"
          >
            Clear Conversation
          </Button>
        )}
      </div>

      <Card className="border-slate-800 bg-[#0d1527]">
        <CardContent className="pt-6">
          <Input
            type="text"
            placeholder="Document ID (optional - leave empty to search all)"
            value={documentId}
            onChange={(e) => setDocumentId(e.target.value)}
            className="bg-[#111827] border-slate-800 text-slate-100"
          />
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="border-slate-800 bg-[#0d1527] lg:col-span-2 min-h-[500px]">
          <CardHeader>
            <CardTitle className="text-slate-200">Conversation</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4 max-h-[600px] overflow-y-auto">
              {messages.length === 0 ? (
                <div className="text-center py-12 text-slate-500">
                  <p>No messages yet. Ask a question to get started!</p>
                </div>
              ) : (
                messages.map((msg, idx) => (
                  <div
                    key={idx}
                    className={`p-4 rounded-xl ${
                      msg.role === 'user' ? 'bg-teal-500/10 border border-teal-500/20' : 'bg-[#111b33] border border-slate-800'
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <div className={`p-2 rounded-lg ${msg.role === 'user' ? 'bg-teal-500/20' : 'bg-indigo-500/20'}`}>
                        {msg.role === 'user' ? <Send className="h-4 w-4 text-teal-400" /> : <Shield className="h-4 w-4 text-indigo-400" />}
                      </div>
                      <div className="flex-1">
                        <p className="text-slate-200">{msg.content}</p>
                        {msg.role === 'assistant' && (
                          <div className="flex gap-2 mt-3">
                            {msg.pii_redacted && msg.pii_redacted > 0 && (
                              <Badge className="bg-amber-500/10 text-amber-400 border border-amber-500/20 text-xs">
                                <AlertTriangle className="h-3 w-3 mr-1" /> {msg.pii_redacted} PII redacted
                              </Badge>
                            )}
                            {msg.blocked && (
                              <Badge className="bg-red-500/10 text-red-400 border border-red-500/20 text-xs">
                                <AlertTriangle className="h-3 w-3 mr-1" /> Blocked by guardrails
                              </Badge>
                            )}
                          </div>
                        )}
                        {msg.sources && msg.sources.length > 0 && (
                          <div className="mt-3 space-y-2">
                            <p className="text-xs text-slate-400 font-medium">Sources:</p>
                            {msg.sources.slice(0, 3).map((source, sidx) => (
                              <div key={sidx} className="p-2 bg-slate-800/50 rounded-lg text-xs text-slate-400 truncate">
                                <FileText className="h-3 w-3 inline mr-1" /> {source.substring(0, 100)}...
                              </div>
                            ))}
                          </div>
        )}
                      </div>
                    </div>
                  </div>
                ))
              )}
              {loading && (
                <div className="p-4 bg-[#111b33] border border-slate-800 rounded-xl">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-indigo-500/20 rounded-lg"><Shield className="h-4 w-4 text-indigo-400" /></div>
                    <p className="text-slate-400">Processing with security guardrails...</p>
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-[#0d1527]">
          <CardHeader>
            <CardTitle className="text-slate-200">Ask a Question</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <textarea
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  placeholder="What would you like to know?"
                  className="w-full h-32 bg-[#111827] border border-slate-800 rounded-lg p-3 text-slate-100 resize-none focus:outline-none focus:border-teal-500"
                  disabled={loading}
                />
              </div>
              <Button type="submit" className="w-full bg-teal-600 hover:bg-teal-700" disabled={loading || !question.trim()}>
                <Send className="h-4 w-4 mr-2" /> {loading ? 'Processing...' : 'Send Question'}
              </Button>
            </form>
            <div className="mt-6 p-4 bg-emerald-500/5 border border-emerald-500/20 rounded-lg">
              <div className="flex items-start gap-2">
                <Shield className="h-4 w-4 text-emerald-400 mt-0.5" />
                <div>
                  <p className="text-xs font-medium text-emerald-400">Security Active</p>
                  <p className="text-xs text-slate-400 mt-1">All queries are screened for PII and prompt injection attempts</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}