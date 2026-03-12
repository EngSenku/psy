#!/usr/bin/env python3
"""
TTS Diagnostic Tool
Run this script to diagnose edge-tts issues
"""

import asyncio
import edge_tts
import sys
import os

async def check_connection():
    """Check if we can connect to Microsoft TTS service."""
    print("=" * 70)
    print("1. CHECKING CONNECTION TO MICROSOFT TTS SERVICE")
    print("=" * 70)
    
    try:
        voices = await asyncio.wait_for(edge_tts.list_voices(), timeout=10.0)
        print(f"✓ Connection successful! Found {len(voices)} voices")
        return True
    except asyncio.TimeoutError:
        print("✗ Connection timeout - check your internet connection")
        return False
    except Exception as e:
        print(f"✗ Connection failed: {type(e).__name__}: {e}")
        return False

async def list_available_voices():
    """List all available voices."""
    print("\n" + "=" * 70)
    print("2. LISTING AVAILABLE VOICES")
    print("=" * 70)
    
    try:
        voices = await edge_tts.list_voices()
        
        # Filter English voices
        en_voices = [v for v in voices if v['Locale'].startswith('en')]
        
        print(f"\nFound {len(en_voices)} English voices:")
        print(f"{'Voice Name':<30} {'Gender':<10} {'Locale':<10}")
        print("-" * 70)
        
        for voice in en_voices[:10]:  # Show first 10
            print(f"{voice['ShortName']:<30} {voice['Gender']:<10} {voice['Locale']:<10}")
        
        if len(en_voices) > 10:
            print(f"... and {len(en_voices) - 10} more")
            
        return en_voices
    except Exception as e:
        print(f"✗ Failed to list voices: {e}")
        return []

async def test_simple_tts():
    """Test simple TTS generation."""
    print("\n" + "=" * 70)
    print("3. TESTING SIMPLE TTS GENERATION")
    print("=" * 70)
    
    test_text = "Hello, this is a test."
    voice = "en-US-AriaNeural"
    
    print(f"\nText: {test_text}")
    print(f"Voice: {voice}")
    
    try:
        communicate = edge_tts.Communicate(test_text, voice)
        
        output_file = "test_output.mp3"
        print(f"Saving to: {output_file}")
        
        await asyncio.wait_for(communicate.save(output_file), timeout=30.0)
        
        if os.path.exists(output_file):
            size = os.path.getsize(output_file)
            print(f"✓ Success! Generated file: {size} bytes")
            print(f"  You can play: {output_file}")
            return True
        else:
            print("✗ File was not created")
            return False
            
    except asyncio.TimeoutError:
        print("✗ Timeout during generation")
        return False
    except edge_tts.exceptions.NoAudioReceived as e:
        print(f"✗ NoAudioReceived error: {e}")
        print("\nPossible causes:")
        print("  - Voice name is invalid")
        print("  - Text contains unsupported characters")
        print("  - Service temporarily unavailable")
        return False
    except Exception as e:
        print(f"✗ Error: {type(e).__name__}: {e}")
        return False

async def test_long_text():
    """Test with longer text similar to your use case."""
    print("\n" + "=" * 70)
    print("4. TESTING WITH LONGER TEXT")
    print("=" * 70)
    
    long_text = """I hear you saying hi hi again, and I still sense that frustration. 
    It's completely understandable, and it's perfectly okay to feel that way. 
    We can just take a moment here."""
    
    voice = "en-US-AriaNeural"
    
    print(f"\nText length: {len(long_text)} characters")
    print(f"Voice: {voice}")
    
    try:
        communicate = edge_tts.Communicate(long_text, voice)
        output_file = "test_long_output.mp3"
        
        await asyncio.wait_for(communicate.save(output_file), timeout=30.0)
        
        if os.path.exists(output_file):
            size = os.path.getsize(output_file)
            print(f"✓ Success! Generated file: {size} bytes")
            return True
        else:
            print("✗ File was not created")
            return False
            
    except Exception as e:
        print(f"✗ Error: {type(e).__name__}: {e}")
        return False

async def main():
    """Run all diagnostic tests."""
    print("\n" + "="*70)
    print(" EDGE-TTS DIAGNOSTIC TOOL")
    print("="*70 + "\n")
    
    # Test 1: Connection
    connected = await check_connection()
    if not connected:
        print("\n⚠ Cannot proceed - no connection to TTS service")
        print("\nTroubleshooting steps:")
        print("  1. Check your internet connection")
        print("  2. Check if any firewall is blocking Python")
        print("  3. Try: ping speech.platform.bing.com")
        return
    
    # Test 2: List voices
    voices = await list_available_voices()
    if not voices:
        print("\n⚠ Cannot retrieve voice list")
        return
    
    # Test 3: Simple TTS
    simple_success = await test_simple_tts()
    
    # Test 4: Long text
    if simple_success:
        await test_long_text()
    
    print("\n" + "="*70)
    print(" DIAGNOSTIC COMPLETE")
    print("="*70)
    
    if simple_success:
        print("\n✓ edge-tts is working correctly!")
        print("\nYour issue might be related to:")
        print("  - asyncio event loop conflicts with eventlet/Flask-SocketIO")
        print("  - Text encoding issues in the advice string")
        print("  - Temporary network glitches")
    else:
        print("\n✗ edge-tts is not working")
        print("\nNext steps:")
        print("  1. Check your internet connection")
        print("  2. Try: pip install --upgrade edge-tts")
        print("  3. Try from a different network")
        print("  4. Check firewall settings")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nDiagnostic interrupted by user")
        sys.exit(0)