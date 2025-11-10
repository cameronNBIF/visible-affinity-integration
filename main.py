import questionary
from dotenv import load_dotenv
from typing import Dict

from affinity import (
    get_affinity_lists,
    get_affinity_list_entries,
    get_affinity_list_fields,
    update_affinity_field,
)
from utils import normalize_domain
from visible import get_visible_metric_names, fetch_visible_metric_data

load_dotenv()

# Interactive Selection Functions

def select_affinity_list() -> str:
    """Prompt user to select an Affinity list interactively."""
    print("\nFetching available Affinity lists...")
    all_lists = get_affinity_lists()

    if not all_lists:
        print("X No lists found in Affinity.")
        exit(1)

    # Build a mapping for easy reference
    choices = [
        questionary.Choice(title=f"{lst['name']} (ID: {lst['id']})", value=str(lst["id"]))
        for lst in all_lists
    ]

    list_id = questionary.select(
        "Select the Affinity list to sync:",
        choices=choices
    ).ask()

    print(f"\n✓ Selected list ID: {list_id}\n")
    return list_id


def select_affinity_field(list_id: str) -> Dict[str, str]:
    """Prompt user to select a field from the selected Affinity list."""
    print("\n" + "=" * 60)
    print(f"🧾 FETCHING FIELDS FOR AFFINITY LIST {list_id}")
    print("=" * 60)

    all_fields = get_affinity_list_fields(list_id)
    if not all_fields:
        print("X No fields found in this list.")
        exit(1)

    # Sort alphabetically for readability
    all_fields = sorted(all_fields, key=lambda f: f.get("name", "").lower())

    choices = [
        questionary.Choice(
            title=f"{f['name']}  (Type: {f.get('valueType', 'unknown')})",
            value={"id": f["id"], "name": f["name"]}
        )
        for f in all_fields
        if f.get("name")
    ]

    selected_field = questionary.select(
        "Select which Affinity field to update:",
        choices=choices
    ).ask()

    print(f"\n✓ Selected field: {selected_field['name']} (ID: {selected_field['id']})\n")
    return selected_field


def select_visible_metric_name() -> str:
    """Prompt user to select a metric name from Visible interactively."""
    print("\n" + "=" * 60)
    print("FETCHING AVAILABLE METRICS FROM VISIBLE")
    print("=" * 60)

    metric_names = get_visible_metric_names()
    if not metric_names:
        print("X No metrics found in Visible.")
        exit(1)

    metric_name = questionary.select(
        "Select which Visible metric to sync:",
        choices=metric_names
    ).ask()

    print(f"\n✓ Selected Visible metric: {metric_name}\n")
    return metric_name


# Main Pipeline

def sync_runway_data(
    dry_run: bool = True,
    list_id: str = None,
    metric_name: str = None,
    field_id: str = None,
    field_name: str = None
):
    """Main pipeline: sync Visible metric data into an Affinity field."""
    print("\n" + "=" * 60)
    print(" VISIBLE → AFFINITY SYNC PIPELINE")
    print("=" * 60)

    # Step 1: Fetch metric data from Visible
    visible_data = fetch_visible_metric_data(metric_name)
    if not visible_data:
        print("\nX No data found in Visible for the selected metric. Exiting.")
        return

    # Step 2: Fetch Affinity list entries
    print("\n" + "=" * 60)
    print("📋 FETCHING DATA FROM AFFINITY")
    print("=" * 60)

    affinity_entries = get_affinity_list_entries(list_id)
    print(f"✓ Retrieved {len(affinity_entries)} entries from Affinity list")

    print(f"✓ Updating Affinity field: '{field_name}' (ID: {field_id})")

    # Step 3: Match companies by domain
    print("\n" + "=" * 60)
    print(" MATCHING COMPANIES BY DOMAIN")
    print("=" * 60)

    matches = []
    unmatched_visible = set(visible_data.keys())
    unmatched_affinity = []

    for entry in affinity_entries:
        company_name = entry.get("entity", {}).get("name", "Unknown")
        domains = entry.get("entity", {}).get("domains", [])
        list_entry_id = entry.get("id")

        matched = False
        for domain in domains:
            normalized = normalize_domain(domain)
            if normalized in visible_data:
                metric_value = visible_data[normalized]
                matches.append({
                    "company_name": company_name,
                    "list_entry_id": list_entry_id,
                    "domain": normalized,
                    "metric_value": metric_value
                })
                unmatched_visible.discard(normalized)
                matched = True
                print(f"  ✓ Matched: {company_name:35} → {metric_value:6.1f}")
                break

        if not matched and domains:
            unmatched_affinity.append((company_name, domains))

    print(f"\n MATCHING SUMMARY:")
    print(f"  ✓ Matched: {len(matches)} companies")
    print(f"  !  {len(unmatched_visible)} companies in Visible not in Affinity")
    print(f"  !  {len(unmatched_affinity)} companies in Affinity not in Visible")

    if unmatched_affinity:
        print("\n  Companies in Affinity without Visible data:")
        for name, domains in unmatched_affinity[:10]:
            print(f"    - {name:35} ({', '.join(domains[:2])})")
        if len(unmatched_affinity) > 10:
            print(f"    ... and {len(unmatched_affinity) - 10} more")

    # Step 4: Update Affinity (or simulate)
    if dry_run:
        print("\n" + "=" * 60)
        print("🔍 DRY RUN MODE - No updates will be made")
        print("   Set dry_run=False to perform actual updates")
        print("=" * 60)
        print("\n📝 Would update the following companies:")
        for match in matches:
            print(f"  - {match['company_name']:35} → {match['metric_value']:6.1f}")
    else:
        print("\n" + "=" * 60)
        print("  UPDATING AFFINITY")
        print("=" * 60)

        success_count = 0
        failed_count = 0

        for match in matches:
            print(f"  Updating {match['company_name']:35} → {match['metric_value']:6.1f}...", end="")
            success = update_affinity_field(
                list_id=list_id,
                list_entry_id=match["list_entry_id"],
                field_id=field_id,
                value=match["metric_value"]
            )

            if success:
                print(" ✓")
                success_count += 1
            else:
                failed_count += 1

        print(f"\n UPDATE SUMMARY:")
        print(f"  ✓ Successfully updated: {success_count}/{len(matches)}")
        print(f"  X Failed updates: {failed_count}/{len(matches)}")

    print("\n" + "=" * 60)
    print(" Pipeline execution complete!")
    print("=" * 60)

if __name__ == "__main__":
    selected_list_id = select_affinity_list()
    selected_field = select_affinity_field(selected_list_id)
    selected_metric_name = select_visible_metric_name()

    sync_runway_data(
        dry_run=True,  # Change to False to push updates
        list_id=selected_list_id,
        metric_name=selected_metric_name,
        field_id=selected_field["id"],
        field_name=selected_field["name"]
    )
