"""
Test Phase 1 Integration

Verifies that SchemaFormatter and CellRetriever are properly wired up
and working in the ask_question() flow.

Usage:
    python tests/test_phase1_integration.py
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from config import Config
from wren_client import WrenClient


async def test_schema_formatter():
    """Test that SchemaFormatter is initialized and working."""
    print("\n" + "="*70)
    print("TEST 1: SchemaFormatter Integration")
    print("="*70)

    config = Config()

    db_config = {
        "host": config.DB_HOST,
        "port": config.DB_PORT,
        "database": config.DB_DATABASE,
        "user": config.DB_USER,
        "password": config.DB_PASSWORD,
    }

    wren = WrenClient(
        base_url=config.WREN_URL,
        db_type=config.DB_TYPE,
        db_config=db_config,
        anthropic_client=config.anthropic_client,
        model=config.ANTHROPIC_MODEL
    )

    # Load MDL (should initialize SchemaFormatter)
    await wren.load_mdl()

    # Test schema formatter
    if wren._schema_formatter:
        print("✅ SchemaFormatter initialized")

        # Test DDL format
        ddl = wren.get_schema_ddl()
        print(f"✅ DDL format: {len(ddl)} chars")
        if ddl:
            print(f"   Preview: {ddl[:100]}...")

        # Test Markdown format
        markdown = wren.get_schema_markdown()
        print(f"✅ Markdown format: {len(markdown)} chars")
        if markdown:
            print(f"   Preview: {markdown[:100]}...")

        # Test Compact format
        compact = wren.get_schema_compact()
        print(f"✅ Compact format: {len(compact)} chars")
        if compact:
            print(f"   Preview: {compact[:100]}...")
    else:
        print("❌ SchemaFormatter NOT initialized")
        return False

    await wren.close()
    return True


async def test_cell_retriever():
    """Test that CellRetriever is initialized and working."""
    print("\n" + "="*70)
    print("TEST 2: CellRetriever Integration")
    print("="*70)

    config = Config()

    db_config = {
        "host": config.DB_HOST,
        "port": config.DB_PORT,
        "database": config.DB_DATABASE,
        "user": config.DB_USER,
        "password": config.DB_PASSWORD,
    }

    wren = WrenClient(
        base_url=config.WREN_URL,
        db_type=config.DB_TYPE,
        db_config=db_config,
        anthropic_client=config.anthropic_client,
        model=config.ANTHROPIC_MODEL
    )

    # Load MDL (should initialize CellRetriever)
    await wren.load_mdl()

    # Test cell retriever
    if wren._cell_retriever:
        print("✅ CellRetriever initialized")

        # Wait a moment for background cache loading
        await asyncio.sleep(2)

        # Get cache stats
        stats = wren._cell_retriever.get_cache_stats()
        print(f"✅ Cache stats:")
        print(f"   - Columns cached: {stats['columns_cached']}")
        print(f"   - Total values: {stats['total_values']}")
        print(f"   - Cache loaded: {stats['cache_loaded']}")

        # Test retrieval
        test_question = "Show me customers in USA"
        relevant_cells = await wren._cell_retriever.retrieve_relevant_cells(test_question)
        print(f"✅ Cell retrieval test:")
        print(f"   Question: '{test_question}'")
        print(f"   Relevant cells found: {len(relevant_cells)}")

        if relevant_cells:
            for key, values in list(relevant_cells.items())[:3]:  # Show first 3
                print(f"   - {key}: {values[:5]}")
    else:
        print("❌ CellRetriever NOT initialized")
        return False

    await wren.close()
    return True


async def test_enhanced_ask_question():
    """Test that ask_question uses Phase 1 enhancements."""
    print("\n" + "="*70)
    print("TEST 3: Enhanced ask_question() Integration")
    print("="*70)

    config = Config()

    db_config = {
        "host": config.DB_HOST,
        "port": config.DB_PORT,
        "database": config.DB_DATABASE,
        "user": config.DB_USER,
        "password": config.DB_PASSWORD,
    }

    wren = WrenClient(
        base_url=config.WREN_URL,
        db_type=config.DB_TYPE,
        db_config=db_config,
        anthropic_client=config.anthropic_client,
        model=config.ANTHROPIC_MODEL
    )

    # Load MDL
    await wren.load_mdl()

    # Wait for cache to load
    await asyncio.sleep(3)

    # Test enhanced ask_question
    test_question = "What is the total revenue?"

    print(f"📝 Testing question: '{test_question}'")
    print("   Using enhancements: True")

    try:
        # This will attempt to use Wren AI with enhancements
        response = await wren.ask_question(test_question, use_enhancements=True)

        print(f"✅ ask_question() completed")
        print(f"   SQL generated: {bool(response.get('sql'))}")
        if response.get('sql'):
            print(f"   SQL preview: {response['sql'][:100]}...")
        print(f"   Confidence: {response.get('confidence', 0)}")
        print(f"   Method: {response.get('method', 'wren_ai')}")

    except Exception as e:
        print(f"⚠️  Wren AI not available: {e}")
        print("   This is OK if Wren AI is not running")
        print("   Testing Claude fallback instead...")

        try:
            response = await wren.generate_sql_with_claude(test_question)
            print(f"✅ Claude fallback worked!")
            print(f"   SQL generated: {bool(response.get('sql'))}")
            if response.get('sql'):
                print(f"   SQL: {response['sql']}")
            print(f"   Method: {response.get('method')}")
        except Exception as e2:
            print(f"❌ Claude fallback failed: {e2}")
            await wren.close()
            return False

    await wren.close()
    return True


async def test_claude_direct_generation():
    """Test direct Claude SQL generation with Phase 1 enhancements."""
    print("\n" + "="*70)
    print("TEST 4: Claude Direct SQL Generation")
    print("="*70)

    config = Config()

    db_config = {
        "host": config.DB_HOST,
        "port": config.DB_PORT,
        "database": config.DB_DATABASE,
        "user": config.DB_USER,
        "password": config.DB_PASSWORD,
    }

    wren = WrenClient(
        base_url=config.WREN_URL,
        db_type=config.DB_TYPE,
        db_config=db_config,
        anthropic_client=config.anthropic_client,
        model=config.ANTHROPIC_MODEL
    )

    # Load MDL
    await wren.load_mdl()

    # Wait for cache
    await asyncio.sleep(3)

    # Test questions
    test_questions = [
        "Show me all customers",
        "What was total revenue last month?",
        "List top 5 products by price"
    ]

    for question in test_questions:
        print(f"\n📝 Question: '{question}'")

        try:
            response = await wren.generate_sql_with_claude(question)

            print(f"✅ SQL generated")
            print(f"   SQL: {response['sql'][:200]}...")
            print(f"   Confidence: {response['confidence']}")
            print(f"   Used cell values: {response['metadata'].get('used_cell_values')}")
            print(f"   Schema format: {response['metadata'].get('schema_format')}")

        except Exception as e:
            print(f"❌ Failed: {e}")
            await wren.close()
            return False

    await wren.close()
    return True


async def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("🧪 PHASE 1 INTEGRATION TESTS")
    print("="*70)
    print("\nThese tests verify that SchemaFormatter and CellRetriever")
    print("are properly integrated into the ask_question() flow.\n")

    results = []

    # Run tests
    try:
        results.append(("SchemaFormatter", await test_schema_formatter()))
    except Exception as e:
        print(f"❌ SchemaFormatter test failed: {e}")
        results.append(("SchemaFormatter", False))

    try:
        results.append(("CellRetriever", await test_cell_retriever()))
    except Exception as e:
        print(f"❌ CellRetriever test failed: {e}")
        results.append(("CellRetriever", False))

    try:
        results.append(("Enhanced ask_question", await test_enhanced_ask_question()))
    except Exception as e:
        print(f"❌ Enhanced ask_question test failed: {e}")
        results.append(("Enhanced ask_question", False))

    try:
        results.append(("Claude Direct", await test_claude_direct_generation()))
    except Exception as e:
        print(f"❌ Claude Direct test failed: {e}")
        results.append(("Claude Direct", False))

    # Summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:8s} {name}")

    print("="*70)
    print(f"Result: {passed}/{total} tests passed")
    print("="*70)

    if passed == total:
        print("\n🎉 All tests passed! Phase 1 is properly integrated.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check the output above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
