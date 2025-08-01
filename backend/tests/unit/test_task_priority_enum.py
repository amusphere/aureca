"""Unit tests for task priority enum and validation."""

import pytest
from app.schema import TaskPriority


class TestTaskPriorityEnum:
    """Test TaskPriority enum functionality."""

    def test_priority_enum_values(self):
        """Test that TaskPriority enum has correct values."""
        assert TaskPriority.HIGH == 1
        assert TaskPriority.MIDDLE == 2
        assert TaskPriority.LOW == 3

    def test_priority_enum_ordering(self):
        """Test that TaskPriority enum values maintain correct ordering."""
        priorities = [TaskPriority.LOW, TaskPriority.HIGH, TaskPriority.MIDDLE]
        sorted_priorities = sorted(priorities)

        expected_order = [TaskPriority.HIGH, TaskPriority.MIDDLE, TaskPriority.LOW]
        assert sorted_priorities == expected_order

    def test_priority_enum_comparison(self):
        """Test TaskPriority enum comparison operations."""
        assert TaskPriority.HIGH < TaskPriority.MIDDLE
        assert TaskPriority.MIDDLE < TaskPriority.LOW
        assert TaskPriority.HIGH < TaskPriority.LOW

        assert TaskPriority.LOW > TaskPriority.MIDDLE
        assert TaskPriority.MIDDLE > TaskPriority.HIGH
        assert TaskPriority.LOW > TaskPriority.HIGH

    def test_priority_enum_equality(self):
        """Test TaskPriority enum equality operations."""
        assert TaskPriority.HIGH == TaskPriority.HIGH
        assert TaskPriority.MIDDLE == TaskPriority.MIDDLE
        assert TaskPriority.LOW == TaskPriority.LOW

        assert TaskPriority.HIGH != TaskPriority.MIDDLE
        assert TaskPriority.HIGH != TaskPriority.LOW
        assert TaskPriority.MIDDLE != TaskPriority.LOW

    def test_priority_enum_with_none_sorting(self):
        """Test sorting behavior when None is mixed with priority enum values."""
        priorities = [None, TaskPriority.MIDDLE, TaskPriority.HIGH, None, TaskPriority.LOW]

        # Sort with None handling (None should be treated as highest value)
        def sort_key(priority):
            return priority if priority is not None else float('inf')

        sorted_priorities = sorted(priorities, key=sort_key)
        expected_order = [TaskPriority.HIGH, TaskPriority.MIDDLE, TaskPriority.LOW, None, None]

        assert sorted_priorities == expected_order

    def test_priority_enum_int_conversion(self):
        """Test that TaskPriority enum can be converted to int."""
        assert int(TaskPriority.HIGH) == 1
        assert int(TaskPriority.MIDDLE) == 2
        assert int(TaskPriority.LOW) == 3

    def test_priority_enum_string_representation(self):
        """Test string representation of TaskPriority enum."""
        assert str(TaskPriority.HIGH) == "TaskPriority.HIGH"
        assert str(TaskPriority.MIDDLE) == "TaskPriority.MIDDLE"
        assert str(TaskPriority.LOW) == "TaskPriority.LOW"

    def test_priority_enum_name_attribute(self):
        """Test that TaskPriority enum has correct name attributes."""
        assert TaskPriority.HIGH.name == "HIGH"
        assert TaskPriority.MIDDLE.name == "MIDDLE"
        assert TaskPriority.LOW.name == "LOW"

    def test_priority_enum_value_attribute(self):
        """Test that TaskPriority enum has correct value attributes."""
        assert TaskPriority.HIGH.value == 1
        assert TaskPriority.MIDDLE.value == 2
        assert TaskPriority.LOW.value == 3

    def test_priority_enum_iteration(self):
        """Test that TaskPriority enum can be iterated."""
        priorities = list(TaskPriority)
        expected_priorities = [TaskPriority.HIGH, TaskPriority.MIDDLE, TaskPriority.LOW]

        assert priorities == expected_priorities
        assert len(priorities) == 3

    def test_priority_enum_membership(self):
        """Test membership testing for TaskPriority enum."""
        assert TaskPriority.HIGH in TaskPriority
        assert TaskPriority.MIDDLE in TaskPriority
        assert TaskPriority.LOW in TaskPriority

        # Note: In Python, integer values are considered members of int-based Enums
        # This is expected behavior for int-based Enums
        assert 1 in TaskPriority  # TaskPriority.HIGH.value
        assert 2 in TaskPriority  # TaskPriority.MIDDLE.value
        assert 3 in TaskPriority  # TaskPriority.LOW.value

        # But invalid values should not be members
        assert 0 not in TaskPriority
        assert 4 not in TaskPriority

    def test_priority_enum_from_value(self):
        """Test creating TaskPriority from integer values."""
        assert TaskPriority(1) == TaskPriority.HIGH
        assert TaskPriority(2) == TaskPriority.MIDDLE
        assert TaskPriority(3) == TaskPriority.LOW

    def test_priority_enum_invalid_value(self):
        """Test that invalid values raise appropriate errors."""
        with pytest.raises(ValueError):
            TaskPriority(0)

        with pytest.raises(ValueError):
            TaskPriority(4)

        with pytest.raises(ValueError):
            TaskPriority(-1)
