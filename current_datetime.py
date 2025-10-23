#!/usr/bin/env python3
"""
Script to print the current date and time
"""

from datetime import datetime

def main():
    # Get the current date and time
    now = datetime.now()
    
    # Print current date and time in different formats
    print("Current Date and Time Information:")
    print("=" * 40)
    print(f"Full date and time: {now}")
    print(f"Date (YYYY-MM-DD): {now.strftime('%Y-%m-%d')}")
    print(f"Time (HH:MM:SS): {now.strftime('%H:%M:%S')}")
    print(f"Formatted: {now.strftime('%A, %B %d, %Y at %I:%M %p')}")

if __name__ == "__main__":
    main()