from pathlib import Path
p = Path(r"C:\Users\suhan\Downloads\palmresearch---palmprint-biometrics-platform - Copy\frontend\src\pages\HomePage.tsx")
s = p.read_text()
old = """        <div className="mt-6 flex flex-wrap gap-3">
          <Link to="/upload" className="btn-primary">
            <Upload className="mr-2 h-4 w-4" />
            Upload a palmprint image
          </Link>
          <Link to="/dashboard" className="btn-secondary">
            Open the dashboard
          </Link>
        </div>"""
new = """        <div className="mt-6 flex flex-wrap gap-3">
          <Link to="/upload" className="btn-primary">
            <Upload className="mr-2 h-4 w-4" />
            Upload a palmprint image
          </Link>
          <Link to="/analysis" className="btn-secondary">
            <Scan className="mr-2 h-4 w-4" />
            Palmprint Analysis
          </Link>
          <Link to="/dashboard" className="btn-secondary">
            Open the dashboard
          </Link>
        </div>"""
if old in s:
    s2 = s.replace(old, new)
    p.write_text(s2)
    print("ok")
else:
    print("no")
