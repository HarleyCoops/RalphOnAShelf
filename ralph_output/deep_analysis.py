import wandb
import json
import pandas as pd
import numpy as np

# Initialize W&B API
api_key = "cee32d77c7edb39a3857ede1c44fa2c7d7f89bb1"
wandb.login(key=api_key)
api = wandb.Api()

entity = "christian-cooper-us"
project_name = "railroad-1959-tinker"

print("Getting the completed run...")
runs = api.runs(f"{entity}/{project_name}")

# Find the completed run
completed_run = None
for run in runs:
    if run.state == "finished":
        completed_run = run
        break

if completed_run:
    print(f"Analyzing completed run: {completed_run.name} ({completed_run.id})")

    # Get full config
    config = completed_run.config
    print("\n=== CONFIGURATION ===")
    for key, value in sorted(config.items()):
        print(f"{key}: {value}")

    # Get history with all metrics
    print("\nFetching run history...")
    history = completed_run.history(samples=10000)

    print(f"\nHistory shape: {history.shape}")
    print(f"Columns ({len(history.columns)}): {list(history.columns)[:20]}...")

    # Save full history
    history.to_csv('/home/user/workspace/full_run_history.csv', index=False)
    print("Saved full history to full_run_history.csv")

    # Analyze key metrics
    print("\n=== KEY METRICS ANALYSIS ===")

    # Get reward metrics
    reward_cols = [col for col in history.columns if 'reward' in col.lower()]
    print(f"\nReward metrics ({len(reward_cols)}):")
    for col in reward_cols[:10]:
        if col in history.columns and not history[col].isna().all():
            print(f"  {col}: min={history[col].min():.4f}, max={history[col].max():.4f}, mean={history[col].mean():.4f}")

    # Get ledger metrics
    ledger_cols = [col for col in history.columns if 'ledger' in col.lower()]
    print(f"\nLedger metrics ({len(ledger_cols)}):")
    for col in ledger_cols[:10]:
        if col in history.columns and not history[col].isna().all():
            print(f"  {col}: min={history[col].min():.4f}, max={history[col].max():.4f}, mean={history[col].mean():.4f}")

    # Get KL divergence metrics
    kl_cols = [col for col in history.columns if 'kl' in col.lower()]
    print(f"\nKL metrics ({len(kl_cols)}):")
    for col in kl_cols[:10]:
        if col in history.columns and not history[col].isna().all():
            print(f"  {col}: min={history[col].min():.4f}, max={history[col].max():.4f}, mean={history[col].mean():.4f}")

    # Get loss metrics
    loss_cols = [col for col in history.columns if 'loss' in col.lower()]
    print(f"\nLoss metrics ({len(loss_cols)}):")
    for col in loss_cols[:10]:
        if col in history.columns and not history[col].isna().all():
            print(f"  {col}: min={history[col].min():.4f}, max={history[col].max():.4f}, mean={history[col].mean():.4f}")

    # Get token metrics
    token_cols = [col for col in history.columns if 'token' in col.lower()]
    print(f"\nToken metrics ({len(token_cols)}):")
    for col in token_cols[:10]:
        if col in history.columns and not history[col].isna().all():
            print(f"  {col}: min={history[col].min():.4f}, max={history[col].max():.4f}, mean={history[col].mean():.4f}")

    # Summary statistics
    summary = completed_run.summary._json_dict

    # Save detailed analysis
    analysis = {
        'run_info': {
            'id': completed_run.id,
            'name': completed_run.name,
            'state': completed_run.state,
            'created': str(completed_run.created_at),
            'runtime': summary.get('_runtime', 0)
        },
        'config': config,
        'summary_metrics': {k: v for k, v in summary.items() if not k.startswith('_')},
        'history_stats': {
            'total_steps': len(history),
            'columns': list(history.columns)
        }
    }

    with open('/home/user/workspace/detailed_analysis.json', 'w') as f:
        json.dump(analysis, f, indent=2, default=str)

    print("\nSaved detailed analysis to detailed_analysis.json")

    print("\n=== ANALYSIS COMPLETE ===")
else:
    print("No completed run found!")
