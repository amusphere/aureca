#!/usr/bin/env python3
"""
CLI tool for managing AI chat usage configuration

Usage:
    python -m app.cli.config_manager list-plans
    python -m app.cli.config_manager get-plan basic
    python -m app.cli.config_manager set-plan premium --limit 50 --description "Premium plan"
    python -m app.cli.config_manager reload-config
"""

import argparse
import json
import sys
from pathlib import Path

# Add the app directory to the path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import config_manager, get_all_ai_chat_plans, update_ai_chat_plan_limit


def list_plans():
    """List all AI chat plans and their configurations"""
    plans = get_all_ai_chat_plans()

    if not plans:
        print("No plans configured.")
        return

    print("AI Chat Plans Configuration:")
    print("=" * 50)

    for plan_name, plan_config in plans.items():
        limit_str = "Unlimited" if plan_config.daily_limit == -1 else str(plan_config.daily_limit)
        print(f"\nPlan: {plan_name}")
        print(f"  Daily Limit: {limit_str}")
        print(f"  Description: {plan_config.description}")
        print(f"  Features: {', '.join(plan_config.features)}")


def get_plan(plan_name: str):
    """Get configuration for a specific plan"""
    plans = get_all_ai_chat_plans()

    if plan_name not in plans:
        print(f"Plan '{plan_name}' not found.")
        print(f"Available plans: {', '.join(plans.keys())}")
        return

    plan_config = plans[plan_name]
    limit_str = "Unlimited" if plan_config.daily_limit == -1 else str(plan_config.daily_limit)

    print(f"Plan Configuration: {plan_name}")
    print("=" * 30)
    print(f"Daily Limit: {limit_str}")
    print(f"Description: {plan_config.description}")
    print("Features:")
    for feature in plan_config.features:
        print(f"  - {feature}")


def set_plan(
    plan_name: str,
    limit: int,
    description: str | None = None,
    features: list[str] | None = None,
):
    """Set or update configuration for a plan"""
    try:
        success = update_ai_chat_plan_limit(
            plan_name=plan_name,
            daily_limit=limit,
            description=description,
            features=features,
        )

        if success:
            limit_str = "Unlimited" if limit == -1 else str(limit)
            print(f"Successfully updated plan '{plan_name}' with daily limit: {limit_str}")
            if description:
                print(f"Description: {description}")
            if features:
                print(f"Features: {', '.join(features)}")
        else:
            print(f"Failed to update plan '{plan_name}'")

    except Exception as e:
        print(f"Error updating plan '{plan_name}': {e}")


def reload_config():
    """Reload configuration from file"""
    try:
        config_manager._check_file_updates()
        print("Configuration reloaded successfully.")

        if config_manager._config_file_path:
            print(f"Config file: {config_manager._config_file_path}")
            if config_manager._last_modified:
                from datetime import datetime

                mod_time = datetime.fromtimestamp(config_manager._last_modified)
                print(f"Last modified: {mod_time}")
        else:
            print("No configuration file configured.")

    except Exception as e:
        print(f"Error reloading configuration: {e}")


def export_config(output_file: str):
    """Export current configuration to a file"""
    try:
        plans = get_all_ai_chat_plans()

        config_data = {
            "ai_chat_plans": {plan_name: plan_config.to_dict() for plan_name, plan_config in plans.items()},
            "exported_at": config_manager._last_modified or "unknown",
        }

        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)

        print(f"Configuration exported to: {output_path}")

    except Exception as e:
        print(f"Error exporting configuration: {e}")


def import_config(input_file: str):
    """Import configuration from a file"""
    try:
        input_path = Path(input_file)

        if not input_path.exists():
            print(f"Configuration file not found: {input_path}")
            return

        with open(input_path, encoding="utf-8") as f:
            config_data = json.load(f)

        if "ai_chat_plans" not in config_data:
            print("Invalid configuration file: missing 'ai_chat_plans' section")
            return

        imported_count = 0
        for plan_name, plan_data in config_data["ai_chat_plans"].items():
            success = update_ai_chat_plan_limit(
                plan_name=plan_name,
                daily_limit=plan_data.get("daily_limit", 0),
                description=plan_data.get("description", f"{plan_name} plan"),
                features=plan_data.get("features", []),
            )

            if success:
                imported_count += 1
                print(f"Imported plan: {plan_name}")
            else:
                print(f"Failed to import plan: {plan_name}")

        print(f"Successfully imported {imported_count} plans from {input_path}")

    except Exception as e:
        print(f"Error importing configuration: {e}")


def main():
    parser = argparse.ArgumentParser(description="AI Chat Usage Configuration Manager")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # List plans command
    subparsers.add_parser("list-plans", help="List all AI chat plans")

    # Get plan command
    get_parser = subparsers.add_parser("get-plan", help="Get configuration for a specific plan")
    get_parser.add_argument("plan_name", help="Name of the plan to retrieve")

    # Set plan command
    set_parser = subparsers.add_parser("set-plan", help="Set or update plan configuration")
    set_parser.add_argument("plan_name", help="Name of the plan to update")
    set_parser.add_argument("--limit", type=int, required=True, help="Daily usage limit (-1 for unlimited)")
    set_parser.add_argument("--description", help="Plan description")
    set_parser.add_argument("--features", nargs="*", help="List of plan features")

    # Reload config command
    subparsers.add_parser("reload-config", help="Reload configuration from file")

    # Export config command
    export_parser = subparsers.add_parser("export-config", help="Export configuration to file")
    export_parser.add_argument("output_file", help="Output file path")

    # Import config command
    import_parser = subparsers.add_parser("import-config", help="Import configuration from file")
    import_parser.add_argument("input_file", help="Input file path")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == "list-plans":
        list_plans()
    elif args.command == "get-plan":
        get_plan(args.plan_name)
    elif args.command == "set-plan":
        set_plan(args.plan_name, args.limit, args.description, args.features)
    elif args.command == "reload-config":
        reload_config()
    elif args.command == "export-config":
        export_config(args.output_file)
    elif args.command == "import-config":
        import_config(args.input_file)


if __name__ == "__main__":
    main()
