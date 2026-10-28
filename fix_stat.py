from pathlib import Path
p = Path(r"C:\Users\suhan\Downloads\palmresearch---palmprint-biometrics-platform - Copy\frontend\src\components\dashboard\StatCard.tsx")
s = p.read_text()
s = s.replace("import type { LucideIcon } from 'lucide-react'", "// lucide types removed")
s = s.replace("  icon: LucideIcon", "  icon: any")
p.write_text(s)
print("ok")
