# AA Blender extensions

A Blender extension repository for AA workshops. Add it once and Blender installs and updates everything below from *Get Extensions*.

| Extension | What it does |
|---|---|
| **Interface Tour** | Step-by-step overlays: *Help > Interface Tour* (the parts of the window) and *Help > Object Basics Tour* (select, move/rotate/scale, Properties tabs, viewport shading). |
| **BlenderGIS** | Geographic data tools: basemaps, DEMs, OSM, QGIS projects. From [mnmly/BlenderGIS](https://github.com/mnmly/BlenderGIS) ([tutorial](https://github.com/mnmly/BlenderGIS/blob/master/docs/tutorial.md)). |
| **E57 Point Cloud Lite** | *File > Import > E57 Point Cloud (.e57)*, or drag an `.e57` laser scan into the viewport. Each scan becomes a point cloud object with its colors. Needs Blender 5.2. |
| **COPC Renderer** | Converts laser scans (E57, LAS/LAZ, PLY, …) to Cloud Optimized Point Clouds and displays even very large ones quickly in the viewport. Renders images and animations that include the points. Needs Blender 5.1, on an Apple Silicon Mac or Windows x64. |

Requires Blender 4.3 or newer (BlenderGIS needs 4.3; Interface Tour alone works from 4.2). E57 Point Cloud Lite needs Blender 5.2 or newer, and COPC Renderer needs 5.1 or newer on an Apple Silicon Mac or Windows x64; Blender doesn't list them elsewhere.

## Install

Step-by-step with screenshots: **[docs/tutorial.md](docs/tutorial.md)**.

1. *Edit > Preferences > System > Network*: tick **Allow Online Access**.
2. *Get Extensions*: click **Repositories** (top right) > **+** > **Add Remote Repository**, and paste:

   ```
   https://mnmly.github.io/aa-blender-extensions/index.json
   ```

   Tick **Check for Updates on Startup**, then **Create**.
3. In *Get Extensions*, search for **Interface Tour**, **BlenderGIS**, **E57 Point Cloud Lite** and **COPC Renderer**, and click **Install** on each. Blender picks the right BlenderGIS and COPC Renderer build for your platform.

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

## Using COPC Renderer

Open the 3D viewport sidebar (**N**) > **COPC** tab.

- **Convert to COPC:** pick one or more scans (E57, LAS/LAZ, PLY, …). They convert in the background (progress in the status bar, **Esc** cancels) to `.copc.laz` files next to the originals, then load into the scene. The converter is built in; nothing else to install.
- **Add COPC:** load existing `.copc.laz` files. Each cloud is an object you can move, rotate and hide.
- **Max Depth:** more depth shows more points (slower). **Reload** applies it.
- **Render Image / Animation**, also in the 3D view's **View** menu as *Viewport Render … (COPC)*: F12 renders and Blender's own Viewport Render don't show the points; these do. They render through the camera in camera view (Numpad 0), save to the output path, and open the folder. Meshes in front of a cloud hide the points behind it.
- Scans exported without registration each sit at their scanner's origin. Converting keeps them that way, so align them in your scanning software (or by moving the objects).

## Maintaining

- `extensions/<id>/`: one folder per extension, each with a `blender_manifest.toml`. Bump `version` there to publish an update.
- `extensions/io_import_e57/` is copied from [mnmly/blender-e57-point-cloud-lite](https://github.com/mnmly/blender-e57-point-cloud-lite), which has the tests. Change it there, then copy the three files over.
- `scripts/build_index.py`: zips every extension and writes `index.json`, merged with the entries of the upstream repositories listed in `UPSTREAM_INDEXES` (their archives stay hosted upstream).
- COPC Renderer ships native binaries per platform, so its zips aren't in `extensions/`. They and their `index.json` are assets of a `copc-renderer-v<version>` release of this repository. To update it, build them with `package_addon.py --index-url-base https://github.com/mnmly/aa-blender-extensions/releases/download/copc-renderer-v<version>` in the add-on's repo, upload them to that release, then bump the tag in `UPSTREAM_INDEXES`.
- `.github/workflows/publish.yml`: builds and deploys to GitHub Pages on every push to `main`, daily (to pick up new BlenderGIS releases), on demand (*Actions > Publish extension repository > Run workflow*), and on a `repository_dispatch` of type `upstream-release`.

Build locally: `python scripts/build_index.py _site` (Python 3.11+), then serve `_site/` and add `http://localhost:<port>/index.json` as a repository.

## License

GPL-3.0-or-later. BlenderGIS is © domlysz and contributors, GPL-3.0-or-later.
