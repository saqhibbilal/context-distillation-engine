import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { getSample, ingestPaste, ingestUpload, listSamples, processSession } from '../api/client';

const PASTE_PLACEHOLDER = `[2024-01-15 10:00] Alice: Hey team, let's decide on the deployment approach.
[2024-01-15 10:02] Bob: I vote for Docker.
[2024-01-15 10:05] Carol: +1 for Docker. Alice can you handle the CI pipeline?`;

function SampleLoader({ onLoad }: { onLoad: (text: string) => void }) {
  const { data } = useQuery({ queryKey: ['samples'], queryFn: listSamples });
  const samples = data?.samples ?? [];
  if (samples.length === 0) return null;
  return (
    <div className="flex flex-wrap gap-2 mb-6">
      <span className="text-zinc-500 text-sm self-center">Load sample:</span>
      {samples.map((name) => (
        <button
          key={name}
          onClick={async () => {
            const { text } = await getSample(name);
            onLoad(text);
          }}
          className="px-3 py-1.5 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-sm rounded transition-colors"
        >
          {name.replace(/_/g, ' ')}
        </button>
      ))}
    </div>
  );
}

export function Ingest() {
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [drag, setDrag] = useState(false);
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  async function handlePaste() {
    if (!text.trim()) {
      setError('Enter or paste chat text');
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const { session_id } = await ingestPaste(text.trim());
      await processSession(session_id);
      await queryClient.invalidateQueries({ queryKey: ['sessions'] });
      navigate(`/dashboard?session=${session_id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed');
    } finally {
      setLoading(false);
    }
  }

  async function handleFile(file: File) {
    if (!file.name.match(/\.(txt|json|csv)$/i)) {
      setError('Use .txt, .json, or .csv');
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const { session_id } = await ingestUpload(file);
      await processSession(session_id);
      await queryClient.invalidateQueries({ queryKey: ['sessions'] });
      navigate(`/dashboard?session=${session_id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="p-8 max-w-3xl">
      <h1 className="font-quantico text-2xl font-bold text-zinc-100 tracking-tight mb-1">
        Ingest Chat
      </h1>
      <p className="text-zinc-500 text-sm mb-8">
        Paste chat logs or upload a file. Supports Discord-style and generic formats.
      </p>

      <SampleLoader onLoad={(t) => setText(t)} />

      <div className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-zinc-400 mb-2">Paste text</label>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder={PASTE_PLACEHOLDER}
            rows={10}
            className="w-full px-4 py-3 bg-zinc-900/80 border border-zinc-700/60 rounded-lg text-zinc-200 placeholder-zinc-500 font-mono text-sm focus:outline-none focus:border-zinc-500 focus:ring-1 focus:ring-zinc-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-zinc-400 mb-2">Or upload file</label>
          <div
            onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
            onDragLeave={() => setDrag(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDrag(false);
              const f = e.dataTransfer.files[0];
              if (f) handleFile(f);
            }}
            className={`border-2 border-dashed rounded-lg p-10 text-center transition-colors ${
              drag ? 'border-zinc-500 bg-zinc-800/30' : 'border-zinc-700/60 bg-zinc-900/40'
            }`}
          >
            <p className="text-zinc-400 text-sm">Drop .txt, .json, or .csv here</p>
            <input
              type="file"
              accept=".txt,.json,.csv"
              onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFile(f); }}
              className="hidden"
              id="file-upload"
            />
            <label
              htmlFor="file-upload"
              className="mt-2 inline-block px-4 py-2 bg-zinc-700 hover:bg-zinc-600 text-zinc-200 text-sm font-medium rounded cursor-pointer transition-colors"
            >
              Choose file
            </label>
          </div>
        </div>

        {error && (
          <div className="px-4 py-3 bg-red-950/40 border border-red-800/60 rounded-lg text-red-300 text-sm">
            {error}
          </div>
        )}

        <button
          onClick={handlePaste}
          disabled={loading}
          className="w-full py-3 bg-zinc-100 text-zinc-900 font-bold rounded-lg hover:bg-white disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? 'Processing…' : 'Analyze & Extract Context'}
        </button>
      </div>

      {loading && (
        <div className="fixed inset-0 bg-black/70 flex flex-col items-center justify-center z-50">
          <div className="w-10 h-10 border-2 border-zinc-400 border-t-white rounded-full animate-spin" />
          <p className="mt-4 text-zinc-300 font-medium">Analyzing chat…</p>
          <p className="mt-1 text-zinc-500 text-sm">Extracting decisions, action items & context</p>
        </div>
      )}
    </div>
  );
}
