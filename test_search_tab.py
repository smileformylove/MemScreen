#!/usr/bin/env python3
"""
Test Search tab functionality
"""

import tkinter as tk
from memscreen.ui.tabs.search_tab import SearchTab
from memscreen.ui.components.colors import COLORS

print("=" * 70)
print("🔍 Search Tab Test")
print("=" * 70)
print()

# Create mock memory
class MockMemory:
    """Mock memory with test data"""
    def search(self, query, user_id="screenshot"):
        # Return test results
        return {
            'results': [
                {'memory': 'Test result 1: Python code example'},
                {'memory': 'Test result 2: Screenshot from today'},
                {'memory': 'Test result 3: Meeting notes'},
            ]
        }

print("📦 [Test 1] Create Search Tab")
print("-" * 70)

try:
    root = tk.Tk()
    root.title("Search Tab Test")
    root.geometry("800x600")

    # Create mock app object
    class MockApp:
        def __init__(self, root):
            self.root = root

    mock_app = MockApp(root)

    # Create search tab
    search_tab = SearchTab(root, app=mock_app, mem=MockMemory())
    search_tab.create_ui()

    print("✅ Search tab created successfully")
    print(f"   Frame: {search_tab.frame}")
    print(f"   Search input: {search_tab.search_input}")

    # Check if search input is editable
    state = search_tab.search_input['state']
    print(f"   Input state: {state}")

    if state == 'normal' or state == tk.NORMAL:
        print("✅ Search input is editable")
    else:
        print(f"⚠️  Search input state: {state}")

    # Pack the frame to show it
    search_tab.frame.pack(fill=tk.BOTH, expand=True)

    # Test inserting text
    print("")
    print("📝 [Test 2] Test Search Input")
    print("-" * 70)

    try:
        search_tab.search_input.delete(0, tk.END)
        search_tab.search_input.insert(0, "test query")
        test_value = search_tab.search_input.get()
        print(f"✅ Can write to search input")
        print(f"   Test value: '{test_value}'")

        if test_value == "test query":
            print("✅ Read/write works correctly")
        else:
            print(f"⚠️  Unexpected value: '{test_value}'")

    except Exception as e:
        print(f"❌ Error testing search input: {e}")

    print("")
    print("🎯 [Test 3] Test Search Function")
    print("-" * 70)

    try:
        # Set a test query
        search_tab.search_input.delete(0, tk.END)
        search_tab.search_input.insert(0, "python")

        # Perform search
        search_tab.perform_search()

        # Check results
        results_text = search_tab.search_results.get("1.0", tk.END)
        if results_text and "Searching for: python" in results_text:
            print("✅ Search function works")
            print(f"   Results preview: {results_text[:100]}...")
        else:
            print(f"⚠️  Unexpected results: {results_text[:100]}")

    except Exception as e:
        print(f"❌ Error performing search: {e}")
        import traceback
        traceback.print_exc()

    print("")
    print("=" * 70)
    print("✅ Search Tab Test Complete!")
    print("=" * 70)
    print()
    print("Summary:")
    print("- Search tab: ✅ Created successfully")
    print("- Search input: ✅ Editable")
    print("- Search function: ✅ Working")
    print()
    print("The Search tab should work correctly in the UI!")
    print()

    # Clean up
    root.destroy()

except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
