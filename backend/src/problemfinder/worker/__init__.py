"""Worker layer: an APScheduler process shelling `pf ingest run` commands.

The cli and worker layers are siblings and never import each other; the
subprocess boundary between them is the layering contract at work.
"""
