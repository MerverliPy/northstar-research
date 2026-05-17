# Chat Import Bridge

Bridge-specific code belongs here.

Safe v1 behavior:

- Manual paste/import of selected transcripts
- Staged queue
- Markdown export packet
- Explicit promotion later
- No direct PostgreSQL or Neo4j mutation before promotion

Keep staging SQLite files and exports out of git.
