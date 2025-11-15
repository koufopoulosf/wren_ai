"""
Evaluation Framework for Text-to-SQL Performance

This script evaluates the Wren AI assistant's ability to:
1. Generate valid SQL from natural language questions
2. Execute queries successfully
3. Return correct results

Usage:
    python tests/evaluate.py
    python tests/evaluate.py --parallel-scaling --candidates 5
    python tests/evaluate.py --verbose
"""

import asyncio
import json
import logging
import argparse
from datetime import datetime
from typing import List, Dict, Any
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from config import Config
from wren_client import WrenClient
from validator import SQLValidator

# Set up logging for evaluation
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Evaluator:
    """Evaluate Text-to-SQL performance."""

    def __init__(self, config: Config, verbose: bool = False):
        """
        Initialize evaluator.

        Args:
            config: Application configuration
            verbose: Enable verbose logging
        """
        self.config = config
        self.verbose = verbose
        self.wren = None
        self.validator = None

        if verbose:
            logging.getLogger().setLevel(logging.DEBUG)

    async def initialize(self):
        """Initialize clients."""
        logger.info("🚀 Initializing evaluation environment...")

        # Database config
        db_config = {
            "host": self.config.DB_HOST,
            "port": self.config.DB_PORT,
            "database": self.config.DB_DATABASE,
            "user": self.config.DB_USER,
            "password": self.config.DB_PASSWORD,
        }

        # Initialize Wren client
        self.wren = WrenClient(
            base_url=self.config.WREN_URL,
            db_type=self.config.DB_TYPE,
            db_config=db_config,
            anthropic_client=self.config.anthropic_client,
            model=self.config.ANTHROPIC_MODEL
        )

        # Load MDL
        logger.info("📚 Loading MDL schema...")
        await self.wren.load_mdl()

        # Initialize validator
        self.validator = SQLValidator(
            mdl_models=self.wren._mdl_models,
            mdl_metrics=self.wren._mdl_metrics
        )

        logger.info("✅ Evaluation environment ready")

    async def evaluate_query(self, test_case: Dict) -> Dict[str, Any]:
        """
        Evaluate a single query.

        Args:
            test_case: Test case dictionary

        Returns:
            Evaluation results
        """
        question = test_case['question']
        test_id = test_case['id']

        result = {
            'id': test_id,
            'question': question,
            'difficulty': test_case.get('difficulty', 'unknown'),
            'success': False,
            'sql_generated': False,
            'sql_valid': False,
            'sql_executable': False,
            'has_results': False,
            'correct_tables': None,
            'error': None,
            'sql': None,
            'execution_time': 0,
            'row_count': 0
        }

        try:
            start_time = datetime.now()

            # Step 1: Generate SQL
            if self.verbose:
                logger.debug(f"Generating SQL for: {question}")

            response = await self.wren.ask_question(question)
            sql = response.get('sql', '')

            result['sql'] = sql
            result['sql_generated'] = bool(sql)

            if not sql:
                result['error'] = "No SQL generated"
                if self.verbose:
                    logger.warning(f"[{test_id}] No SQL generated")
                return result

            # Step 2: Validate SQL
            if self.verbose:
                logger.debug(f"Validating SQL: {sql[:100]}...")

            is_valid, error = self.validator.validate(sql)
            result['sql_valid'] = is_valid

            if not is_valid:
                result['error'] = f"Validation failed: {error}"
                if self.verbose:
                    logger.warning(f"[{test_id}] Validation failed: {error}")
                return result

            # Step 3: Execute SQL
            if self.verbose:
                logger.debug(f"Executing SQL...")

            try:
                results = await self.wren.execute_sql(sql)
                result['sql_executable'] = True
                result['has_results'] = len(results) > 0
                result['row_count'] = len(results)

                if self.verbose:
                    logger.debug(f"[{test_id}] Execution successful: {len(results)} rows")

            except Exception as e:
                result['error'] = f"Execution failed: {str(e)}"
                if self.verbose:
                    logger.warning(f"[{test_id}] Execution failed: {e}")
                return result

            # Step 4: Check if correct tables used (if specified)
            expected_tables = test_case.get('expected_tables', [])
            if expected_tables:
                used_tables = set(self._extract_table_names(sql))
                expected_set = set(expected_tables)
                result['correct_tables'] = expected_set.issubset(used_tables)

                if self.verbose and not result['correct_tables']:
                    logger.debug(f"[{test_id}] Expected tables {expected_set}, got {used_tables}")

            # Success!
            result['success'] = (
                result['sql_generated'] and
                result['sql_valid'] and
                result['sql_executable']
            )

            # Calculate execution time
            end_time = datetime.now()
            result['execution_time'] = (end_time - start_time).total_seconds()

        except Exception as e:
            result['error'] = str(e)
            logger.error(f"❌ [{test_id}] Error evaluating query: {e}", exc_info=self.verbose)

        return result

    def _extract_table_names(self, sql: str) -> List[str]:
        """Extract table names from SQL."""
        # Simple regex-based extraction
        import re

        # Match FROM and JOIN clauses
        pattern = r'\b(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*)'
        matches = re.findall(pattern, sql, re.IGNORECASE)

        return list(set(matches))

    async def evaluate_all(self, test_cases: List[Dict]) -> Dict[str, Any]:
        """
        Evaluate all test cases.

        Args:
            test_cases: List of test case dictionaries

        Returns:
            Aggregate metrics and results
        """
        results = []
        total = len(test_cases)

        logger.info(f"\n{'='*70}")
        logger.info(f"📊 Evaluating {total} test cases...")
        logger.info(f"{'='*70}\n")

        for i, test_case in enumerate(test_cases, 1):
            logger.info(f"[{i}/{total}] Evaluating: {test_case['question'][:60]}...")
            result = await self.evaluate_query(test_case)
            results.append(result)

            # Print immediate feedback
            status = "✅" if result['success'] else "❌"
            print(f"{status} [{result['id']}] {test_case['question'][:60]}...")

            if not result['success'] and result['error']:
                print(f"     Error: {result['error'][:80]}")

        # Calculate metrics
        total = len(results)
        success = sum(1 for r in results if r['success'])
        sql_generated = sum(1 for r in results if r['sql_generated'])
        sql_valid = sum(1 for r in results if r['sql_valid'])
        sql_executable = sum(1 for r in results if r['sql_executable'])

        metrics = {
            'total_queries': total,
            'successful': success,
            'success_rate': success / total if total > 0 else 0,
            'sql_generation_rate': sql_generated / total if total > 0 else 0,
            'validation_rate': sql_valid / sql_generated if sql_generated > 0 else 0,
            'execution_rate': sql_executable / sql_valid if sql_valid > 0 else 0,
            'avg_execution_time': sum(r['execution_time'] for r in results) / total if total > 0 else 0,
            'results': results,
            'timestamp': datetime.now().isoformat()
        }

        return metrics

    def print_report(self, metrics: Dict, test_cases: List[Dict]):
        """Print evaluation report."""
        print("\n" + "="*70)
        print("📊 EVALUATION REPORT")
        print("="*70)
        print(f"Total Queries:        {metrics['total_queries']}")
        print(f"Successful:           {metrics['successful']} ({metrics['success_rate']*100:.1f}%)")
        print(f"SQL Generated:        {int(metrics['total_queries'] * metrics['sql_generation_rate'])} ({metrics['sql_generation_rate']*100:.1f}%)")
        print(f"SQL Valid:            ({metrics['validation_rate']*100:.1f}%)")
        print(f"SQL Executable:       ({metrics['execution_rate']*100:.1f}%)")
        print(f"Avg Execution Time:   {metrics['avg_execution_time']:.2f}s")
        print("="*70)

        # By difficulty
        results = metrics['results']
        difficulties = {}
        for r in results:
            diff = r.get('difficulty', 'unknown')

            if diff not in difficulties:
                difficulties[diff] = {'total': 0, 'success': 0}

            difficulties[diff]['total'] += 1
            if r['success']:
                difficulties[diff]['success'] += 1

        if difficulties:
            print("\n📈 Performance by Difficulty:")
            for diff, stats in sorted(difficulties.items()):
                rate = stats['success'] / stats['total'] * 100 if stats['total'] > 0 else 0
                print(f"  {diff.capitalize():10s}: {stats['success']}/{stats['total']} ({rate:.1f}%)")

        # Failures
        failures = [r for r in results if not r['success']]
        if failures:
            print(f"\n❌ Failed Queries ({len(failures)}):")
            for r in failures:
                print(f"  [{r['id']}] {r['question'][:60]}...")
                if r['error']:
                    error_preview = r['error'][:100]
                    print(f"       Error: {error_preview}")

        print("="*70 + "\n")

    async def close(self):
        """Cleanup."""
        if self.wren:
            await self.wren.close()


async def main():
    """Run evaluation."""
    # Parse arguments
    parser = argparse.ArgumentParser(description='Evaluate Wren AI performance')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    parser.add_argument('--parallel-scaling', action='store_true', help='Enable parallel scaling (not yet implemented)')
    parser.add_argument('--candidates', type=int, default=5, help='Number of candidates for parallel scaling')
    parser.add_argument('--output', type=str, help='Output file path')
    args = parser.parse_args()

    # Load test cases
    test_file = Path(__file__).parent / 'test_queries.json'

    if not test_file.exists():
        logger.error(f"❌ Test file not found: {test_file}")
        return

    with open(test_file, 'r') as f:
        test_cases = json.load(f)

    logger.info(f"📋 Loaded {len(test_cases)} test cases from {test_file}")

    # Initialize
    config = Config()
    evaluator = Evaluator(config, verbose=args.verbose)

    try:
        await evaluator.initialize()

        # Run evaluation
        print("\n🚀 Starting evaluation...\n")
        metrics = await evaluator.evaluate_all(test_cases)

        # Print report
        evaluator.print_report(metrics, test_cases)

        # Save results
        if args.output:
            output_file = Path(args.output)
        else:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            phase_name = 'baseline'  # Can be changed based on args
            output_file = Path(__file__).parent / 'results' / f'{phase_name}_{timestamp}.json'

        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w') as f:
            json.dump(metrics, f, indent=2)

        print(f"💾 Results saved to: {output_file}")

        # Print summary
        print(f"\n🎯 Overall Success Rate: {metrics['success_rate']*100:.1f}%")

        if metrics['success_rate'] >= 0.90:
            print("🌟 Excellent performance!")
        elif metrics['success_rate'] >= 0.75:
            print("👍 Good performance")
        elif metrics['success_rate'] >= 0.60:
            print("📈 Room for improvement")
        else:
            print("⚠️  Needs significant improvement")

    finally:
        # Cleanup
        await evaluator.close()


if __name__ == "__main__":
    asyncio.run(main())
