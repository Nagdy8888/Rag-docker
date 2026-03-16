# documents

Default folder for user-uploaded documents (PDF, DOCX, TXT, etc.).

- When running with Docker, this folder is **mounted** so the backend can read and store files.
- The **file watcher** (if enabled) can process new files dropped here.
- Uploads via the app API are also stored under this tree (or a configured path).

Do not commit large or sensitive files. Add patterns to `.gitignore` if needed.
