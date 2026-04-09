#!/usr/bin/env python3
"""Manual pipeline trigger for testing. Simulates a file upload and runs the full pipeline."""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


async def main():
    if len(sys.argv) < 3:
        print("Usage: python run_pipeline.py <user_id> <video_file_path>")
        print("Example: python run_pipeline.py 550e8400-e29b-41d4-a716-446655440000 /path/to/podcast.mp4")
        sys.exit(1)

    user_id = sys.argv[1]
    video_path = sys.argv[2]

    if not os.path.exists(video_path):
        print(f"File not found: {video_path}")
        sys.exit(1)

    print(f"Starting pipeline for user {user_id} with file {video_path}")

    from scout.tasks.ingest import _ingest_file
    from scout.db.session import async_session_factory

    async with async_session_factory() as db:
        await _ingest_file(db, user_id, video_path, os.path.basename(video_path))
        await db.commit()

    print("Ingest task submitted. Check Celery worker logs for pipeline progress.")


if __name__ == "__main__":
    asyncio.run(main())
