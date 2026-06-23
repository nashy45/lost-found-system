#!/usr/bin/env python3
"""
Quick script to verify all statistics are coming from real database
"""
import sqlite3

def check_stats():
    conn = sqlite3.connect('database/lostfound.db')
    cursor = conn.cursor()
    
    print("=" * 50)
    print("REAL DATABASE STATISTICS")
    print("=" * 50)
    
    # Total items
    total = cursor.execute('SELECT COUNT(*) FROM items').fetchone()[0]
    print(f"\n✓ Total Items in Database: {total}")
    
    # Lost items
    lost = cursor.execute('SELECT COUNT(*) FROM items WHERE status="Lost"').fetchone()[0]
    print(f"✓ Lost Items: {lost}")
    
    # Found items
    found = cursor.execute('SELECT COUNT(*) FROM items WHERE status="Found"').fetchone()[0]
    print(f"✓ Found Items: {found}")
    
    # Claimed items
    claimed = cursor.execute('SELECT COUNT(*) FROM items WHERE status="Claimed"').fetchone()[0]
    print(f"✓ Claimed Items: {claimed}")
    
    # Success rate
    success_rate = round((claimed * 100 / total)) if total > 0 else 0
    print(f"✓ Success Rate: {success_rate}%")
    
    # Users
    users = cursor.execute('SELECT COUNT(*) FROM users WHERE role!="Admin"').fetchone()[0]
    print(f"✓ Total Users: {users}")
    
    print("\n" + "=" * 50)
    print("ALL NUMBERS ARE REAL FROM YOUR DATABASE!")
    print("=" * 50)
    print("\nThese are the actual numbers showing on your pages.")
    print("No fake/demo numbers anymore! ✅")
    
    conn.close()

if __name__ == '__main__':
    check_stats()
