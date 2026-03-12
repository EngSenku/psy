#!/usr/bin/env python3
"""
Test script to check available ElevenLabs voices
"""

import os
from elevenlabs.client import ElevenLabs

# Your API key
ELEVENLABS_API_KEY = ""

client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

print("=" * 70)
print("CHECKING ELEVENLABS ACCOUNT")
print("=" * 70)

try:
    # Get all voices
    voices = client.voices.get_all()
    
    print(f"\n✓ Found {len(voices.voices)} voices available:\n")
    
    for i, voice in enumerate(voices.voices, 1):
        print(f"{i}. Name: {voice.name}")
        print(f"   ID: {voice.voice_id}")
        print(f"   Category: {voice.category}")
        print(f"   Labels: {voice.labels}")
        print()
    
    # Test generation with first voice
    if voices.voices:
        print("=" * 70)
        print("TESTING SPEECH GENERATION")
        print("=" * 70)
        
        test_voice = voices.voices[0]
        print(f"\nTesting with voice: {test_voice.name}")
        
        audio = client.generate(
            text="Hello! This is a test of ElevenLabs text to speech.",
            voice=test_voice.voice_id,
            model="eleven_monolingual_v1"
        )
        
        # Save to file
        output_file = "test_elevenlabs.mp3"
        with open(output_file, "wb") as f:
            for chunk in audio:
                f.write(chunk)
        
        print(f"✓ Audio generated successfully: {output_file}")
        print(f"  File size: {os.path.getsize(output_file)} bytes")
        print("\nYou can play it with: mpv test_elevenlabs.mp3")
        
except Exception as e:
    print(f"\n✗ Error: {type(e).__name__}")
    print(f"  Message: {e}")
    print("\nPossible issues:")
    print("  1. API key is invalid or expired")
    print("  2. No credits remaining on account")
    print("  3. Network connection issue")