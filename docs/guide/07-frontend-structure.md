# Frontend Structure (Detailed)

The frontend is a **React 18** SPA with **TypeScript**, **Vite**, and **Tailwind CSS**. It talks to the backend via `/api` (proxied in dev by Vite, in Docker by nginx).

## Directory Layout

```
frontend/
├── src/
│   ├── main.tsx           # React root, strict mode
│   ├── App.tsx             # Layout: Toaster, sidebar (open/close), view (chat | documents), ChatInterface or DocumentsPage
│   ├── index.css           # Tailwind, Inter font, keyframes (skeleton, streaming-cursor)
│   ├── api/
│   │   └── client.ts       # listChats, getChat, createChat, deleteChat, listDocuments, uploadDocuments, getDocumentsStatus, streamChat (SSE)
│   ├── types/
│   │   └── index.ts        # ChatSession, ChatMessage, SourceRef, SSEMessageEvent, DocumentFile
│   └── components/
│       ├── ChatInterface.tsx   # Messages, streaming, sources (collapsible), ThinkingIndicator, InputBar
│       ├── Sidebar.tsx         # Documents (top), New Chat, session list, delete (trash), nav to Documents
│       ├── InputBar.tsx        # Textarea, send button
│       ├── EmptyState.tsx      # "Start a conversation"
│       ├── ThinkingIndicator.tsx  # Pulsing dot + status label
│       ├── SourceCard.tsx      # Filename, chunk index, expandable snippet
│       ├── DocumentsPage.tsx   # Folder status, DocumentList
│       └── DocumentList.tsx    # Grid of file cards (icon, name, size, chunks, status)
├── index.html
├── package.json
├── vite.config.ts          # Proxy /api → backend (timeout 5 min)
├── Dockerfile               # Build with Node, serve with nginx
└── nginx.conf               # /api → backend:8000, long timeouts
```

## Data Flow

- **App.tsx** holds `sessions`, `activeId`, `view` (chat | documents). It loads sessions on mount and when `loadSessions` is called (after new chat, delete, or title change). When `sessions` load and `activeId` is null, it auto-selects the first session.
- **ChatInterface** receives `sessionId` and `onSessionTitleChange`. On `sessionId` change it fetches messages with `getChat(sessionId)`. Send: append user message, call `streamChat` with callbacks (`onStatus`, `onToken`, `onSources`, `onDone`, `onError`); on done append assistant message with optional sources.
- **Sidebar** receives `sessions`, `activeId`, `onSelect`, `onNewChat`, `onSessionsChange`, `onNavigateToDocuments`, `currentView`. New Chat calls `createChat()` then `onSessionsChange()` and `onSelect(chat.id)`. Delete calls `deleteChat(id)`, then `onSessionsChange()` and optionally `onNewChat()` if the deleted chat was active; toasts success/error.
- **streamChat** in `api/client.ts`: POST body `{ session_id, content }`, reads response body as stream, parses SSE lines `data: {...}`, dispatches by `type` (status, token, sources, error, done). Sources payload is JSON array; error type triggers `onError`.

## Styling

- Dark theme: background `#0f0f11`, sidebar `#18181b`, cards `#1c1c21`, accent indigo, user bubble indigo, assistant bubble zinc-800.
- Tailwind utility classes; Framer Motion for list animations and collapsible sources.
- Responsive: sidebar collapses/hides on small screens; chat area max-width 768px centered.
