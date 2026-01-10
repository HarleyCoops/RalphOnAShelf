import wandb
from datetime import datetime

# Login with API key
api_key = "cee32d77c7edb39a3857ede1c44fa2c7d7f89bb1"
wandb.login(key=api_key)

# Initialize API
api = wandb.Api()

# Get username/entity name
print("=" * 60)
print("WEIGHTS & BIASES ACCOUNT INFORMATION")
print("=" * 60)

# Get user info
user = api.viewer
print(f"\nUsername/Entity: {user.username}")
print(f"Display Name: {getattr(user, 'name', 'N/A')}")
print(f"Email: {getattr(user, 'email', 'N/A')}")

# List all projects
print("\n" + "=" * 60)
print("PROJECTS")
print("=" * 60)

try:
    entity_name = user.username
    projects = api.projects(entity=entity_name)

    project_list = []
    for project in projects:
        project_list.append(project)

    if project_list:
        print(f"\nTotal Projects: {len(project_list)}")
        for idx, project in enumerate(project_list, 1):
            print(f"\n{idx}. Project: {project.name}")
            print(f"   Entity: {project.entity}")
    else:
        print("\nNo projects found.")
except Exception as e:
    print(f"\nError fetching projects: {e}")

# List recent runs across all projects
print("\n" + "=" * 60)
print("RECENT RUNS (Last 10)")
print("=" * 60)

try:
    all_runs = []

    # Get runs from all projects
    if project_list:
        for project in project_list:
            try:
                runs = api.runs(f"{project.entity}/{project.name}", per_page=50)
                for run in runs:
                    all_runs.append(run)
            except Exception as e:
                print(f"Error fetching runs from {project.name}: {e}")

    if all_runs:
        # Sort by created_at timestamp
        all_runs.sort(key=lambda x: x.created_at if hasattr(x, 'created_at') else '', reverse=True)

        # Show last 10 runs
        recent_runs = all_runs[:10]

        print(f"\nTotal Runs Found: {len(all_runs)}")
        print(f"Showing Most Recent: {len(recent_runs)}")

        for idx, run in enumerate(recent_runs, 1):
            print(f"\n{idx}. Run: {run.name}")
            print(f"   ID: {run.id}")
            print(f"   Project: {run.project}")
            print(f"   State: {run.state}")
            print(f"   Created: {run.created_at}")
            if hasattr(run, 'updated_at'):
                print(f"   Updated: {run.updated_at}")

        # Find last activity
        print("\n" + "=" * 60)
        print("LAST ACTIVITY")
        print("=" * 60)

        most_recent_run = all_runs[0]
        print(f"\nLast Activity (Most Recent Run):")
        print(f"  Run Name: {most_recent_run.name}")
        print(f"  Project: {most_recent_run.project}")
        print(f"  Created At: {most_recent_run.created_at}")
        if hasattr(most_recent_run, 'updated_at'):
            print(f"  Updated At: {most_recent_run.updated_at}")
        print(f"  State: {most_recent_run.state}")

    else:
        print("\nNo runs found in any project.")
        print("\n" + "=" * 60)
        print("LAST ACTIVITY")
        print("=" * 60)
        print("\nNo activity found - no runs have been created yet.")

except Exception as e:
    print(f"\nError fetching runs: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("QUERY COMPLETE")
print("=" * 60)
