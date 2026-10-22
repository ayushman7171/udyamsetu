
import ast
import json
from pathlib import Path

root = Path(__file__).resolve().parent
source = (root / "locations.py").read_text(encoding="utf-8")
tree = ast.parse(source)

locations = None
for node in tree.body:
    if isinstance(node, ast.Assign):
        if any(
            isinstance(target, ast.Name)
            and target.id == "INDIAN_LOCATIONS"
            for target in node.targets
        ):
            locations = ast.literal_eval(node.value)
            break

if not locations:
    raise RuntimeError("Could not find INDIAN_LOCATIONS in locations.py")

output = root / "js" / "locations-data.js"
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(
    "// Generated from locations.py\n"
    "window.INDIAN_LOCATIONS = "
    + json.dumps(locations, ensure_ascii=False, indent=2)
    + ";\n",
    encoding="utf-8",
)

print(f"Created {output} with {len(locations)} state/UT entries.")
