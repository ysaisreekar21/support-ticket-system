from databricks.sdk import WorkspaceClient

_client = None

def get_client():
    global _client
    if _client is None:
        _client = WorkspaceClient()
    return _client