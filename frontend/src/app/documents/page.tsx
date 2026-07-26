// src/app/documents/page.tsx
'use client';

import { useState, useCallback, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Upload, FileText, Trash2, CheckCircle, AlertCircle } from 'lucide-react';
import { api } from '@/lib/api';

interface Document {
  id: string;
  title: string;
  chunk_count: number;
  created_at: string;
  status: 'ingested' | 'processing' | 'error';
}

export default function DocumentsPage() {
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState('');
  
  // 1. Initialize state from localStorage
  const [documents, setDocuments] = useState<Document[]>(() => {
    if (typeof window !== 'undefined') {
      const savedDocs = localStorage.getItem('aegis_documents');
      if (savedDocs) {
        try {
          return JSON.parse(savedDocs);
        } catch (e) {
          console.error('Failed to load documents:', e);
        }
      }
    }
    return [];
  });

  // 2. Save to localStorage whenever documents change
  useEffect(() => {
    if (typeof window !== 'undefined' && documents.length > 0) {
      localStorage.setItem('aegis_documents', JSON.stringify(documents));
    }
  }, [documents]);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;

    setUploading(true);
    const file = acceptedFiles[0];
    setUploadProgress(`Uploading ${file.name}...`);

    try {
      const response = await api.uploadDocument(file);
      setUploadProgress(`✓ Successfully ingested ${response.chunk_count} chunks`);
      
      // Add to documents list
      const newDoc: Document = {
        id: response.document_id,
        title: file.name,
        chunk_count: response.chunk_count,
        created_at: new Date().toISOString(),
        status: 'ingested'
      };
      
      setDocuments(prev => [...prev, newDoc]);
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : 'Upload failed';
      setUploadProgress(`✗ ${message}`);
    } finally {
      setUploading(false);
    }
  }, []);

  const handleDelete = (docId: string) => {
    setDocuments(prev => prev.filter(doc => doc.id !== docId));
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'text/plain': ['.txt']
    },
    maxFiles: 1,
    disabled: uploading
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-slate-100">Documents</h1>
        <p className="text-slate-500 mt-1">Upload and manage your knowledge base documents</p>
      </div>

      {/* Upload Zone */}
      <Card className="border-slate-800 bg-[#0d1527]">
        <CardHeader>
          <CardTitle className="text-slate-200">Upload Document</CardTitle>
        </CardHeader>
        <CardContent>
          <div
            {...getRootProps()}
            className={`border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-all ${
              isDragActive
                ? 'border-teal-500 bg-teal-500/10'
                : 'border-slate-700 hover:border-slate-600'
            }`}
          >
            <input {...getInputProps()} />
            <Upload className="h-12 w-12 text-slate-400 mx-auto mb-4" />
            {isDragActive ? (
              <p className="text-teal-400 font-medium">Drop the file here...</p>
            ) : (
              <>
                <p className="text-slate-300 font-medium">
                  Drag & drop a PDF or TXT file here, or click to select
                </p>
                <p className="text-slate-500 text-sm mt-2">
                  Supported formats: PDF, TXT (Max 10MB)
                </p>
              </>
            )}
          </div>

          {uploadProgress && (
            <div className="mt-4 p-3 bg-slate-800 rounded-lg">
              <p className="text-sm text-slate-300">{uploadProgress}</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Documents List */}
      <Card className="border-slate-800 bg-[#0d1527]">
        <CardHeader>
          <CardTitle className="text-slate-200">Your Documents</CardTitle>
        </CardHeader>
        <CardContent>
          {documents.length === 0 ? (
            <div className="text-center py-12">
              <FileText className="h-12 w-12 text-slate-600 mx-auto mb-4" />
              <p className="text-slate-400">No documents uploaded yet</p>
              <p className="text-slate-500 text-sm mt-1">Upload a document to get started</p>
            </div>
          ) : (
            <div className="space-y-3">
              {documents.map((doc) => (
                <div
                  key={doc.id}
                  className="flex items-center justify-between p-4 bg-[#111b33] border border-slate-800 rounded-xl"
                >
                  <div className="flex items-center gap-4">
                    <div className="p-2 bg-teal-500/10 rounded-lg">
                      <FileText className="h-5 w-5 text-teal-400" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-slate-200">{doc.title}</p>
                      <p className="text-xs text-slate-500">
                        {doc.chunk_count} chunks • {new Date(doc.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <Badge
                      className={
                        doc.status === 'ingested'
                          ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                          : doc.status === 'processing'
                          ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                          : 'bg-red-500/10 text-red-400 border border-red-500/20'
                      }
                    >
                      {doc.status === 'ingested' && <CheckCircle className="h-3 w-3 mr-1" />}
                      {doc.status === 'error' && <AlertCircle className="h-3 w-3 mr-1" />}
                      {doc.status}
                    </Badge>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="text-slate-400 hover:text-red-400"
                      onClick={() => handleDelete(doc.id)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}