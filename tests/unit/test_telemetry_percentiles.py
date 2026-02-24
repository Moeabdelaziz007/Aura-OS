"""
Unit tests for telemetry P95/P99 latency tracking.
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from agent.aether_core.aether_telemetry import AetherLatencyTracker, AetherTelemetryManager, AetherLatencyTimer


def test_latency_tracker_basic():
    """Test basic latency tracking functionality."""
    print("Testing LatencyTracker basic functionality...")
    
    tracker = AetherLatencyTracker(window_size=100)
    
    # Record some sample latencies
    sample_latencies = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    for latency in sample_latencies:
        tracker.aether_record_latency(latency)
    
    # Test average
    avg = tracker.aether_calculate_avg_latency()
    expected_avg = sum(sample_latencies) / len(sample_latencies)
    assert abs(avg - expected_avg) < 0.01, f"Expected avg {expected_avg}, got {avg}"
    print(f"  ✓ Average latency: {avg:.2f}ms")
    
    # Test P50 (median)
    p50 = tracker.aether_calculate_p50_latency()
    assert p50 == 55.0, f"Expected P50 55.0, got {p50}"
    print(f"  ✓ P50 latency: {p50:.2f}ms")
    
    # Test P95
    p95 = tracker.aether_calculate_p95_latency()
    # With 10 samples, index = 9.5 -> 9 -> value 100
    assert p95 == 100.0, f"Expected P95 100.0, got {p95}"
    print(f"  ✓ P95 latency: {p95:.2f}ms")
    
    # Test P99
    p99 = tracker.aether_calculate_p99_latency()
    # With 10 samples, index = 9.9 -> 9 -> value 100
    assert p99 == 100.0, f"Expected P99 100.0, got {p99}"
    print(f"  ✓ P99 latency: {p99:.2f}ms")
    
    # Test percentile metrics dict
    metrics = tracker.aether_get_percentile_metrics()
    assert "p50_latency_ms" in metrics
    assert "p95_latency_ms" in metrics
    assert "p99_latency_ms" in metrics
    print(f"  ✓ Percentile metrics dict: {metrics}")


def test_latency_tracker_large_dataset():
    """Test with a larger dataset for more accurate percentiles."""
    print("\nTesting LatencyTracker with large dataset...")
    
    tracker = AetherLatencyTracker(window_size=1000)
    
    # Generate 1000 samples with a normal distribution-like pattern
    import random
    random.seed(42)
    latencies = []
    for _ in range(1000):
        # Generate latencies between 5ms and 200ms with some clustering
        base = random.gauss(50, 30)
        latency = max(5, min(200, base))
        latencies.append(latency)
        tracker.aether_record_latency(latency)
    
    # Test percentiles
    p50 = tracker.aether_calculate_p50_latency()
    p95 = tracker.aether_calculate_p95_latency()
    p99 = tracker.aether_calculate_p99_latency()
    
    # Verify ordering
    assert p50 is not None and p95 is not None and p99 is not None
    assert p50 <= p95 <= p99, f"Percentiles not ordered: P50={p50}, P95={p95}, P99={p99}"
    print(f"  ✓ P50: {p50:.2f}ms, P95: {p95:.2f}ms, P99: {p99:.2f}ms")
    
    # Verify percentiles are in reasonable ranges
    assert 40 < p50 < 60, f"P50 out of expected range: {p50}"
    assert 90 < p95 < 120, f"P95 out of expected range: {p95}"
    assert 100 < p99 < 140, f"P99 out of expected range: {p99}"
    print(f"  ✓ Percentiles are in expected ranges")


def test_latency_tracker_rolling_window():
    """Test rolling window behavior."""
    print("\nTesting LatencyTracker rolling window...")
    
    tracker = AetherLatencyTracker(window_size=10)
    
    # Add 20 samples
    for i in range(20):
        tracker.aether_record_latency(i)
    
    # Should only have last 10 samples (10-19)
    samples = tracker.aether_get_latency_samples()
    assert len(samples) == 10, f"Expected 10 samples, got {len(samples)}"
    assert samples == list(range(10, 20)), f"Expected [10-19], got {samples}"
    print(f"  ✓ Rolling window maintains correct size: {len(samples)} samples")
    
    # Verify percentiles based on rolling window
    p50 = tracker.aether_calculate_p50_latency()
    assert p50 == 14.5, f"Expected P50 14.5, got {p50}"
    print(f"  ✓ P50 from rolling window: {p50:.2f}ms")


def test_resource_metrics():
    """Test resource metrics tracking."""
    print("\nTesting resource metrics tracking...")
    
    tracker = AetherLatencyTracker(window_size=10)
    
    # Record latencies with resource data
    expected_cpu = []
    expected_memory = []
    expected_energy = []
    
    for i in range(5):
        cpu = 10.0 + i * 2
        memory = 100.0 + i * 10
        energy = 5.0 + i
        
        expected_cpu.append(cpu)
        expected_memory.append(memory)
        expected_energy.append(energy)
        
        resource_data = {
            "cpu_percent": cpu,
            "memory_mb": memory,
            "energy_mj": energy
        }
        tracker.aether_record_latency(50 + i, resource_data)
    
    metrics = tracker.aether_get_resource_metrics()
    
    assert metrics["sample_count"] == 5, f"Expected 5 samples, got {metrics['sample_count']}"
    
    # Calculate expected values
    expected_avg_cpu = sum(expected_cpu) / len(expected_cpu)
    expected_avg_memory = sum(expected_memory) / len(expected_memory)
    expected_total_energy = sum(expected_energy)
    
    # Use tolerance for floating point comparisons
    assert abs(metrics["avg_cpu_percent"] - expected_avg_cpu) < 0.1, \
        f"CPU mismatch: {metrics['avg_cpu_percent']} vs {expected_avg_cpu}"
    assert abs(metrics["avg_memory_mb"] - expected_avg_memory) < 0.1, \
        f"Memory mismatch: {metrics['avg_memory_mb']} vs {expected_avg_memory}"
    assert abs(metrics["total_energy_mj"] - expected_total_energy) < 0.1, \
        f"Energy mismatch: {metrics['total_energy_mj']} vs {expected_total_energy}"
    
    print(f"  ✓ Resource metrics: CPU={metrics['avg_cpu_percent']:.1f}%, "
          f"Memory={metrics['avg_memory_mb']:.1f}MB, Energy={metrics['total_energy_mj']:.1f}mJ")


def test_empty_tracker():
    """Test tracker behavior with no samples."""
    print("\nTesting empty tracker...")
    
    tracker = AetherLatencyTracker()
    
    assert tracker.aether_calculate_p50_latency() is None
    assert tracker.aether_calculate_p95_latency() is None
    assert tracker.aether_calculate_p99_latency() is None
    assert tracker.aether_calculate_avg_latency() is None
    
    metrics = tracker.aether_get_percentile_metrics()
    assert metrics["p50_latency_ms"] is None
    assert metrics["p95_latency_ms"] is None
    assert metrics["p99_latency_ms"] is None
    
    resource_metrics = tracker.aether_get_resource_metrics()
    assert resource_metrics["sample_count"] == 0
    
    print(f"  ✓ Empty tracker returns None for percentiles")


def test_clear_tracker():
    """Test clearing the tracker."""
    print("\nTesting tracker clear...")
    
    tracker = AetherLatencyTracker()
    
    # Add samples
    for i in range(10):
        tracker.aether_record_latency(i)
    
    assert len(tracker.aether_get_latency_samples()) == 10
    
    # Clear
    tracker.aether_clear()
    
    assert len(tracker.aether_get_latency_samples()) == 0
    assert tracker.aether_calculate_p50_latency() is None
    
    print(f"  ✓ Tracker cleared successfully")


def test_latency_timer():
    """Test the LatencyTimer context manager."""
    print("\nTesting LatencyTimer context manager...")
    
    async def run_timer():
        async with AetherLatencyTimer() as timer:
            await asyncio.sleep(0.01)  # 10ms sleep
        
        # Verify latency was recorded
        tracker = await AetherTelemetryManager.aether_get_latency_tracker()
        samples = tracker.aether_get_latency_samples()
        assert len(samples) >= 1
        # Should be approximately 10ms (with some overhead)
        assert samples[-1] >= 8, f"Latency too low: {samples[-1]}ms"
        assert samples[-1] < 50, f"Latency too high: {samples[-1]}ms"
        print(f"  ✓ LatencyTimer recorded: {samples[-1]:.2f}ms")
    
    asyncio.run(run_timer())


def test_telemetry_manager_integration():
    """Test TelemetryManager integration with latency tracking."""
    print("\nTesting TelemetryManager integration...")
    
    async def run_integration():
        # Clear tracker
        tracker = await AetherTelemetryManager.aether_get_latency_tracker()
        tracker.aether_clear()
        
        # Record some latencies
        await AetherTelemetryManager.aether_record_request_latency(50.0)
        await AetherTelemetryManager.aether_record_request_latency(75.0)
        await AetherTelemetryManager.aether_record_request_latency(100.0)
        
        # Verify samples were recorded
        tracker = await AetherTelemetryManager.aether_get_latency_tracker()
        assert len(tracker.aether_get_latency_samples()) == 3
        
        # Verify percentiles
        p50 = tracker.aether_calculate_p50_latency()
        assert p50 == 75.0
        
        p95 = tracker.aether_calculate_p95_latency()
        assert p95 == 100.0
        
        print(f"  ✓ TelemetryManager integration: P50={p50:.2f}ms, P95={p95:.2f}ms")
    
    asyncio.run(run_integration())


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("Running Telemetry P95/P99 Tests")
    print("=" * 60)
    
    tests = [
        test_latency_tracker_basic,
        test_latency_tracker_large_dataset,
        test_latency_tracker_rolling_window,
        test_resource_metrics,
        test_empty_tracker,
        test_clear_tracker,
        test_latency_timer,
        test_telemetry_manager_integration
    ]
    
    failed = []
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"  ✗ FAILED: {e}")
            failed.append((test.__name__, e))
    
    print("\n" + "=" * 60)
    if failed:
        print(f"FAILED: {len(failed)} test(s) failed")
        for name, error in failed:
            print(f"  - {name}: {error}")
        return False
    else:
        print("SUCCESS: All tests passed!")
        return True


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
