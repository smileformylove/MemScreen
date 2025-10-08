import logging
import os
import platform
import sys
import json
import uuid

from posthog import Posthog

# import memscreen
# from memscreen.memory.setup import get_or_create_user_id

# Set up the directory path
VECTOR_ID = str(uuid.uuid4())
home_dir = os.path.expanduser("~")
memscreen_dir = os.environ.get("memscreen_DIR") or os.path.join(home_dir, ".memscreen")
os.makedirs(memscreen_dir, exist_ok=True)

def get_user_id():
    config_path = os.path.join(memscreen_dir, "config.json")
    if not os.path.exists(config_path):
        return "anonymous_user"

    try:
        with open(config_path, "r") as config_file:
            config = json.load(config_file)
            user_id = config.get("user_id")
            return user_id
    except Exception:
        return "anonymous_user"


def get_or_create_user_id(vector_store):
    """Store user_id in vector store and return it."""
    user_id = get_user_id()

    # Try to get existing user_id from vector store
    try:
        existing = vector_store.get(vector_id=user_id)
        if existing and hasattr(existing, "payload") and existing.payload and "user_id" in existing.payload:
            return existing.payload["user_id"]
    except Exception:
        pass

    # If we get here, we need to insert the user_id
    try:
        dims = getattr(vector_store, "embedding_model_dims", 1536)
        vector_store.insert(
            vectors=[[0.1] * dims], payloads=[{"user_id": user_id, "type": "user_identity"}], ids=[user_id]
        )
    except Exception:
        pass

    return user_id


memscreen_TELEMETRY = os.environ.get("memscreen_TELEMETRY", "True")
PROJECT_API_KEY = "phc_hgJkUVJFYtmaJqrvf6CYN67TIQ8yhXAkWzUn9AMU4yX"
HOST = "https://us.i.posthog.com"

if isinstance(memscreen_TELEMETRY, str):
    memscreen_TELEMETRY = memscreen_TELEMETRY.lower() in ("true", "1", "yes")

if not isinstance(memscreen_TELEMETRY, bool):
    raise ValueError("memscreen_TELEMETRY must be a boolean value.")

logging.getLogger("posthog").setLevel(logging.CRITICAL + 1)
logging.getLogger("urllib3").setLevel(logging.CRITICAL + 1)


class AnonymousTelemetry:
    def __init__(self, vector_store=None):
        self.posthog = Posthog(project_api_key=PROJECT_API_KEY, host=HOST)

        self.user_id = get_or_create_user_id(vector_store)

        if not memscreen_TELEMETRY:
            self.posthog.disabled = True

    def capture_event(self, event_name, properties=None, user_email=None):
        if properties is None:
            properties = {}
        properties = {
            "client_source": "python",
            # "client_version": memscreen.__version__,
            "client_version": "local_memscreen",
            "python_version": sys.version,
            "os": sys.platform,
            "os_version": platform.version(),
            "os_release": platform.release(),
            "processor": platform.processor(),
            "machine": platform.machine(),
            **properties,
        }
        distinct_id = self.user_id if user_email is None else user_email
        self.posthog.capture(distinct_id=distinct_id, event=event_name, properties=properties)

    def close(self):
        self.posthog.shutdown()


client_telemetry = AnonymousTelemetry()


def capture_event(event_name, memory_instance, additional_data=None):
    oss_telemetry = AnonymousTelemetry(
        vector_store=memory_instance._telemetry_vector_store
        if hasattr(memory_instance, "_telemetry_vector_store")
        else None,
    )

    event_data = {
        "collection": memory_instance.collection_name,
        "vector_size": memory_instance.embedding_model.config.embedding_dims,
        "history_store": "sqlite",
        # "graph_store": f"{memory_instance.graph.__class__.__module__}.{memory_instance.graph.__class__.__name__}"
        # if memory_instance.config.graph_store.config
        # else None,
        "vector_store": f"{memory_instance.vector_store.__class__.__module__}.{memory_instance.vector_store.__class__.__name__}",
        "llm": f"{memory_instance.llm.__class__.__module__}.{memory_instance.llm.__class__.__name__}",
        "embedding_model": f"{memory_instance.embedding_model.__class__.__module__}.{memory_instance.embedding_model.__class__.__name__}",
        "function": f"{memory_instance.__class__.__module__}.{memory_instance.__class__.__name__}.{memory_instance.api_version}",
    }
    if additional_data:
        event_data.update(additional_data)

    oss_telemetry.capture_event(event_name, event_data)


def capture_client_event(event_name, instance, additional_data=None):
    event_data = {
        "function": f"{instance.__class__.__module__}.{instance.__class__.__name__}",
    }
    if additional_data:
        event_data.update(additional_data)

    client_telemetry.capture_event(event_name, event_data, instance.user_email)
