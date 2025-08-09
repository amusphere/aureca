"""
Unit tests for PlanLimits constants class
"""

from app.constants.plan_limits import PlanLimits


class TestPlanLimits:
    """Test PlanLimits constants class"""

    def test_get_limit_free_plan(self):
        """Test getting limit for free plan"""
        limit = PlanLimits.get_limit("free")
        assert limit == 0

    def test_get_limit_standard_plan(self):
        """Test getting limit for standard plan"""
        limit = PlanLimits.get_limit("standard")
        assert limit == 10

    def test_get_limit_unknown_plan(self):
        """Test getting limit for unknown plan defaults to free"""
        limit = PlanLimits.get_limit("unknown_plan")
        assert limit == 0

    def test_get_limit_none_plan(self):
        """Test getting limit for None plan defaults to free"""
        limit = PlanLimits.get_limit(None)
        assert limit == 0

    def test_get_limit_empty_string_plan(self):
        """Test getting limit for empty string plan defaults to free"""
        limit = PlanLimits.get_limit("")
        assert limit == 0

    def test_is_valid_plan_free(self):
        """Test is_valid_plan for free plan"""
        assert PlanLimits.is_valid_plan("free") is True

    def test_is_valid_plan_standard(self):
        """Test is_valid_plan for standard plan"""
        assert PlanLimits.is_valid_plan("standard") is True

    def test_is_valid_plan_unknown(self):
        """Test is_valid_plan for unknown plan"""
        assert PlanLimits.is_valid_plan("unknown_plan") is False

    def test_is_valid_plan_none(self):
        """Test is_valid_plan for None"""
        assert PlanLimits.is_valid_plan(None) is False

    def test_is_valid_plan_empty_string(self):
        """Test is_valid_plan for empty string"""
        assert PlanLimits.is_valid_plan("") is False

    def test_get_available_plans(self):
        """Test getting all available plans"""
        plans = PlanLimits.get_available_plans()

        assert isinstance(plans, list)
        assert len(plans) == 2
        assert "free" in plans
        assert "standard" in plans

    def test_get_plan_info(self):
        """Test getting plan information"""
        # Test valid plan
        info = PlanLimits.get_plan_info("standard")
        assert info["name"] == "standard"
        assert info["limit"] == 10
        assert info["is_valid"] is True

        # Test invalid plan
        info = PlanLimits.get_plan_info("invalid")
        assert info["name"] == "invalid"
        assert info["limit"] == 0
        assert info["is_valid"] is False

    def test_case_insensitivity(self):
        """Test that plan names are case insensitive"""
        assert PlanLimits.get_limit("FREE") == 0  # Should work with uppercase
        assert PlanLimits.get_limit("Free") == 0  # Should work with mixed case
        assert PlanLimits.get_limit("STANDARD") == 10  # Should work with uppercase
        assert PlanLimits.get_limit("Standard") == 10  # Should work with mixed case

        assert PlanLimits.is_valid_plan("FREE") is True
        assert PlanLimits.is_valid_plan("Free") is True
        assert PlanLimits.is_valid_plan("STANDARD") is True
        assert PlanLimits.is_valid_plan("Standard") is True

    def test_plan_constants_immutability(self):
        """Test that plan constants cannot be modified externally"""
        # This test ensures the constants are properly encapsulated
        original_free_limit = PlanLimits.get_limit("free")
        original_standard_limit = PlanLimits.get_limit("standard")

        # Try to get available plans and modify (this should not affect the constants)
        plans = PlanLimits.get_available_plans()
        if plans:
            plans.clear()  # Try to modify the returned list

        # Original limits should be unchanged
        assert PlanLimits.get_limit("free") == original_free_limit
        assert PlanLimits.get_limit("standard") == original_standard_limit

        # Available plans should still work
        new_plans = PlanLimits.get_available_plans()
        assert len(new_plans) == 2

    def test_boundary_values(self):
        """Test boundary values for plan limits"""
        # Free plan should be exactly 0
        assert PlanLimits.get_limit("free") == 0

        # Standard plan should be exactly 10
        assert PlanLimits.get_limit("standard") == 10

        # Verify these are the expected types
        assert isinstance(PlanLimits.get_limit("free"), int)
        assert isinstance(PlanLimits.get_limit("standard"), int)

    def test_performance_characteristics(self):
        """Test that plan limit lookups are fast (constant time)"""
        import time

        # Measure time for multiple lookups
        start_time = time.time()
        for _ in range(1000):
            PlanLimits.get_limit("free")
            PlanLimits.get_limit("standard")
            PlanLimits.get_limit("unknown")
        end_time = time.time()

        # Should complete very quickly (less than 0.1 seconds for 1000 lookups)
        elapsed_time = end_time - start_time
        assert elapsed_time < 0.1, f"Plan limit lookups took too long: {elapsed_time} seconds"

    def test_string_representation_consistency(self):
        """Test that plan names are handled consistently as strings"""
        # Test with different string-like inputs
        assert PlanLimits.get_limit("free") == 0
        assert PlanLimits.get_limit("free") == 0

        # Test with non-string inputs (should handle gracefully)
        assert PlanLimits.get_limit(123) == 0  # Should default to free
        assert PlanLimits.get_limit([]) == 0  # Should default to free
        assert PlanLimits.get_limit({}) == 0  # Should default to free
