using System;
using System.IO;
using System.Text;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using SolidWorks.Interop.sldworks;
using SolidWorks.Interop.swconst;

public static class SwDump {
  static string Esc(string s) { return s.Replace("\\", "\\\\").Replace("\"", "\\\""); }

  public static string Run(string asmPath, string outDir) {
    SldWorks sw = (SldWorks)Marshal.GetActiveObject("SldWorks.Application");
    int errs = 0, warns = 0;
    ModelDoc2 doc = sw.OpenDoc6(asmPath, (int)swDocumentTypes_e.swDocASSEMBLY,
      (int)swOpenDocOptions_e.swOpenDocOptions_Silent, "", ref errs, ref warns);
    if (doc == null) return "open failed " + errs;
    sw.ActivateDoc3(doc.GetTitle(), false, 0, ref errs);
    AssemblyDoc asm = (AssemblyDoc)doc;
    asm.ResolveAllLightWeightComponents(false);
    double[] asmColor = (double[])doc.MaterialPropertyValues;

    object[] comps = (object[])asm.GetComponents(false);
    BinaryWriter bin = new BinaryWriter(File.Create(Path.Combine(outDir, "parts.bin")));
    StringBuilder js = new StringBuilder("[\n");
    StringBuilder log = new StringBuilder();
    long offset = 0; bool first = true;

    foreach (object o in comps) {
      Component2 c = (Component2)o;
      object[] kids = (object[])c.GetChildren();
      string name = c.Name2;
      if (kids != null && kids.Length > 0) continue;
      if (c.IsSuppressed()) { log.AppendLine("SUPPRESSED " + name); continue; }
      if (c.IsHidden(true)) { log.AppendLine("HIDDEN " + name); continue; }

      object bodyInfo;
      object[] bodies = (object[])c.GetBodies3((int)swBodyType_e.swSolidBody, out bodyInfo);
      if (bodies == null) { log.AppendLine("NOBODY " + name); continue; }

      MathTransform xf = c.Transform2;
      double[] t = xf == null ? null : (double[])xf.ArrayData;

      double[] col = (double[])c.GetMaterialPropertyValues2((int)swInConfigurationOpts_e.swThisConfiguration, null);
      ModelDoc2 pd = (ModelDoc2)c.GetModelDoc2();
      double[] pcol = pd != null ? (double[])pd.MaterialPropertyValues : null;

      long triCount = 0;
      foreach (object bo in bodies) {
        Body2 b = (Body2)bo;
        double[] bcol = (double[])b.MaterialPropertyValues2;
        object[] faces = (object[])b.GetFaces();
        if (faces == null) continue;
        foreach (object fo in faces) {
          Face2 f = (Face2)fo;
          float[] tris = (float[])f.GetTessTriangles(true);
          if (tris == null) continue;
          double[] fcol = (double[])f.MaterialPropertyValues;
          double[] use = (fcol != null && fcol[0] >= 0) ? fcol : (bcol != null && bcol[0] >= 0) ? bcol : (col != null && col[0] >= 0) ? col : pcol;
          byte r = 200, g = 200, bb = 200;
          if (use != null && use[0] >= 0) { r = (byte)(use[0] * 255); g = (byte)(use[1] * 255); bb = (byte)(use[2] * 255); }
          for (int i = 0; i < tris.Length; i += 9) {
            for (int k = 0; k < 9; k++) bin.Write(tris[i + k]);
            bin.Write(r); bin.Write(g); bin.Write(bb); bin.Write((byte)255);
            triCount++;
          }
        }
      }
      if (triCount == 0) { log.AppendLine("NOTRIS " + name); continue; }
      if (!first) js.Append(",\n");
      first = false;
      js.Append("{\"name\":\"" + Esc(name) + "\",\"path\":\"" + Esc(c.GetPathName()) + "\",\"offset\":" + offset + ",\"tris\":" + triCount + ",\"xf\":[");
      if (t != null) for (int i = 0; i < t.Length; i++) js.Append((i > 0 ? "," : "") + t[i].ToString("R", System.Globalization.CultureInfo.InvariantCulture));
      js.Append("]}");
      offset += triCount * 40;
    }
    js.Append("\n]\n");
    bin.Close();
    File.WriteAllText(Path.Combine(outDir, "parts.json"), js.ToString());
    File.WriteAllText(Path.Combine(outDir, "skipped.log"), log.ToString());
    return "ok bytes=" + offset;
  }
}
