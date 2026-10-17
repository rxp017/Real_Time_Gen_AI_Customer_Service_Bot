const $ = id => document.getElementById(id);
const state = { session: null, config: null };
function show(target, value) { target.textContent = typeof value === 'string' ? value : JSON.stringify(value, null, 2); }
function ticketsView(value) {
  const rows = Array.isArray(value) ? value : [value];
  show($('tickets'), rows.length ? rows.map(ticket => `Ticket ${ticket.id}\nStatus: ${ticket.status}\nIssue: ${ticket.fields?.issue || ''}${ticket.question ? `\n${ticket.question}` : ''}`).join('\n\n') : 'No tickets yet.');
}
function uploadView(job) {
  const result = job.result;
  if (!result) { show($('upload-result'), `Document ${job.status}. We will check for the result here.`); return; }
  const fields = Object.entries(result.fields || {}).map(([name, field]) => `${name.replaceAll('_', ' ')}: ${field.value ?? 'not found'}`);
  const conflicts = (result.conflicts || []).map(item => `${item.field}: document ${item.document}; your message ${item.customer}`);
  show($('upload-result'), [result.message || result.status, ...fields, ...conflicts, result.vision?.description || ''].filter(Boolean).join('\n'));
}
async function request(path, data, method = 'POST') {
  const headers = {};
  const key = $('access-key').value.trim();
  if (key) headers['x-api-key'] = key;
  if (data && !(data instanceof FormData)) headers['content-type'] = 'application/json';
  const response = await fetch(path, { method, headers, credentials: 'omit', body: data ? (data instanceof FormData ? data : JSON.stringify(data)) : undefined });
  const result = await response.json();
  if (!response.ok) throw new Error(typeof result.detail === 'string' ? result.detail : `Request failed (${response.status})`);
  return result;
}
function bubble(text, role = 'assistant', metadata = '') {
  const element = document.createElement('div'); element.className = `bubble ${role}`; element.textContent = text;
  if ($('messages').querySelector('.empty')) $('messages').replaceChildren();
  $('messages').append(element);
  if (metadata) { const note = document.createElement('p'); note.className = 'meta'; note.textContent = metadata; $('messages').append(note); }
  $('messages').scrollTop = $('messages').scrollHeight;
}
async function busy(form, operation) {
  const button = form.querySelector('button[type=submit]'); button.disabled = true;
  try { await operation(); } finally { button.disabled = false; }
}
$('chat-form').addEventListener('submit', async event => {
  event.preventDefault();
  await busy(event.currentTarget, async () => {
    const question = $('question').value.trim(); if (!question) return;
    bubble(question, 'user'); $('question').value = '';
    try {
      const result = await request('/query', { question, session_id: state.session, unresolved: $('unresolved').checked });
      state.session = result.session_id;
      bubble(result.display_answer || result.answer, 'assistant', `Language: ${result.answer_language || result.language || 'unspecified'} · ${result.verified && result.citations?.length ? 'Source checked' : 'No cited factual answer'}`);
      if (result.citations?.length) bubble(result.citations.map(c => `${c.doc_id} · v${c.version} · ${c.section}`).join('\n'), 'source');
      if (result.source_answer && result.source_answer !== result.answer) {
        const details = document.createElement('details'); const summary = document.createElement('summary'); summary.textContent = 'Source answer';
        const source = document.createElement('p'); source.className = 'source'; source.textContent = result.source_answer; details.append(summary, source); $('messages').append(details);
      }
      show($('ticket-questions'), result.ticket_questions?.length ? result.ticket_questions.join('\n') : 'Session ready. Supply actual details below if you need a ticket.');
      if (result.tickets?.length) ticketsView(result.tickets);
    } catch (error) { bubble(error.message); }
  });
});
$('new-conversation').addEventListener('click', () => { state.session = null; $('messages').replaceChildren(); show($('ticket-questions'), 'Send a message to start a new session.'); });
$('upload-form').addEventListener('submit', async event => {
  event.preventDefault();
  await busy(event.currentTarget, async () => {
    try {
      if (!$('access-key').value.trim()) throw new Error('Enter your customer access key first.');
      const file = $('file').files[0]; if (!file) return;
      if (!state.config || file.size > state.config.max_upload_bytes || !state.config.upload_types.includes(file.type)) throw new Error('Choose a supported file within the upload size limit.');
      const data = new FormData(); data.append('file', file); data.append('customer_message', $('upload-message').value); data.append('purpose', $('purpose').value); data.append('language', $('language').value);
      show($('upload-result'), 'Checking file…');
      let result = await request('/uploads', data); uploadView(result);
      for (let attempt = 0; attempt < 120 && ['queued', 'running'].includes(result.status); attempt++) {
        await new Promise(resolve => setTimeout(resolve, 1500));
        result = await request(`/uploads/${encodeURIComponent(result.id)}`, null, 'GET'); uploadView(result);
      }
    } catch (error) { show($('upload-result'), error.message); }
  });
});
$('ticket-form').addEventListener('submit', async event => {
  event.preventDefault();
  await busy(event.currentTarget, async () => {
    try {
      if (!state.session) throw new Error('Send a chat message first.');
      if (!$('access-key').value.trim()) throw new Error('Enter your customer access key first.');
      const data = Object.fromEntries(new FormData($('ticket-form'))); const draft = data.draft_id.trim(); delete data.draft_id;
      const ticket = await request('/tickets', { session_id: state.session, fields: data, draft_id: draft || null });
      ticketsView(ticket); show($('ticket-questions'), ticket.question || 'Ticket recorded. Refresh to check its status.');
      if (ticket.status !== 'DRAFT') $('ticket-form').elements.draft_id.value = '';
    } catch (error) { show($('tickets'), error.message); }
  });
});
$('refresh-tickets').addEventListener('click', async () => { try { ticketsView(await request('/tickets', null, 'GET')); } catch (error) { show($('tickets'), error.message); } });
try {
  state.config = await request('/client-config', null, 'GET');
  for (const code of state.config.languages) { const option = document.createElement('option'); option.value = code; option.textContent = code; $('language').append(option); }
  const health = await request('/health', null, 'GET'); show($('health'), health.status === 'healthy' ? 'Service ready' : 'Service available · live provider not configured');
} catch (error) { show($('health'), error.message); }
