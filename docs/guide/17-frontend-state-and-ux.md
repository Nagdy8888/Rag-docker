# Frontend State and UX (Detailed)

This document describes how state and user experience are managed in the React app.

## App-Level State (App.tsx)

- **sessions** — List of chat sessions from GET /api/chats. Updated by loadSessions() (after new chat, delete, or onSessionTitleChange from ChatInterface).
- **activeId** — UUID of the selected chat, or null. When null and view is chat, ChatInterface shows "Select a chat or create a new one".
- **sidebarOpen** — Boolean for sidebar visibility (responsive: overlay on mobile, collapse on tablet).
- **view** — "chat" | "documents". Determines whether ChatInterface or DocumentsPage is rendered.

**Effects:**  
- loadSessions() on mount.  
- When sessions change: if activeId is not in sessions (e.g. deleted), set activeId to sessions[0] or null; if activeId is null and sessions.length > 0, set activeId to sessions[0].id (auto-select first chat).

**Callbacks passed to Sidebar:**  
- onSelect(id) → setActiveId(id), setView("chat"), setSidebarOpen(false).  
- onNewChat() → setActiveId(null).  
- onSessionsChange → loadSessions.  
- onNavigateToDocuments → setView("documents").

## ChatInterface State

- **messages** — List of ChatMessage for the current sessionId. Loaded by getChat(sessionId) when sessionId changes; cleared when sessionId is set (before fetch) and on error.
- **loading** — True while getChat is in progress.
- **streamingContent** — Accumulated token string for the current reply (cleared when send is pressed).
- **streamingStatus** — Current step label from SSE ("Analyzing question...", etc.); null when tokens are streaming.
- **streamingSources** — Sources array from the last stream (for the in-progress assistant message).
- **streamingSourcesRef** — Ref holding the same sources so onDone can read the latest value (React batching).
- **error** — Error message to show (e.g. from getChat or stream onError).
- **sourcesOpen** — Record<messageId, boolean> for which Sources sections are expanded.

**Send flow:** Append user message to state; clear streaming state and error; call streamChat with onStatus, onToken (append to streamingContent, clear status), onSources (update ref and state), onDone (append assistant message with content and sources from ref, clear streaming, call onSessionTitleChange), onError (clear streaming, set error).

**Display:** If sessionId is null, show empty state. Otherwise show loading skeletons, or empty state when not loading and no messages and no streaming; else show message list (with optional streaming bubble) and optional Sources (N) per assistant message. ThinkingIndicator shown when streamingStatus is set. Error banner when error is set.

## Sidebar UX

- **Documents** at top (sticky), then **New Chat**, then scrollable chat list.  
- New Chat: createChat() → onSessionsChange() → onSelect(chat.id). No onNewChat() after create (so the new chat stays selected).  
- Delete: single click on trash → deleteChat(id) → onSessionsChange(); if activeId === id, onNewChat(). Toast success or error. Button disabled while request in flight.  
- Clicking a session: onSelect(s.id). Active session highlighted (border + background).  
- Collapsed mode (if used): icon-only; Documents icon at bottom in collapsed layout.

## Documents Page

- DocumentsPage shows folder status and DocumentList.  
- DocumentList fetches GET /api/documents and displays cards (icon, filename, size, chunk count, status). Auto-refresh on an interval (e.g. 5s).  
- Upload (if present) uses POST /api/documents/upload and then refetches.

## Toasts

- react-hot-toast used for delete success/error.  
- Toaster configured in App (top-right, dark style).  
- Other operations (e.g. send error) can show inline error in ChatInterface instead of toast.
