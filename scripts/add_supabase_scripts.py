import glob
import re

html_files = glob.glob("*.html")
print(f"Found {len(html_files)} HTML files: {html_files}")

supabase_scripts = """  <!-- Supabase Client SDK & Configuration (Vercel & Static Ready) -->
  <script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
  <script src="js/supabase-config.js"></script>
  <script src="js/supabase-client.js"></script>
  <script src="js/supabase-api.js"></script>
"""

updated = []
for hf in html_files:
    with open(hf, "r", encoding="utf-8") as f:
        content = f.read()
    if "js/supabase-config.js" in content:
        continue
    m = re.search(r"(\s*<script src=[\"']js/(?:data|i18n|main)\.js[\"']><\/script>)", content)
    if m:
        idx = m.start()
        new_content = content[:idx] + "\n" + supabase_scripts + content[idx:]
        with open(hf, "w", encoding="utf-8") as out:
            out.write(new_content)
        updated.append(hf)

print(f"Added Supabase scripts to {len(updated)} files: {updated}")
