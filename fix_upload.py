from pathlib import Path
p = Path(r"C:\Users\suhan\Downloads\palmresearch---palmprint-biometrics-platform - Copy\frontend\src\pages\UploadPage.tsx")
s = p.read_text()
old = "            <button type=\"button\" className=\"btn-primary\" onClick={() => navigate('/processing?image=' + uploaded.id)}>Process this image</button>"
new = "            <button type=\"button\" className=\"btn-primary\" onClick={() => navigate('/analysis?image=' + uploaded.id)}>Analyze this image</button>\n            <button type=\"button\" className=\"btn-secondary\" onClick={() => navigate('/processing?image=' + uploaded.id)}>Process this image</button>"
if old in s:
    p.write_text(s.replace(old, new))
    print("ok")
else:
    print("no")
