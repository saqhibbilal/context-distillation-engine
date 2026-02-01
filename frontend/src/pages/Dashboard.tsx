import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { chat, getSession, listSessions, processSession } from '../api/client';

type Tab = 'context' | 'decisions' | 'actions' | 'topics';

export function Dashboard() {
  const [searchParams, setSearchParams] = useSearchParams();
  const sessionParam = searchParams.get('session') || '';
  const [sessionId, setSessionId] = useState(sessionParam);
  const [tab, setTab] = useState<Tab>('context');
  const [assigneeFilter, setAssigneeFilter] = useState('');
  const [topicFilter, setTopicFilter] = useState('');
  const [chatInput, setChatInput] = useState('');
  const [chatHistory, setChatHistory] = useState<Array<{ q: string; a: string }>>([]);
  const queryClient = useQueryClient();

  const reprocessMutation = useMutation({
    mutationFn: (sid: string) => processSession(sid),
    onSuccess: (_, sid) => {
      queryClient.invalidateQueries({ queryKey: ['session', sid] });
    },
  });

  const chatMutation = useMutation({
    mutationFn: ({ sid, q }: { sid: string; q: string }) => chat(sid, q),
    onSuccess: (data, variables) => {
      setChatHistory((prev) => [...prev, { q: variables.q, a: data.answer }]);
      setChatInput('');
    },
    onError: (err, variables) => {
      setChatHistory((prev) => [...prev, { q: variables.q, a: `Error: ${err instanceof Error ? err.message : 'Failed'}` }]);
      setChatInput('');
    },
  });

  useEffect(() => {
    if (sessionParam) setSessionId(sessionParam);
  }, [sessionParam]);

  const { data: sessionsData } = useQuery({
    queryKey: ['sessions'],
    queryFn: listSessions,
  });

  const sessions = sessionsData?.sessions ?? [];
  const activeSession = sessionParam || sessionId || (sessions[0] ?? '');

  const { data: sessionData, isLoading, error } = useQuery({
    queryKey: ['session', activeSession],
    queryFn: () => getSession(activeSession),
    enabled: !!activeSession,
  });

  const handleSessionChange = (id: string) => {
    setSessionId(id);
    setSearchParams(id ? { session: id } : {});
  };

  if (!activeSession) {
    return (
      <div className="p-8">
        <h1 className="font-quantico text-2xl font-bold text-zinc-100 mb-4">Dashboard</h1>
        <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-12 text-center">
          <p className="text-zinc-400">No sessions yet.</p>
          <p className="text-zinc-500 text-sm mt-2">Ingest a chat to get started.</p>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="p-8 flex items-center justify-center min-h-[300px]">
        <p className="text-zinc-500">Loading…</p>
      </div>
    );
  }

  if (error || !sessionData) {
    return (
      <div className="p-8">
        <div className="rounded-lg border border-red-800/60 bg-red-950/20 p-4 text-red-300">
          Failed to load session. Try ingesting again.
        </div>
      </div>
    );
  }

  const processed = sessionData.processed as {
    summary?: string;
    clusters?: Array<{
      topic_id: number;
      topic_name: string;
      message_count: number;
      messages: Array<{ author: string; content: string; timestamp?: string }>;
    }>;
    extractions?: Array<{
      topic_id: number;
      topic_name: string;
      extraction: {
        decisions: Array<{ description: string; context?: string; participants?: string[] }>;
        action_items: Array<{ task: string; assignee?: string; due_context?: string }>;
        responsibilities: Array<{ person: string; responsibility: string }>;
        open_questions: Array<{ question: string; context?: string }>;
        critical_notes: Array<{ note: string; category?: string }>;
        summary?: string;
      };
    }>;
  } | undefined;

  const summary = processed?.summary ?? '';
  const clusters = processed?.clusters ?? [];
  const extractions = processed?.extractions ?? [];
  const allDecisions = extractions.flatMap((e) =>
    (e.extraction?.decisions ?? []).map((d) => ({ ...d, topic: e.topic_name }))
  );
  const allActions = extractions.flatMap((e) =>
    (e.extraction?.action_items ?? []).map((a) => ({ ...a, topic: e.topic_name }))
  );
  const allOpenQuestions = extractions.flatMap((e) =>
    (e.extraction?.open_questions ?? []).map((q) => ({ ...q, topic: e.topic_name }))
  );

  const topics = [...new Set([...allDecisions.map((d) => d.topic), ...allActions.map((a) => a.topic)])].filter(Boolean);
  const filteredDecisions = !topicFilter
    ? allDecisions
    : allDecisions.filter((d) => d.topic.toLowerCase().includes(topicFilter.toLowerCase()));
  const filteredActions = allActions
    .filter((a) => !topicFilter || (a.topic ?? '').toLowerCase().includes(topicFilter.toLowerCase()))
    .filter((a) => !assigneeFilter || (a.assignee ?? '').toLowerCase().includes(assigneeFilter.toLowerCase()));

  const tabs: { id: Tab; label: string }[] = [
    { id: 'context', label: 'Context' },
    { id: 'decisions', label: 'Decisions' },
    { id: 'actions', label: 'Action Items' },
    { id: 'topics', label: 'Topics' },
  ];

  return (
    <div className="p-8">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
        <h1 className="font-quantico text-2xl font-bold text-zinc-100 tracking-tight">
          Dashboard
        </h1>
        <div className="flex items-center gap-2">
          <button
            onClick={() => reprocessMutation.mutate(activeSession)}
            disabled={reprocessMutation.isPending}
            className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-sm font-medium rounded-lg disabled:opacity-50 transition-colors"
          >
            {reprocessMutation.isPending ? 'Reprocessing…' : 'Reprocess'}
          </button>
          <select
            value={activeSession}
            onChange={(e) => handleSessionChange(e.target.value)}
            className="px-4 py-2 bg-zinc-900 border border-zinc-700 rounded-lg text-zinc-200 text-sm font-medium focus:outline-none focus:border-zinc-500"
          >
            {([...new Set([activeSession, ...sessions])]).filter(Boolean).map((id) => (
              <option key={id} value={id}>
                {id.slice(0, 8)}…
              </option>
            ))}
          </select>
        </div>
      </div>

      {reprocessMutation.isPending && (
        <div className="fixed inset-0 bg-black/70 flex flex-col items-center justify-center z-50">
          <div className="w-10 h-10 border-2 border-zinc-400 border-t-white rounded-full animate-spin" />
          <p className="mt-4 text-zinc-300 font-medium">Reprocessing…</p>
          <p className="mt-1 text-zinc-500 text-sm">Extracting decisions & action items</p>
        </div>
      )}

      <div className="flex gap-2 border-b border-zinc-800 mb-6">
        {tabs.map(({ id, label }) => (
          <button
            key={id}
            onClick={() => setTab(id)}
            className={`px-4 py-2 text-sm font-medium transition-colors ${
              tab === id
                ? 'text-zinc-100 border-b-2 border-zinc-100 -mb-px'
                : 'text-zinc-500 hover:text-zinc-300'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {tab === 'context' && (
        <div className="space-y-6">
          {summary ? (
            <div className="rounded-lg border border-zinc-800 bg-zinc-900/40 p-5">
              <h3 className="text-sm font-medium text-zinc-400 mb-3">Summary</h3>
              <p className="text-zinc-200 leading-relaxed whitespace-pre-wrap">{summary}</p>
            </div>
          ) : null}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard label="Messages" value={sessionData.message_count ?? 0} />
            <StatCard label="Topics" value={clusters.length} />
            <StatCard label="Decisions" value={allDecisions.length} />
            <StatCard label="Action Items" value={allActions.length} />
          </div>

          <div className="rounded-lg border border-zinc-800 bg-zinc-900/40 p-4">
            <h3 className="text-sm font-medium text-zinc-400 mb-3">Ask about this chat</h3>
            <p className="text-zinc-500 text-sm mb-3">e.g. What is Alice responsible for? What was decided about deployment?</p>
            <div className="flex gap-2">
              <input
                type="text"
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && chatMutation.mutate({ sid: activeSession, q: chatInput })}
                placeholder="Type your question…"
                className="flex-1 px-4 py-2 bg-zinc-900 border border-zinc-700 rounded-lg text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-zinc-500"
              />
              <button
                onClick={() => chatMutation.mutate({ sid: activeSession, q: chatInput })}
                disabled={!chatInput.trim() || chatMutation.isPending}
                className="px-4 py-2 bg-zinc-700 hover:bg-zinc-600 text-zinc-200 rounded-lg disabled:opacity-50"
              >
                {chatMutation.isPending ? '…' : 'Ask'}
              </button>
            </div>
            {chatHistory.length > 0 && (
              <div className="mt-4 space-y-3">
                {chatHistory.map((h, i) => (
                  <div key={i} className="text-sm">
                    <p className="text-zinc-500">Q: {h.q}</p>
                    <p className="text-zinc-200 mt-1">{h.a}</p>
                  </div>
                ))}
              </div>
            )}
          </div>

          {allDecisions.length === 0 && allActions.length === 0 && allOpenQuestions.length === 0 && !summary ? (
            <div className="rounded-lg border border-zinc-800 bg-zinc-900/40 p-8 text-center">
              <p className="text-zinc-500">No context extracted yet.</p>
              <p className="text-zinc-600 text-sm mt-2">Click Reprocess to run AI extraction. Ensure MISTRAL_API_KEY is set.</p>
            </div>
          ) : (
            <div className="space-y-6">
              {allDecisions.length > 0 && (
                <section>
                  <h3 className="text-sm font-medium text-zinc-400 mb-3">Decisions</h3>
                  <div className="space-y-2">
                    {allDecisions.slice(0, 5).map((d, i) => (
                      <div key={i} className="rounded-lg border border-zinc-800 bg-zinc-900/40 px-4 py-3">
                        <p className="text-zinc-200">{d.description}</p>
                        <p className="text-zinc-500 text-sm mt-1">{d.topic}</p>
                      </div>
                    ))}
                  </div>
                </section>
              )}
              {allActions.length > 0 && (
                <section>
                  <h3 className="text-sm font-medium text-zinc-400 mb-3">Action Items</h3>
                  <div className="space-y-2">
                    {allActions.slice(0, 5).map((a, i) => (
                      <div key={i} className="rounded-lg border border-zinc-800 bg-zinc-900/40 px-4 py-3">
                        <p className="text-zinc-200">{a.task}</p>
                        <p className="text-zinc-500 text-sm mt-1">{a.assignee ? `→ ${a.assignee}` : ''} {a.topic}</p>
                      </div>
                    ))}
                  </div>
                </section>
              )}
              {allOpenQuestions.length > 0 && (
                <section>
                  <h3 className="text-sm font-medium text-zinc-400 mb-3">Open Questions</h3>
                  <div className="space-y-2">
                    {allOpenQuestions.slice(0, 3).map((q, i) => (
                      <div key={i} className="rounded-lg border border-zinc-800 bg-zinc-900/40 px-4 py-3">
                        <p className="text-zinc-200">{q.question}</p>
                        <p className="text-zinc-500 text-sm mt-1">{q.topic}</p>
                      </div>
                    ))}
                  </div>
                </section>
              )}
            </div>
          )}
        </div>
      )}

      {tab === 'topics' && (
        <div className="space-y-4">
          {clusters.map((c) => (
            <div
              key={c.topic_id}
              className="rounded-lg border border-zinc-800 bg-zinc-900/40 overflow-hidden"
            >
              <div className="px-4 py-3 border-b border-zinc-800 flex items-center justify-between">
                <span className="font-medium text-zinc-200">{c.topic_name}</span>
                <span className="text-zinc-500 text-sm">{c.message_count} messages</span>
              </div>
              <div className="p-4 space-y-2">
                {c.messages?.slice(0, 5).map((m: { author: string; content: string; timestamp?: string }, i: number) => (
                  <div key={i} className="text-sm">
                    <span className="text-zinc-500">{m.author}:</span>{' '}
                    <span className="text-zinc-300">{m.content}</span>
                  </div>
                ))}
                {(c.messages?.length ?? 0) > 5 && (
                  <p className="text-zinc-500 text-sm">+ {(c.messages?.length ?? 0) - 5} more</p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {tab === 'decisions' && (
        <div className="space-y-3">
          {allDecisions.length === 0 ? (
            <div className="rounded-lg border border-zinc-800 bg-zinc-900/40 p-6 text-center">
              <p className="text-zinc-500">No decisions extracted.</p>
              <p className="text-zinc-600 text-sm mt-2">Ensure MISTRAL_API_KEY is set in backend/.env for AI extraction.</p>
            </div>
          ) : (
            filteredDecisions.map((d, i) => (
              <div
                key={i}
                className="rounded-lg border border-zinc-800 bg-zinc-900/40 px-4 py-3"
              >
                <p className="text-zinc-200">{d.description}</p>
                <div className="flex gap-4 mt-2 text-zinc-500 text-sm">
                  <span>{d.topic}</span>
                  {d.participants?.length ? (
                    <span>{d.participants.join(', ')}</span>
                  ) : null}
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {tab === 'actions' && (
        <div className="space-y-4">
          <div className="flex flex-wrap gap-2 items-center">
            <input
              type="text"
              placeholder="Filter by assignee"
              value={assigneeFilter}
              onChange={(e) => setAssigneeFilter(e.target.value)}
              className="px-4 py-2 bg-zinc-900 border border-zinc-700 rounded-lg text-zinc-200 text-sm placeholder-zinc-500 focus:outline-none focus:border-zinc-500"
            />
            {topics.length > 0 && (
              <select
                value={topicFilter}
                onChange={(e) => setTopicFilter(e.target.value)}
                className="px-4 py-2 bg-zinc-900 border border-zinc-700 rounded-lg text-zinc-200 text-sm"
              >
                <option value="">All topics</option>
                {topics.map((t) => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            )}
          </div>
          <div className="space-y-3">
            {filteredActions.map((a, i) => (
                <div
                  key={i}
                  className="rounded-lg border border-zinc-800 bg-zinc-900/40 px-4 py-3"
                >
                  <p className="text-zinc-200">{a.task}</p>
                  <div className="flex gap-4 mt-2 text-zinc-500 text-sm">
                    {a.assignee && <span>→ {a.assignee}</span>}
                    <span>{a.topic}</span>
                    {a.due_context && <span>{a.due_context}</span>}
                  </div>
                </div>
              ))}
            {filteredActions.length === 0 && (
              <div className="rounded-lg border border-zinc-800 bg-zinc-900/40 p-6 text-center">
                <p className="text-zinc-500">No action items extracted.</p>
                <p className="text-zinc-600 text-sm mt-2">Ensure MISTRAL_API_KEY is set in backend/.env for AI extraction.</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-900/40 px-4 py-4">
      <p className="text-zinc-500 text-sm">{label}</p>
      <p className="font-quantico text-2xl font-bold text-zinc-100 mt-1">{value}</p>
    </div>
  );
}
