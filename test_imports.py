#!/usr/bin/env python3
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'api'))

try:
    from utils.database import get_user_by_username, NFL_TEAMS
    print("✓ Database utils import: SUCCESS")
except ImportError as e:
    print("✗ Database utils import: FAILED -", e)

try:
    from utils.auth import hash_password, verify_token
    print("✓ Auth utils import: SUCCESS")
except ImportError as e:
    print("✗ Auth utils import: FAILED -", e)

try:
    from utils.storage import save_profile_picture
    print("✓ Storage utils import: SUCCESS")
except ImportError as e:
    print("✗ Storage utils import: FAILED -", e)

try:
    import asyncpg
    print("✓ asyncpg import: SUCCESS")
except ImportError as e:
    print("✗ asyncpg import: FAILED -", e)

try:
    from vercel_blob import put, delete
    print("✓ vercel-blob import: SUCCESS")
except ImportError as e:
    print("✗ vercel-blob import: FAILED -", e)

print("\nTesting NFL_TEAMS data:")
print(f"NFL_TEAMS length: {len(NFL_TEAMS)}")
print(f"First 3 teams: {NFL_TEAMS[:3]}")
