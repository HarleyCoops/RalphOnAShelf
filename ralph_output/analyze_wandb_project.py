import wandb
import json
import pandas as pd
from datetime import datetime

# Initialize W&B API
api_key = "cee32d77c7edb39a3857ede1c44fa2c7d7f89bb1"
wandb.login(key=api_key)
api = wandb.Api()

# Project details
entity = None  # Will be auto-detected
project_name = "railroad-1959-tinker"

print("=" * 80)
print("STEP 1: Getting Project Details")
print("=" * 80)

# Try to get the project - we need to find the entity first
try:
    # Get current user
    user = api.viewer
    entity = user.username if hasattr(user, 'username') else user.entity
    print(f"Entity: {entity}")
    print(f"Project: {project_name}")

    # Get all runs
    runs = api.runs(f"{entity}/{project_name}")
    print(f"\nTotal runs found: {len(runs)}")

    # Collect run data
    run_data = []
    all_metrics = set()
    all_configs = {}

    for i, run in enumerate(runs):
        print(f"\n--- Run {i+1}/{len(runs)} ---")
        print(f"Run ID: {run.id}")
        print(f"Run Name: {run.name}")
        print(f"State: {run.state}")
        print(f"Created: {run.created_at}")

        # Get config
        config = run.config
        print(f"Config keys: {list(config.keys())}")

        # Get summary metrics
        summary = run.summary._json_dict
        print(f"Summary keys: {list(summary.keys())}")

        # Track all unique metrics
        all_metrics.update(summary.keys())

        # Store run data
        run_info = {
            'id': run.id,
            'name': run.name,
            'state': run.state,
            'created': run.created_at,
            'config': config,
            'summary': summary
        }
        run_data.append(run_info)

        # Collect configs for analysis
        for key, value in config.items():
            if key not in all_configs:
                all_configs[key] = []
            all_configs[key].append(value)

    print("\n" + "=" * 80)
    print("STEP 2: Analyzing RL Mechanics")
    print("=" * 80)

    print("\nAll tracked metrics:")
    for metric in sorted(all_metrics):
        print(f"  - {metric}")

    print("\nConfiguration parameters across runs:")
    for key, values in sorted(all_configs.items()):
        unique_values = set(str(v) for v in values)
        if len(unique_values) == 1:
            print(f"  - {key}: {list(unique_values)[0]}")
        else:
            print(f"  - {key}: {unique_values}")

    # Try to get detailed history for first run
    if len(runs) > 0:
        print("\n" + "=" * 80)
        print("Detailed Analysis of First Run")
        print("=" * 80)

        first_run = runs[0]
        print(f"\nAnalyzing run: {first_run.name} ({first_run.id})")

        # Get history
        history = first_run.history()
        print(f"\nHistory shape: {history.shape}")
        print(f"Columns: {list(history.columns)}")

        if len(history) > 0:
            print("\nFirst few rows:")
            print(history.head())

            print("\nLast few rows:")
            print(history.tail())

            print("\nStatistics:")
            print(history.describe())

            # Save history to CSV
            history.to_csv('/home/user/workspace/run_history.csv', index=False)
            print("\nSaved full history to run_history.csv")

    print("\n" + "=" * 80)
    print("STEP 3: Checking for Artifacts")
    print("=" * 80)

    for i, run in enumerate(runs):
        print(f"\nRun {i+1}: {run.name}")
        artifacts = run.logged_artifacts()
        if artifacts:
            for artifact in artifacts:
                print(f"  Artifact: {artifact.name} (type: {artifact.type})")
        else:
            print("  No artifacts")

        # Check for files
        files = run.files()
        file_list = list(files)
        if file_list:
            print(f"  Files: {len(file_list)}")
            for f in file_list[:5]:  # Show first 5
                print(f"    - {f.name}")
        else:
            print("  No files")

    # Save comprehensive data
    print("\n" + "=" * 80)
    print("Saving Analysis Data")
    print("=" * 80)

    with open('/home/user/workspace/run_data.json', 'w') as f:
        json.dump(run_data, f, indent=2, default=str)
    print("Saved run data to run_data.json")

    print("\n" + "=" * 80)
    print("Analysis Complete!")
    print("=" * 80)

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
