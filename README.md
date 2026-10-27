# AA Blender extensions

A Blender extension repository for AA workshops. Add it once and Blender installs and updates everything below from *Get Extensions*.

| Extension | What it does |
|---|---|
| **Interface Tour** | Step-by-step overlays: *Help > Interface Tour* (the parts of the window) and *Help > Object Basics Tour* (select, move/rotate/scale, Properties tabs, viewport shading). |
| **BlenderGIS** | Geographic data tools: basemaps, DEMs, OSM, QGIS projects. From [mnmly/BlenderGIS](https://github.com/mnmly/BlenderGIS) ([tutorial](https://github.com/mnmly/BlenderGIS/blob/master/docs/tutorial.md)). |
| **E57 Point Cloud Lite** | *File > Import > E57 Point Cloud (.e57)*, or drag an `.e57` laser scan into the viewport. Each scan becomes a point cloud object with its colors. Needs Blender 5.2. |

Requires Blender 4.3 or newer (BlenderGIS needs 4.3; Interface Tour alone works from 4.2). E57 Point Cloud Lite needs Blender 5.2 or newer; older versions don't list it.

## Install

Step-by-step with screenshots: **[docs/tutorial.md](docs/tutorial.md)**.

1. *Edit > Preferences > System > Network*: tick **Allow Online Access**.
2. *Get Extensions*: click **Repositories** (top right) > **+** > **Add Remote Repository**, and paste:

   ```
   https://mnmly.github.io/aa-blender-extensions/index.json
   ```

   Tick **Check for Updates on Startup**, then **Create**.
3. In *Get Extensions*, search for **Interface Tour**, **BlenderGIS** and **E57 Point Cloud Lite** and click **Install** on each. Blender picks the right BlenderGIS build for Windows, macOS (Intel or Apple Silicon) or Linux.

Updates show up in *Get Extensions* with an **Update** button. Restart Blender after updating BlenderGIS.

Already installed BlenderGIS from its own repository or a zip? Uninstall it first, so you don't have two copies.

## Using the Interface Tour

Start it from *Help > Interface Tour* or *Help > Object Basics Tour*.

| Key | Action |
|---|---|
| Right Arrow / Space / Enter, or **Next** | Next step |
| Left Arrow / Backspace, or **Back** | Previous step |
| M | Open the manual page for the step |
| Esc | Exit |

Other keys keep working during the tour, so students can try G, R, S and Z as they read. The Object Basics tour switches the Properties tab and viewport shading to match each step, and restores the viewport shading when it ends.

## Using E57 Point Cloud Lite

*File > Import > E57 Point Cloud (.e57)*, or drag the file into the 3D viewport. Each file becomes a collection, and each scan in it a point cloud object.

- Colors show in *Material Preview* and *Rendered* shading. *Solid* shading draws point clouds in one flat color.
- Large scans: raise **Keep Every Nth Point** (e.g. 10) to import a lighter copy.
- **Recenter** (on by default) moves the first scan to the world origin so georeferenced scans stay precise. The shift is saved on the scene as `e57_origin`, and later imports reuse it, so scans from separate files still line up.
- **Point Radius** sets how big points render.

## Maintaining

- `extensions/<id>/`: one folder per extension, each with a `blender_manifest.toml`. Bump `version` there to publish an update.
- `extensions/io_import_e57/` is copied from its development repo (`bl_e57_importer`, which has the tests). Change it there, then copy the three files over.
- `scripts/build_index.py`: zips every extension and writes `index.json`, merged with the entries of the upstream repositories listed in `UPSTREAM_INDEXES` (their archives stay hosted upstream).
- `.github/workflows/publish.yml`: builds and deploys to GitHub Pages on every push to `main`, daily (to pick up new BlenderGIS releases), on demand (*Actions > Publish extension repository > Run workflow*), and on a `repository_dispatch` of type `upstream-release`.

Build locally: `python scripts/build_index.py _site` (Python 3.11+), then serve `_site/` and add `http://localhost:<port>/index.json` as a repository.

## License

GPL-3.0-or-later. BlenderGIS is © domlysz and contributors, GPL-3.0-or-later.
