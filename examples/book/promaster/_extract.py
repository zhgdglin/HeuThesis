import pypdf, io, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
r = pypdf.PdfReader("715释放器项目总结报告.pdf")
out = []
for i, p in enumerate(r.pages):
    t = p.extract_text() or ""
    out.append("="*20 + f" PAGE {i+1} " + "="*20 + "\n" + t)
open("_report.txt","w",encoding="utf-8").write("\n".join(out))
print("written", sum(len(x) for x in out))
