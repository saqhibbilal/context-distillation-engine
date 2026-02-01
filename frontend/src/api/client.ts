const API_BASE = '';

export async function listSamples(): Promise<{ samples: string[] }> {
  const res = await fetch(`${API_BASE}/api/samples`);
  if (!res.ok) return { samples: [] };
  return res.json();
}

export async function getSample(name: string): Promise<{ name: string; text: string }> {
  const res = await fetch(`${API_BASE}/api/samples/${name}`);
  if (!res.ok) throw new Error('Sample not found');
  return res.json();
}

export async function listSessions(): Promise<{ sessions: string[] }> {
  const res = await fetch(`${API_BASE}/api/sessions`);
  if (!res.ok) throw new Error('Failed to list sessions');
  return res.json();
}

export async function ingestPaste(text: string) {
  const res = await fetch(`${API_BASE}/api/ingest`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) throw new Error((await res.json()).detail || 'Ingest failed');
  return res.json();
}

export async function ingestUpload(file: File) {
  const form = new FormData();
  form.append('file', file);
  const res = await fetch(`${API_BASE}/api/ingest/upload`, {
    method: 'POST',
    body: form,
  });
  if (!res.ok) throw new Error((await res.json()).detail || 'Upload failed');
  return res.json();
}

export async function processSession(sessionId: string) {
  const res = await fetch(`${API_BASE}/api/process/${sessionId}`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error((await res.json()).detail || 'Process failed');
  return res.json();
}

export async function getSession(sessionId: string) {
  const res = await fetch(`${API_BASE}/api/sessions/${sessionId}`);
  if (!res.ok) throw new Error('Session not found');
  return res.json();
}

export async function getDecisions(sessionId: string) {
  const res = await fetch(`${API_BASE}/api/sessions/${sessionId}/decisions`);
  if (!res.ok) throw new Error('Failed to fetch decisions');
  return res.json();
}

export async function chat(sessionId: string, question: string): Promise<{ answer: string }> {
  const res = await fetch(`${API_BASE}/api/sessions/${sessionId}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  });
  if (!res.ok) throw new Error((await res.json()).detail || 'Chat failed');
  return res.json();
}

export async function getActionItems(sessionId: string, assignee?: string) {
  const url = assignee
    ? `${API_BASE}/api/sessions/${sessionId}/action-items?assignee=${encodeURIComponent(assignee)}`
    : `${API_BASE}/api/sessions/${sessionId}/action-items`;
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to fetch action items');
  return res.json();
}
