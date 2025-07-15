"""
Simplified spoke manager - Handles spoke discovery, loading, and execution
"""

import importlib.util
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Type, Any

from app.schema import User
from sqlmodel import Session

from ..core.models import NextAction, SpokeResponse
from ..utils.exceptions import ActionExecutionError
from ..utils.logger import AIAssistantLogger
from .base import BaseSpoke


@dataclass
class ActionParameter:
    """Action parameter definition"""

    type: str
    required: bool
    description: str
    format: Optional[str] = None
    default: Optional[str] = None


@dataclass
class ActionDefinition:
    """Action definition"""

    action_type: str
    display_name: str
    description: str
    parameters: Dict[str, ActionParameter]


@dataclass
class SpokeConfig:
    """Spoke configuration"""

    spoke_name: str
    display_name: str
    description: str
    actions: List[ActionDefinition]


class SpokeManager:
    """
    Simplified spoke manager that handles spoke discovery, loading, and execution

    Combines the functionality of the previous SpokeConfigLoader, SpokeRegistry,
    DynamicSpokeLoader, and SpokeManager into a single, simpler class.
    """

    def __init__(self, spokes_dir: str, session: Optional[Session] = None):
        self.spokes_dir = Path(spokes_dir)
        self.session = session
        self.logger = AIAssistantLogger("spoke_manager")

        # Internal storage
        self._spoke_configs: Dict[str, SpokeConfig] = {}
        self._spoke_classes: Dict[str, Type[BaseSpoke]] = {}
        self._spoke_instances: Dict[str, BaseSpoke] = {}
        self._action_to_spoke: Dict[str, str] = {}

        # Load all spokes during initialization
        self._load_all_spokes()

    def _load_all_spokes(self):
        """Load all spoke configurations and classes"""
        self.logger.info(f"Loading spokes from: {self.spokes_dir}")

        if not self.spokes_dir.exists():
            self.logger.warning(f"Spokes directory not found: {self.spokes_dir}")
            return

        excluded_dirs = {"__pycache__", ".git", "node_modules", "venv", ".venv", "base"}

        for spoke_dir in self.spokes_dir.iterdir():
            if (
                spoke_dir.is_dir()
                and not spoke_dir.name.startswith(".")
                and spoke_dir.name not in excluded_dirs
            ):
                self._load_spoke(spoke_dir)

        # Build action-to-spoke mapping
        self._build_action_mapping()

        self.logger.info(
            f"Loaded {len(self._spoke_configs)} spokes with {len(self._action_to_spoke)} total actions"
        )

    def _load_spoke(self, spoke_dir: Path):
        """Load a single spoke"""
        spoke_name = spoke_dir.name

        try:
            # Load configuration
            config_file = spoke_dir / "actions.json"
            if not config_file.exists():
                self.logger.warning(f"No actions.json found in: {spoke_dir}")
                return

            config = self._load_spoke_config(config_file)
            self._spoke_configs[spoke_name] = config

            # Load spoke class
            spoke_file = spoke_dir / "spoke.py"
            if not spoke_file.exists():
                self.logger.warning(f"No spoke.py found in: {spoke_dir}")
                return

            spoke_class = self._load_spoke_class(spoke_file, spoke_name)
            if spoke_class:
                self._spoke_classes[spoke_name] = spoke_class
                self.logger.info(f"Loaded spoke: {spoke_name}")
            else:
                self.logger.error(f"Failed to load spoke class: {spoke_name}")

        except Exception as e:
            self.logger.error(f"Error loading spoke {spoke_name}: {str(e)}")

    def _load_spoke_config(self, config_file: Path) -> SpokeConfig:
        """Load spoke configuration from JSON file"""
        with open(config_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Parse action definitions
        actions = []
        for action_data in data.get("actions", []):
            parameters = {}
            for param_name, param_data in action_data.get("parameters", {}).items():
                parameters[param_name] = ActionParameter(
                    type=param_data.get("type", "string"),
                    required=param_data.get("required", False),
                    description=param_data.get("description", ""),
                    format=param_data.get("format"),
                    default=param_data.get("default"),
                )

            action = ActionDefinition(
                action_type=action_data.get("action_type", ""),
                display_name=action_data.get("display_name", ""),
                description=action_data.get("description", ""),
                parameters=parameters,
            )
            actions.append(action)

        return SpokeConfig(
            spoke_name=data.get("spoke_name", ""),
            display_name=data.get("display_name", ""),
            description=data.get("description", ""),
            actions=actions,
        )

    def _load_spoke_class(
        self, spoke_file: Path, spoke_name: str
    ) -> Optional[Type[BaseSpoke]]:
        """Dynamically load spoke class from file"""
        try:
            spec = importlib.util.spec_from_file_location(
                f"{spoke_name}_spoke", str(spoke_file)
            )
            if spec is None or spec.loader is None:
                self.logger.error(f"Failed to create module spec for {spoke_name}")
                return None

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Find spoke class using naming convention
            class_name = self._get_spoke_class_name(spoke_name)
            spoke_class = getattr(module, class_name, None)

            if spoke_class is None:
                self.logger.error(f"Spoke class {class_name} not found in {spoke_file}")
                return None

            if not issubclass(spoke_class, BaseSpoke):
                self.logger.error(f"Class {class_name} is not a subclass of BaseSpoke")
                return None

            return spoke_class

        except Exception as e:
            self.logger.error(f"Failed to load spoke class from {spoke_file}: {str(e)}")
            return None

    def _get_spoke_class_name(self, spoke_name: str) -> str:
        """Generate class name from spoke name"""
        # gmail -> GmailSpoke
        # google_calendar -> GoogleCalendarSpoke
        parts = spoke_name.split("_")
        class_name = "".join(word.capitalize() for word in parts) + "Spoke"
        return class_name

    def _build_action_mapping(self):
        """Build mapping from action types to spoke names"""
        self._action_to_spoke.clear()
        for spoke_name, config in self._spoke_configs.items():
            for action in config.actions:
                self._action_to_spoke[action.action_type] = spoke_name

    def get_spoke_instance(
        self, spoke_name: str, current_user: User
    ) -> Optional[BaseSpoke]:
        """Get spoke instance (with caching)"""
        cache_key = f"{spoke_name}_{current_user.id}"

        if cache_key in self._spoke_instances:
            return self._spoke_instances[cache_key]

        spoke_class = self._spoke_classes.get(spoke_name)
        if spoke_class is None:
            self.logger.error(f"Spoke class not found: {spoke_name}")
            return None

        try:
            instance = spoke_class(self.session, current_user)
            self._spoke_instances[cache_key] = instance
            return instance
        except Exception as e:
            self.logger.error(f"Failed to instantiate spoke {spoke_name}: {str(e)}")
            return None

    async def execute_action(
        self, action: NextAction, current_user: User
    ) -> SpokeResponse:
        """Execute action through appropriate spoke"""
        try:
            # Find spoke for action
            spoke_name = self._action_to_spoke.get(action.action_type)
            if spoke_name is None:
                return SpokeResponse(
                    success=False,
                    error=f"No spoke found for action type: {action.action_type}",
                )

            # Get action definition
            action_definition = self._get_action_definition(
                spoke_name, action.action_type
            )
            if action_definition is None:
                return SpokeResponse(
                    success=False,
                    error=f"Action definition not found: {spoke_name}.{action.action_type}",
                )

            # Get spoke instance
            spoke_instance = self.get_spoke_instance(spoke_name, current_user)
            if spoke_instance is None:
                return SpokeResponse(
                    success=False,
                    error=f"Failed to get spoke instance: {spoke_name}",
                )

            # Execute action
            self.logger.info(f"Executing action: {spoke_name}.{action.action_type}")
            result = await spoke_instance.execute_action(
                action, action_definition.__dict__
            )

            return result

        except Exception as e:
            error_msg = f"Error executing action {action.action_type}: {str(e)}"
            self.logger.log_error(
                ActionExecutionError(error_msg),
                {
                    "action_type": action.action_type,
                    "spoke_name": getattr(action, "spoke_name", "unknown"),
                },
            )
            return SpokeResponse(success=False, error=error_msg)

    def _get_action_definition(
        self, spoke_name: str, action_type: str
    ) -> Optional[ActionDefinition]:
        """Get action definition for specific spoke and action"""
        config = self._spoke_configs.get(spoke_name)
        if config:
            for action in config.actions:
                if action.action_type == action_type:
                    return action
        return None

    def get_all_action_types(self) -> List[str]:
        """Get all available action types"""
        return sorted(self._action_to_spoke.keys())

    def get_actions_description(self) -> str:
        """Get formatted description of all available actions"""
        actions_list = []

        for config in self._spoke_configs.values():
            actions_list.append(
                f"\n## {config.display_name}\n"
                f"スポーク名: {config.spoke_name}\n"
                f"説明: {config.description}"
            )

            actions_list.append("\n### アクション名 : 説明 : パラメータ")

            for action in config.actions:
                actions_list.append(
                    f"- {action.action_type} : {action.description} : {action.parameters}"
                )

        return "\n".join(actions_list)

    def get_spoke_configs(self) -> Dict[str, SpokeConfig]:
        """Get all spoke configurations"""
        return self._spoke_configs.copy()
