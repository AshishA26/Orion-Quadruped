# CAD → GLB

Exports the full SolidWorks assembly (including internals the URDF leaves out) to a compact, meshopt-compressed GLB. This is the model behind the scroll-driven exploded view on [ashisha26.github.io/orion.html](https://ashisha26.github.io/orion.html).

## Requirements

- Windows with SOLIDWORKS installed (uses the .NET interop DLLs in `SOLIDWORKS\api\redist`)
- Node.js 18+

## Usage

```powershell
npm install

# 1. Tessellate every visible, unsuppressed component in models/Main_Assembly.SLDASM
#    -> export/parts.json + export/parts.bin   (~15 min, ~200 MB)
npm run export

# 2. Weld, decimate and compress into a GLB (default budget: 160k triangles)
npm run convert -- ../../../AshishA26.github.io/assets/models/orion.glb 160000
```

`export-assembly.ps1` accepts `-Assembly`, `-OutDir` and `-SwInstall` to point at a different assembly, output folder or SOLIDWORKS install.

## How it works

| File | Role |
|:--|:--|
| `SwDump.cs` | Compiled at runtime by PowerShell. Walks `AssemblyDoc.GetComponents`, skips hidden/suppressed parts, and writes each face's tessellation with its appearance colour (face → body → component → part priority) plus the component's `Transform2`. |
| `export-assembly.ps1` | Loads the interop DLLs, compiles `SwDump.cs`, starts SOLIDWORKS if needed and runs the dump. |
| `convert.mjs` | Moves each part into assembly space, welds vertices per colour, simplifies with meshoptimizer (budget shared by triangle count, small parts keep a minimum), and writes one glTF node per component named by its SolidWorks path, e.g. `Leg_Assembly_Left-1/Femur_Inside-2` (also in node `extras.name`). |

### `parts.bin` format

Per triangle, 40 bytes: 9 × float32 vertex positions in part space (metres), then RGBA as 4 × uint8. `parts.json` lists each component's `name`, `path`, byte `offset`, `tris` count and `xf` (SolidWorks `MathTransform.ArrayData`: rotation rows, translation, scale; points transform as `p * R + T`).

### Notes

- Hidden components (e.g. the neodymium magnets) are skipped; unhide them in the assembly before exporting if you want them included.
- The web page groups parts by these component names, so renaming parts in SOLIDWORKS may require updating the rules in `assets/js/orion-exploded.js` on the website.
