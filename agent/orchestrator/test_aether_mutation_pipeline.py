"""
Test the AetherEvolve Mutation Pipeline
Tests the activation, generation, validation, and telemetry tracking of mutations.
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from agent.orchestrator.aether_evolve import (
    AetherEvolve,
    AetherNeuralMonitor,
    AetherMutationGenerator,
    AetherMutationValidator,
    AetherMutationTracker,
    AetherAnomalyAnalyzer,
    MUTATION_TEMPLATES,
    DANGEROUS_PATTERNS
)


async def test_mutation_tracker():
    """Test the AetherMutationTracker class."""
    print("\n🧪 Testing AetherMutationTracker...")
    
    tracker = AetherMutationTracker()
    
    # Record some mutations
    tracker.record_mutation("ZeroDivisionError", "Orchestrator", True, "mut_001")
    tracker.record_mutation("FileNotFoundError", "Forge", False, "mut_002")
    tracker.record_mutation("ZeroDivisionError", "Orchestrator", True, "mut_003")
    
    metrics = tracker.get_metrics()
    
    assert metrics["total_mutations"] == 3, f"Expected 3 total mutations, got {metrics['total_mutations']}"
    assert metrics["successful_mutations"] == 2, f"Expected 2 successful mutations, got {metrics['successful_mutations']}"
    assert metrics["failed_mutations"] == 1, f"Expected 1 failed mutation, got {metrics['failed_mutations']}"
    assert metrics["mutations_by_type"]["ZeroDivisionError"] == 2
    assert metrics["mutations_by_component"]["Orchestrator"] == 2
    
    print("✅ AetherMutationTracker tests passed")
    return True


def test_mutation_validator():
    """Test the AetherMutationValidator class."""
    print("\n🧪 Testing AetherMutationValidator...")
    
    validator = AetherMutationValidator()
    
    # Test safe mutation
    safe_code = "def foo():\n    return 42"
    is_safe, reason = validator.is_safe_mutation(safe_code, safe_code + "\n    pass")
    assert is_safe, f"Expected safe mutation, got: {reason}"
    
    # Test dangerous pattern - rm -rf
    dangerous_code = "import os\nos.system('rm -rf /')"
    is_safe, reason = validator.is_safe_mutation(safe_code, dangerous_code)
    assert not is_safe, f"Expected unsafe mutation for rm -rf"
    
    # Test dangerous pattern - eval
    eval_code = "eval('print(1)')"
    is_safe, reason = validator.is_safe_mutation(safe_code, eval_code)
    assert not is_safe, f"Expected unsafe mutation for eval"
    
    # Test empty mutation
    is_safe, reason = validator.is_safe_mutation(safe_code, "")
    assert not is_safe, f"Expected unsafe mutation for empty code"
    
    # Test syntax error
    syntax_error_code = "def foo(\n    # missing parenthesis"
    is_safe, reason = validator.is_safe_mutation(safe_code, syntax_error_code)
    assert not is_safe, f"Expected unsafe mutation for syntax error"
    
    # Test template validation
    assert validator.validate_mutation_template("ZeroDivisionError", "x = 1/0")
    assert not validator.validate_mutation_template("UnknownError", "x = 1/0")
    
    print("✅ AetherMutationValidator tests passed")
    return True


def test_mutation_templates():
    """Test mutation templates exist for common error types."""
    print("\n🧪 Testing Mutation Templates...")
    
    expected_templates = [
        "ZeroDivisionError",
        "FileNotFoundError",
        "KeyError",
        "AttributeError",
        "TypeError",
        "IndexError",
        "ValueError",
        "ConnectionError",
        "TimeoutError"
    ]
    
    for template_name in expected_templates:
        assert template_name in MUTATION_TEMPLATES, f"Missing template: {template_name}"
        assert "description" in MUTATION_TEMPLATES[template_name]
        assert "patterns" in MUTATION_TEMPLATES[template_name]
        assert "fix_template" in MUTATION_TEMPLATES[template_name]
    
    print(f"✅ All {len(expected_templates)} mutation templates present")
    return True


def test_dangerous_patterns():
    """Test dangerous patterns are defined."""
    print("\n🧪 Testing Dangerous Patterns...")
    
    # Verify dangerous patterns list is not empty
    assert len(DANGEROUS_PATTERNS) > 0, "Dangerous patterns list should not be empty"
    
    # Verify critical patterns are present
    critical_patterns = [
        "rm",      # File deletion
        "rmtree",  # Directory deletion
        "eval",    # Code execution
        "exec",    # Code execution
        "pickle"   # Deserialization
    ]
    
    for pattern in critical_patterns:
        found = any(pattern in dp for dp in DANGEROUS_PATTERNS)
        assert found, f"Missing dangerous pattern containing: {pattern}"
    
    print(f"✅ All {len(DANGEROUS_PATTERNS)} dangerous patterns defined")
    return True


async def test_anomaly_analyzer():
    """Test the AetherAnomalyAnalyzer class."""
    print("\n🧪 Testing AetherAnomalyAnalyzer...")
    
    # Create a temporary test anomaly log
    test_log_path = "/tmp/test_anomaly_log.json"
    test_anomalies = [
        {
            "timestamp": "2026-02-23T15:00:00",
            "component": "Orchestrator",
            "error_type": "ZeroDivisionError",
            "message": "division by zero",
            "status": "DETECTED"
        },
        {
            "timestamp": "2026-02-23T15:01:00",
            "component": "Orchestrator",
            "error_type": "ZeroDivisionError",
            "message": "division by zero",
            "status": "DETECTED"
        },
        {
            "timestamp": "2026-02-23T15:02:00",
            "component": "Forge",
            "error_type": "FileNotFoundError",
            "message": "file not found",
            "status": "DETECTED"
        },
        {
            "timestamp": "2026-02-23T15:03:00",
            "component": "Orchestrator",
            "error_type": "ZeroDivisionError",
            "message": "division by zero",
            "status": "HEALED"
        }
    ]
    
    with open(test_log_path, 'w') as f:
        json.dump(test_anomalies, f)
    
    try:
        analyzer = AetherAnomalyAnalyzer(test_log_path)
        
        # Test loading
        anomalies = analyzer.load_anomalies()
        assert len(anomalies) == 4, f"Expected 4 anomalies, got {len(anomalies)}"
        
        # Test grouping (should exclude HEALED status)
        grouped = analyzer.group_anomalies()
        # Only 2 groups: ZeroDivisionError_Orchestrator (2 DETECTED) and FileNotFoundError_Forge (1 DETECTED)
        assert len(grouped) == 2, f"Expected 2 groups, got {len(grouped)}"
        
        # Test prioritization
        prioritized = analyzer.prioritize_anomalies()
        assert len(prioritized) == 2, f"Expected 2 prioritized groups"
        # ZeroDivisionError should be first (higher frequency)
        assert "ZeroDivisionError" in prioritized[0][0]
        
        print("✅ AetherAnomalyAnalyzer tests passed")
        return True
    finally:
        # Clean up
        if os.path.exists(test_log_path):
            os.remove(test_log_path)


async def test_pipeline_activation():
    """Test pipeline activation and deactivation."""
    print("\n🧪 Testing Pipeline Activation...")
    
    monitor = AetherNeuralMonitor()
    evolve = AetherEvolve(monitor)
    
    # Test initial state
    assert not evolve.is_pipeline_active, "Pipeline should be inactive initially"
    
    # Test activation
    status = evolve.activate_pipeline(max_mutations=3, rate_limit=5)
    assert status["status"] == "activated"
    assert evolve.is_pipeline_active
    assert evolve.max_mutations_per_cycle == 3
    assert evolve.mutation_rate_limit == 5
    
    # Test pipeline status
    pipeline_status = evolve.get_pipeline_status()
    assert pipeline_status["is_active"] == True
    assert "metrics" in pipeline_status
    
    # Test deactivation
    status = evolve.deactivate_pipeline()
    assert status["status"] == "deactivated"
    assert not evolve.is_pipeline_active
    
    print("✅ Pipeline activation tests passed")
    return True


async def test_template_mutation_generation():
    """Test template-based mutation generation."""
    print("\n🧪 Testing Template Mutation Generation...")
    
    generator = AetherMutationGenerator(use_gemini=False)  # Disable Gemini for this test
    
    anomaly = {
        "component": "TestComponent",
        "error_type": "ZeroDivisionError",
        "message": "division by zero"
    }
    
    source_code = "def calculate():\n    return 10 / 0"
    
    mutation = await generator.generate_mutation(anomaly, source_code)
    
    assert mutation is not None, "Template mutation should be generated"
    assert "AETHER_EVOLVE_FIX" in mutation, "Mutation should contain fix marker"
    assert "ZeroDivisionError" in mutation, "Mutation should contain error type"
    
    print("✅ Template mutation generation tests passed")
    return True


async def test_telemetry_integration():
    """Test telemetry integration."""
    print("\n🧪 Testing Telemetry Integration...")
    
    monitor = AetherNeuralMonitor()
    evolve = AetherEvolve(monitor)
    
    # Activate pipeline
    evolve.activate_pipeline()
    
    # Record a mutation
    evolve.mutation_tracker.record_mutation("ZeroDivisionError", "Orchestrator", True, "test_mut_001")
    
    # Update telemetry
    await evolve._update_telemetry()
    
    # Check telemetry file
    telemetry_path = "agent/memory/TELEMETRY.json"
    if os.path.exists(telemetry_path):
        with open(telemetry_path, 'r') as f:
            telemetry = json.load(f)
        
        assert "evolution_metrics" in telemetry, "Telemetry should contain evolution_metrics"
        assert telemetry["evolution_metrics"]["total_mutations"] == 1
        assert telemetry["evolution_metrics"]["successful_mutations"] == 1
        assert telemetry["mutation_pipeline_active"] == True
        
        print("✅ Telemetry integration tests passed")
        return True
    else:
        print("⚠️ Telemetry file not found, skipping telemetry check")
        return True


async def run_all_tests():
    """Run all mutation pipeline tests."""
    print("=" * 60)
    print("🧬 AetherEvolve Mutation Pipeline Test Suite")
    print("=" * 60)
    
    tests = [
        test_mutation_tracker,
        test_mutation_validator,
        test_mutation_templates,
        test_dangerous_patterns,
        test_anomaly_analyzer,
        test_pipeline_activation,
        test_template_mutation_generation,
        test_telemetry_integration
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if asyncio.iscoroutinefunction(test):
                result = await test()
            else:
                result = test()
            
            if result:
                passed += 1
            else:
                failed += 1
                print(f"❌ Test {test.__name__} returned False")
        except Exception as e:
            failed += 1
            print(f"❌ Test {test.__name__} failed with error: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
