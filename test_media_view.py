#!/usr/bin/env python
"""
Quick test script to diagnose the media_list view error.
Run this on the server: python test_media_view.py
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erickvale.settings')
django.setup()

from django.test import RequestFactory
from activity_media.views import media_list
import traceback

print("Testing media_list view...")
print("=" * 50)

factory = RequestFactory()
request = factory.get('/apps/activity-media/')

try:
    response = media_list(request)
    print(f"✅ SUCCESS! Status code: {response.status_code}")
    print(f"Content length: {len(response.content)} bytes")
except Exception as e:
    print(f"❌ ERROR: {type(e).__name__}: {e}")
    print("\nFull traceback:")
    print("=" * 50)
    traceback.print_exc()
    print("=" * 50)
