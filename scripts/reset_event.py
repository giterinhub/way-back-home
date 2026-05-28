#!/usr/bin/env python3
"""
Way Back Home - Event Reset Script

This script completely resets an event code:
1. Deletes all participants belonging to the event in Firestore (which frees up usernames and removes them from the map).
2. Resets the event's participant_count to 0.
3. Clears all uploaded avatar and evidence assets in the Firebase Storage bucket for that event.

Prerequisites:
- Run 'gcloud auth login' and set the active project via 'gcloud config set project YOUR_PROJECT_ID'.
- Installed Google Cloud libraries: pip install google-cloud-firestore google-cloud-storage

Usage:
  python scripts/reset_event.py gdg
"""

import sys
import os
import json

# Ensure Google Cloud client libraries are installed
try:
    from google.cloud import firestore
    from google.cloud import storage
except ImportError:
    print("❌ Error: Missing Google Cloud client libraries.")
    print("   Please run: pip install google-cloud-firestore google-cloud-storage")
    sys.exit(1)


def get_project_id() -> str:
    """Detect Google Cloud project ID from config.json or environment."""
    # Check config.json first
    config_path = os.path.join(os.path.dirname(__file__), "..", "config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path) as f:
                return json.load(f).get("project_id", "")
        except Exception:
            pass

    # Check environment variable
    env_project = os.environ.get("GOOGLE_CLOUD_PROJECT")
    if env_project:
        return env_project

    # Try gcloud CLI fallback
    try:
        import subprocess
        result = subprocess.run(
            ["gcloud", "config", "get-value", "project"],
            capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except Exception:
        pass

    return ""


def main():
    if len(sys.argv) < 2:
        print("❌ Usage: python scripts/reset_event.py <event_code>")
        print("Example: python scripts/reset_event.py gdg")
        sys.exit(1)

    event_code = sys.argv[1].strip().lower()
    project_id = get_project_id()

    if not project_id:
        print("❌ Error: Could not detect your Google Cloud Project ID.")
        print("   Please run 'gcloud config set project YOUR_PROJECT_ID' or run from the project directory.")
        sys.exit(1)

    print("═══════════════════════════════════════════════════════════════")
    print(f"🛸 RESETTING EVENT: {event_code.upper()}")
    print(f"📍 GCP Project:    {project_id}")
    print("═══════════════════════════════════════════════════════════════")

    # Confirm action
    confirm = input(f"⚠️  Are you sure you want to delete all participants and files for event '{event_code}'? (y/N): ")
    if confirm.strip().lower() not in ("y", "yes"):
        print("Aborted.")
        sys.exit(0)

    print("\n🧹 Connecting to Firestore...")
    try:
        db = firestore.Client(project=project_id)
    except Exception as e:
        print(f"❌ Error connecting to Firestore: {e}")
        print("   Make sure you are logged in via 'gcloud auth login' and have permission.")
        sys.exit(1)

    # 1. Check if event exists
    event_ref = db.collection("events").document(event_code)
    event_snap = event_ref.get()
    if not event_snap.exists:
        print(f"⚠️  Warning: Event document '{event_code}' not found in Firestore.")
        create_now = input("Would you like to create this event first? (y/N): ")
        if create_now.strip().lower() in ("y", "yes"):
            event_name = input("Enter Event Name (e.g. Build with AI): ").strip()
            if not event_name:
                event_name = f"Event {event_code.upper()}"
            event_ref.set({
                "code": event_code,
                "name": event_name,
                "description": "Automatically created",
                "max_participants": 500,
                "participant_count": 0,
                "created_at": firestore.SERVER_TIMESTAMP,
                "active": True
            })
            print(f"✓ Event '{event_code}' created.")
        else:
            print("Reset aborted.")
            sys.exit(0)

    # 2. Delete all participants
    print("🗑️  Deleting participants...")
    participants_ref = db.collection("participants").where("event_code", "==", event_code)
    docs = participants_ref.stream()

    deleted_count = 0
    for doc in docs:
        print(f"  - Deleting participant: {doc.to_dict().get('username', doc.id)} ({doc.id})")
        doc.reference.delete()
        deleted_count += 1

    print(f"✓ Deleted {deleted_count} participants from Firestore database.")

    # 3. Reset participant count
    print("🔄 Resetting event participant counter to 0...")
    event_ref.update({"participant_count": 0})
    print("✓ Event counter reset.")

    # 4. Clear storage bucket objects
    bucket_name = f"{project_id}.firebasestorage.app"
    print(f"☁️  Clearing Firebase Storage assets for avatars and evidence (gs://{bucket_name})...")
    try:
        storage_client = storage.Client(project=project_id)
        bucket = storage_client.bucket(bucket_name)

        # Deleting avatars
        avatar_prefix = f"avatars/{event_code}/"
        avatar_blobs = list(bucket.list_blobs(prefix=avatar_prefix))
        if avatar_blobs:
            print(f"  - Wiping {len(avatar_blobs)} avatar files...")
            for blob in avatar_blobs:
                blob.delete()
            print("  ✓ Avatars cleared.")
        else:
            print("  - No avatar files to clear.")

        # Deleting evidence
        evidence_prefix = f"evidence/{event_code}/"
        evidence_blobs = list(bucket.list_blobs(prefix=evidence_prefix))
        if evidence_blobs:
            print(f"  - Wiping {len(evidence_blobs)} evidence files...")
            for blob in evidence_blobs:
                blob.delete()
            print("  ✓ Evidence files cleared.")
        else:
            print("  - No evidence files to clear.")

    except Exception as e:
        print(f"⚠️  Notice: Storage bucket clearing skipped or failed: {e}")
        print("   This might occur if Firebase Storage is not yet enabled or your bucket name is different.")

    print("\n🎉 RESET COMPLETE! All user names have been freed and the map is cleared! 🚀\n")


if __name__ == "__main__":
    main()
