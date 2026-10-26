# SPDX-License-Identifier: GPL-3.0-or-later
"""Interface Tour: a step-by-step overlay that explains Blender's GUI.

Start it from Help > Interface Tour (or F3 > "Interface Tour").
Keys: Right / Space / Enter = next, Left / Backspace = back, M = open manual, Esc = exit.
"""

bl_info = {
    "name": "Interface Tour",
    "author": "mnmly",
    "version": (1, 1, 0),
    "blender": (3, 6, 0),
    "location": "Help > Interface Tour",
    "description": "Step-by-step overlay explaining the parts of Blender's interface",
    "category": "Interface",
}

import math

import bpy
import blf
import gpu
from gpu_extras.batch import batch_for_shader

MANUAL = "https://docs.blender.org/manual/en/latest/"


# ---------------------------------------------------------------------------
# Targets: each returns a list of window-space rects (x0, y0, x1, y1), or None
# when the element isn't visible in the current workspace.
# ---------------------------------------------------------------------------

def _area_rect(area):
    return (area.x, area.y, area.x + area.width, area.y + area.height)


def _region_rect(region):
    return (region.x, region.y, region.x + region.width, region.y + region.height)


def _find_area(screen, area_type, ui_type=None):
    areas = [
        a for a in screen.areas
        if a.type == area_type and (ui_type is None or a.ui_type == ui_type)
    ]
    return max(areas, key=lambda a: a.width * a.height, default=None)


def _find_region(area, *region_types):
    if area is None:
        return []
    return [
        r for r in area.regions
        if r.type in region_types and r.width > 1 and r.height > 1
    ]


def target_area(area_type, ui_type=None):
    def fn(screen):
        area = _find_area(screen, area_type, ui_type)
        return [_area_rect(area)] if area else None
    return fn


def target_view3d_regions(*region_types):
    def fn(screen):
        regions = _find_region(_find_area(screen, 'VIEW_3D'), *region_types)
        return [_region_rect(r) for r in regions] or None
    return fn


def target_all_editors(screen):
    return [_area_rect(a) for a in screen.areas] or None


def _window_pixel_size(screen):
    """Window size in region pixels. `Window.width/height` are in OS points,
    which differ from region pixels on HiDPI displays, so infer the size from
    the areas, which are inset symmetrically from the window edges."""
    window = bpy.context.window
    x0 = min(a.x for a in screen.areas)
    x1 = max(a.x + a.width for a in screen.areas)
    factor = (x1 + x0) / window.width
    return x1 + x0, round(window.height * factor)


def global_bars(screen):
    """The Topbar and Status Bar are "global areas": they aren't part of
    `screen.areas`, so derive their rects from the space the screen leaves free."""
    width, height = _window_pixel_size(screen)
    y0 = min(a.y for a in screen.areas)
    y1 = max(a.y + a.height for a in screen.areas)
    gap = y0 if y0 < 8 else 0  # area edges are inset a few pixels from the window
    topbar = (0, y1 + gap, width, height) if height - y1 > 12 else None
    statusbar = (0, 0, width, y0 - gap) if y0 > 12 else None
    return topbar, statusbar


def target_topbar(screen):
    topbar = global_bars(screen)[0]
    return [topbar] if topbar else None


def target_statusbar(screen):
    statusbar = global_bars(screen)[1]
    return [statusbar] if statusbar else None


def target_timeline(screen):
    area = _find_area(screen, 'DOPESHEET_EDITOR', 'TIMELINE') or _find_area(screen, 'TIMELINE')
    return [_area_rect(area)] if area else None


# ---------------------------------------------------------------------------
# Steps
# ---------------------------------------------------------------------------

INTERFACE_STEPS = (
    dict(
        title="Welcome to Blender",
        body="This short tour points out the main parts of the interface. "
             "Use Right Arrow / Space to continue, Left Arrow to go back, "
             "M to open the manual page for a step, and Esc to exit.",
        target=None,
        url="interface/index.html",
    ),
    dict(
        title="Topbar",
        body="The strip at the very top holds the main menus (File, Edit, Render, Window, Help), "
             "the workspace tabs, and the active Scene and View Layer selectors.",
        target=target_topbar,
        url="interface/window_system/topbar.html",
    ),
    dict(
        title="Workspaces",
        body="The tabs in the Topbar (Layout, Modeling, Sculpting, Shading, Animation, ...) are "
             "workspaces: predefined window layouts tuned for one task. Each has its own set of "
             "editors. Switch with a click or Ctrl+PageUp / Ctrl+PageDown.",
        target=target_topbar,
        url="interface/window_system/workspaces.html",
    ),
    dict(
        title="Areas & Editors",
        body="The window is divided into rectangular areas. Each area shows one editor, which you "
             "can change from the editor-type menu in its top-left corner. Drag a border to resize, "
             "drag from a corner to split or join, and press Ctrl+Space to maximize.",
        target=target_all_editors,
        url="interface/window_system/areas.html",
    ),
    dict(
        title="3D Viewport",
        body="The main editor for looking at and working with your scene. "
             "Middle-mouse drag orbits, Shift+middle pans, scroll wheel zooms. "
             "Numpad keys jump to front / side / top views.",
        target=target_area('VIEW_3D'),
        missing="This workspace has no 3D Viewport.",
        url="editors/3dview/index.html",
    ),
    dict(
        title="Header",
        body="Every editor has a header. In the 3D Viewport it holds the mode selector "
             "(Object, Edit, Sculpt, ...), the View / Select / Add / Object menus, "
             "and the viewport shading buttons on the right.",
        target=target_view3d_regions('HEADER', 'TOOL_HEADER'),
        missing="The 3D Viewport header is hidden. Show it from View > Header.",
        url="interface/window_system/regions.html#header",
    ),
    dict(
        title="Toolbar",
        body="The Toolbar on the left holds interactive tools: Select, Move, Rotate, Scale, "
             "Annotate, Measure and more. Toggle it with T.",
        target=target_view3d_regions('TOOLS'),
        missing="The Toolbar is hidden. Hover the 3D Viewport and press T to show it.",
        url="interface/window_system/regions.html#toolbar",
    ),
    dict(
        title="Sidebar",
        body="The Sidebar on the right shows the active object's transform, view settings and "
             "add-on panels, organized in vertical tabs. Toggle it with N.",
        target=target_view3d_regions('UI'),
        missing="The Sidebar is hidden. Hover the 3D Viewport and press N to show it, "
                "then go back and forth to refresh this step.",
        url="interface/window_system/regions.html#sidebar",
    ),
    dict(
        title="Outliner",
        body="The Outliner is the scene tree: every collection, object and data-block in a "
             "hierarchy. Click to select, double-click to rename, use the eye icon to hide.",
        target=target_area('OUTLINER'),
        missing="This workspace has no Outliner.",
        url="editors/outliner/index.html",
    ),
    dict(
        title="Properties Editor",
        body="Settings for the active data. The vertical tabs on its left switch between Render, "
             "Output, Scene, World, Object, Modifiers, Material and more.",
        target=target_area('PROPERTIES'),
        missing="This workspace has no Properties editor.",
        url="editors/properties_editor.html",
    ),
    dict(
        title="Timeline",
        body="The Timeline shows the current frame and the scene's frame range, with playback "
             "controls. Space plays / pauses the animation; I inserts a keyframe.",
        target=target_timeline,
        missing="This workspace has no Timeline.",
        url="editors/timeline.html",
    ),
    dict(
        title="Status Bar",
        body="The bottom bar shows mouse and keyboard hints for the current context on the left, "
             "and scene statistics, memory and the Blender version on the right.",
        target=target_statusbar,
        url="interface/window_system/status_bar.html",
    ),
    dict(
        title="That's the tour!",
        body="Restart it any time from Help > Interface Tour. Next, try Help > Object Basics Tour "
             "to learn how to move objects and change how they look.",
        target=None,
        url="interface/index.html",
    ),
)


def show_properties_tab(tab):
    """Switch the Properties editor to `tab` so the step shows what it describes."""
    def fn(screen):
        area = _find_area(screen, 'PROPERTIES')
        if area is None:
            return
        try:
            area.spaces.active.context = tab
        except TypeError:
            pass  # tab not available, e.g. no active object
    return fn


def target_properties_tabs(screen):
    """The vertical tab column on the left of the Properties editor."""
    area = _find_area(screen, 'PROPERTIES')
    if area is None:
        return None
    regions = _find_region(area, 'NAVIGATION_BAR')
    return [_region_rect(regions[0])] if regions else [_area_rect(area)]


def target_shading_buttons(screen):
    """Approximate rect of the shading buttons at the right end of the 3D Viewport
    header; the Python API doesn't expose button positions."""
    regions = _find_region(_find_area(screen, 'VIEW_3D'), 'HEADER')
    if not regions:
        return None
    x0, y0, x1, y1 = _region_rect(regions[0])
    s = _ui_scale()
    return [(x1 - 104 * s, y0, x1 - 12 * s, y1)]


def _view3d_space(screen):
    area = _find_area(screen, 'VIEW_3D')
    return area.spaces.active if area else None


def set_shading(shading_type, xray=False):
    """Switch the 3D Viewport's shading so the step shows what it describes."""
    def fn(screen):
        space = _view3d_space(screen)
        if space is None:
            return
        space.shading.type = shading_type
        if shading_type == 'WIREFRAME':
            space.shading.show_xray_wireframe = xray
        else:
            space.shading.show_xray = xray
    return fn


def _shading_snapshot(screen):
    space = _view3d_space(screen)
    if space is None:
        return None
    sh = space.shading
    return (space, sh.type, sh.show_xray, sh.show_xray_wireframe)


def _restore_shading(snapshot):
    if snapshot is None:
        return
    space, shading_type, xray, xray_wireframe = snapshot
    try:
        space.shading.type = shading_type
        space.shading.show_xray = xray
        space.shading.show_xray_wireframe = xray_wireframe
    except ReferenceError:
        pass  # the area was closed during the tour


OBJECT_STEPS = (
    dict(
        title="Object Basics",
        body="This tour covers selecting, moving, rotating and scaling objects, and changing how "
             "they look in the Properties editor. Shortcuts work while the mouse is over the "
             "3D Viewport, and you can try each one while the tour is open.",
        target=None,
        url="scene_layout/object/index.html",
    ),
    dict(
        title="Select",
        body="Left-click an object to select it (try the Cube). Shift+click adds to the selection, "
             "A selects all, Alt+A deselects all. The last-clicked object is the active one, "
             "drawn with a lighter outline.",
        target=target_area('VIEW_3D'),
        missing="This workspace has no 3D Viewport.",
        url="scene_layout/object/selecting.html",
    ),
    dict(
        title="Move: G",
        body="Press G (grab) and move the mouse; click or press Enter to confirm, right-click or "
             "Esc to cancel. Press X, Y or Z afterwards to lock to an axis, and type a number for "
             "an exact distance: G X 2 Enter moves 2 m along X.",
        target=target_area('VIEW_3D'),
        missing="This workspace has no 3D Viewport.",
        url="scene_layout/object/editing/transform/move.html",
    ),
    dict(
        title="Rotate: R",
        body="Press R and move the mouse around the object. Like Move, add an axis and a number: "
             "R Z 45 Enter turns the object 45 degrees around the vertical axis. "
             "Pressing R twice switches to free trackball rotation.",
        target=target_area('VIEW_3D'),
        missing="This workspace has no 3D Viewport.",
        url="scene_layout/object/editing/transform/rotate.html",
    ),
    dict(
        title="Scale: S",
        body="Press S and move the mouse towards or away from the object. S 2 Enter doubles its "
             "size; S Z 0.5 Enter halves its height. Shift+Z locks the Z axis and scales X and Y.",
        target=target_area('VIEW_3D'),
        missing="This workspace has no 3D Viewport.",
        url="scene_layout/object/editing/transform/scale.html",
    ),
    dict(
        title="Undo & Reset",
        body="Ctrl+Z undoes, Shift+Ctrl+Z redoes. Alt+G, Alt+R and Alt+S clear the location, "
             "rotation and scale back to their defaults.",
        target=target_area('VIEW_3D'),
        missing="This workspace has no 3D Viewport.",
        url="scene_layout/object/editing/transform/clear_apply.html",
    ),
    dict(
        title="Transform Tools",
        body="The same actions are available as tools with on-screen handles (gizmos): Move, "
             "Rotate, Scale and Transform. Pick one here, then drag the colored handles.",
        target=target_view3d_regions('TOOLS'),
        missing="The Toolbar is hidden. Hover the 3D Viewport and press T to show it.",
        url="scene_layout/object/tools/index.html",
    ),
    dict(
        title="Object Properties",
        body="Click the orange square tab in the Properties editor's tab column. It holds the "
             "active object's settings: exact Location, Rotation and Scale values, parenting, "
             "collections and visibility. Drag a field, or double-click to type a value.",
        target=target_properties_tabs,
        reveal=target_area('PROPERTIES'),
        icon='OBJECT',
        on_enter=show_properties_tab('OBJECT'),
        missing="This workspace has no Properties editor.",
        url="editors/properties_editor.html",
    ),
    dict(
        title="Object Data Properties",
        body="Click the green tab to edit the object's data. Its icon changes with the object "
             "type (this one is a mesh). For a mesh it holds vertex groups, shape keys and UV "
             "maps; for a light, its color and power; for a camera, its lens.",
        target=target_properties_tabs,
        reveal=target_area('PROPERTIES'),
        icon='DATA',
        on_enter=show_properties_tab('DATA'),
        missing="This workspace has no Properties editor.",
        url="editors/properties_editor.html",
    ),
    dict(
        title="Material Properties",
        body="Click the red sphere tab to control appearance. Click New to add a material, then "
             "change Base Color, Metallic and Roughness. Objects that share a material all "
             "update together.",
        target=target_properties_tabs,
        reveal=target_area('PROPERTIES'),
        icon='MATERIAL',
        on_enter=show_properties_tab('MATERIAL'),
        missing="This workspace has no Properties editor.",
        url="render/materials/assignment.html",
    ),
    dict(
        title="Viewport Shading",
        body="The four sphere buttons at the right end of the 3D Viewport header change how the "
             "scene is drawn. Press Z over the viewport for a pie menu with all of them. The next "
             "steps switch modes for you; your setting comes back when the tour ends.",
        target=target_shading_buttons,
        reveal=target_area('VIEW_3D'),
        missing="The 3D Viewport header is hidden. Show it from View > Header.",
        url="editors/3dview/display/shading.html",
    ),
    dict(
        title="Wireframe",
        body="Draws only the edges of each object. Handy for seeing the structure of a mesh and "
             "what's hidden behind it. Shift+Z toggles Wireframe on and off.",
        target=target_shading_buttons,
        reveal=target_area('VIEW_3D'),
        on_enter=set_shading('WIREFRAME'),
        missing="The 3D Viewport header is hidden. Show it from View > Header.",
        url="editors/3dview/display/shading.html#wireframe",
    ),
    dict(
        title="Solid",
        body="The default: fast, simply lit surfaces for modeling. The small arrow next to the "
             "buttons opens options: Lighting (Studio, MatCap, Flat) and Color (Material, Object, "
             "Random, ...).",
        target=target_shading_buttons,
        reveal=target_area('VIEW_3D'),
        on_enter=set_shading('SOLID'),
        missing="The 3D Viewport header is hidden. Show it from View > Header.",
        url="editors/3dview/display/shading.html#solid",
    ),
    dict(
        title="X-Ray",
        body="Alt+Z makes surfaces see-through, so you can view and box-select objects or "
             "vertices hidden behind others. Its button sits just left of the shading buttons; "
             "the strength is set in the shading options.",
        target=target_shading_buttons,
        reveal=target_area('VIEW_3D'),
        on_enter=set_shading('SOLID', xray=True),
        missing="The 3D Viewport header is hidden. Show it from View > Header.",
        url="editors/3dview/display/shading.html#x-ray",
    ),
    dict(
        title="Material Preview",
        body="Shows your materials lit by a built-in studio HDRI, using EEVEE. Use it to judge "
             "colors and surfaces without setting up any lights.",
        target=target_shading_buttons,
        reveal=target_area('VIEW_3D'),
        on_enter=set_shading('MATERIAL'),
        missing="The 3D Viewport header is hidden. Show it from View > Header.",
        url="editors/3dview/display/shading.html#material-preview",
    ),
    dict(
        title="Rendered",
        body="A live preview with the scene's render engine (set in Render Properties), its "
             "lights and world. Closest to the final image, but the slowest, especially with "
             "Cycles. Switch back to Solid while modeling.",
        target=target_shading_buttons,
        reveal=target_area('VIEW_3D'),
        on_enter=set_shading('RENDERED'),
        missing="The 3D Viewport header is hidden. Show it from View > Header.",
        url="editors/3dview/display/shading.html#rendered",
    ),
    dict(
        title="You're ready!",
        body="Summary: G move, R rotate, S scale, add X/Y/Z and a number for precision, "
             "Ctrl+Z to undo, Z to change shading, Alt+Z for X-Ray. "
             "Restart from Help > Object Basics Tour.",
        target=None,
        url="scene_layout/object/index.html",
    ),
)

TOURS = {
    'INTERFACE': ("Interface Tour", INTERFACE_STEPS),
    'OBJECTS': ("Object Basics Tour", OBJECT_STEPS),
}


# ---------------------------------------------------------------------------
# Tour state (one tour at a time)
# ---------------------------------------------------------------------------

class TourState:
    def __init__(self):
        self.active = False
        self.window_ptr = 0
        self.steps = INTERFACE_STEPS
        self.step = 0
        self.layout = None      # last computed tooltip layout, used for hit-testing
        self.shading = None     # viewport shading to restore when the tour ends
        self.signature = None   # used to detect layout changes and trigger redraws

    def current(self):
        return self.steps[self.step]


_state = TourState()
_handlers = []

COL_DIM = (0.0, 0.0, 0.0, 0.55)
# The 3D Viewport blends its overlay in linear color space, so it needs a
# stronger alpha to look as dark as the other editors.
COL_DIM_VIEW3D = (0.0, 0.0, 0.0, 0.78)
COL_ACCENT = (1.0, 0.55, 0.12, 1.0)
COL_GLOW = (1.0, 0.55, 0.12, 0.25)
COL_BOX = (0.11, 0.11, 0.11, 0.97)
COL_BTN = (0.24, 0.24, 0.24, 1.0)
COL_TEXT = (0.92, 0.92, 0.92, 1.0)
COL_SUBTLE = (0.6, 0.6, 0.6, 1.0)


def _ui_scale():
    return bpy.context.preferences.system.ui_scale


def _set_font_size(font_id, size):
    try:
        blf.size(font_id, size)
    except TypeError:  # Blender < 3.4 needs dpi
        blf.size(font_id, int(size), 72)


def _resolve_holes(screen):
    step = _state.current()
    target = step["target"]
    if target is None:
        return [], False
    rects = target(screen)
    if rects is None:
        return [], True
    return rects, False


def _bbox(rects):
    return (
        min(r[0] for r in rects), min(r[1] for r in rects),
        max(r[2] for r in rects), max(r[3] for r in rects),
    )


def _wrap(text, width, font_id):
    lines, line = [], ""
    for word in text.split():
        candidate = f"{line} {word}" if line else word
        if blf.dimensions(font_id, candidate)[0] <= width or not line:
            line = candidate
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def _compute_layout(screen):
    s = _ui_scale()
    font = 0
    holes, missing = _resolve_holes(screen)
    step = _state.current()

    pad = 16 * s
    box_w = 380 * s
    title_size, body_size, foot_size = 17 * s, 13 * s, 12 * s
    line_h = body_size * 1.45
    btn_h = 26 * s
    btn_w = 80 * s

    text = step["body"]
    if missing:
        text = step.get("missing", "Not visible in this workspace.")
    _set_font_size(font, body_size)
    lines = _wrap(text, box_w - 2 * pad, font)

    icon_size = 44 * s if step.get("icon") else 0
    head_h = max(title_size, icon_size)
    box_h = pad + head_h + 12 * s + len(lines) * line_h + 12 * s + btn_h + pad

    win_w, win_h = _window_pixel_size(screen)
    margin = 12 * s
    gap = 18 * s
    # Blender draws area borders over overlays, so the box has to stay inside a
    # single area. This also keeps it out of the topbar and status bar, which
    # aren't in `screen.areas` and can't be drawn over.
    areas = sorted((_area_rect(a) for a in screen.areas),
                   key=lambda r: (r[2] - r[0]) * (r[3] - r[1]), reverse=True)

    def clamp(v, lo, hi):
        return min(max(v, lo), hi)

    def settle(x, y):
        """Clamp the box into the area under its centre, falling back to the
        largest area. Returns None if neither can hold it."""
        cx, cy = x + box_w / 2, y + box_h / 2
        under = [a for a in areas if a[0] <= cx <= a[2] and a[1] <= cy <= a[3]]
        for a in under + areas[:1]:
            lo_x, hi_x = a[0] + margin, a[2] - margin - box_w
            lo_y, hi_y = a[1] + margin, a[3] - margin - box_h
            if lo_x <= hi_x and lo_y <= hi_y:
                return clamp(x, lo_x, hi_x), clamp(y, lo_y, hi_y)
        return None

    def clear_of(rects, pos):
        x, y = pos
        return not any(x < r[2] and x + box_w > r[0] and y < r[3] and y + box_h > r[1]
                       for r in rects)

    pos = None
    if holes:
        b = _bbox(holes)
        beside = (
            (b[2] + gap, b[3] - box_h),         # right
            (b[0] - gap - box_w, b[3] - box_h), # left
        )
        stacked = (
            (b[0], b[1] - gap - box_h),         # below
            (b[0], b[3] + gap),                 # above
        )
        # Short strips (headers, bars) read best with the tooltip under or over
        # them; beside them it would cover the rest of the strip.
        short = (b[3] - b[1]) < box_h / 2
        for candidate in (stacked + beside if short else beside + stacked):
            settled = settle(*candidate)
            if settled and clear_of(holes, settled):
                pos = settled
                break
        if pos is None:  # large target: tuck into its bottom-right corner, away from the scene
            big = max(holes, key=lambda r: (r[2] - r[0]) * (r[3] - r[1]))
            pos = settle(big[2] - gap - box_w, big[1] + gap)
    if pos is None:
        pos = settle((win_w - box_w) / 2, (win_h - box_h) / 2) or (margin, margin)
    x, y = pos

    last = _state.step == len(_state.steps) - 1
    next_btn = (x + box_w - pad - btn_w, y + pad, x + box_w - pad, y + pad + btn_h)
    back_btn = (next_btn[0] - 8 * s - btn_w, y + pad, next_btn[0] - 8 * s, y + pad + btn_h)

    return dict(
        holes=holes,
        reveal=(step["reveal"](screen) or []) if step.get("reveal") else [],
        icon=step.get("icon"), icon_size=icon_size, head_h=head_h,
        box=(x, y, x + box_w, y + box_h),
        pad=pad, s=s,
        title=step["title"], title_size=title_size,
        lines=lines, body_size=body_size, line_h=line_h,
        foot_size=foot_size,
        counter=f"{_state.step + 1} / {len(_state.steps)}",
        next_btn=next_btn, next_label="Finish" if last else "Next",
        back_btn=back_btn if _state.step > 0 else None,
    )


# ---------------------------------------------------------------------------
# Drawing. Every region of every editor draws its own slice of one shared,
# window-space overlay; the GPU clips each slice to its region.
# ---------------------------------------------------------------------------

def _shader():
    try:
        return gpu.shader.from_builtin('UNIFORM_COLOR')
    except ValueError:
        return gpu.shader.from_builtin('2D_UNIFORM_COLOR')


def _subtract(rect, holes):
    """Split `rect` into cells that don't overlap any of `holes`."""
    xs = sorted({rect[0], rect[2], *(min(max(v, rect[0]), rect[2]) for h in holes for v in (h[0], h[2]))})
    ys = sorted({rect[1], rect[3], *(min(max(v, rect[1]), rect[3]) for h in holes for v in (h[1], h[3]))})
    cells = []
    for x0, x1 in zip(xs, xs[1:]):
        for y0, y1 in zip(ys, ys[1:]):
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            if not any(h[0] <= cx <= h[2] and h[1] <= cy <= h[3] for h in holes):
                cells.append((x0, y0, x1, y1))
    return cells


def _frame(rect, width):
    x0, y0, x1, y1 = rect
    return [
        (x0 - width, y0 - width, x1 + width, y0),
        (x0 - width, y1, x1 + width, y1 + width),
        (x0 - width, y0, x0, y1),
        (x1, y0, x1 + width, y1),
    ]


def _draw_rects(shader, rects, color, ox, oy):
    if not rects:
        return
    verts, indices = [], []
    for x0, y0, x1, y1 in rects:
        i = len(verts)
        verts += [(x0 - ox, y0 - oy), (x1 - ox, y0 - oy), (x1 - ox, y1 - oy), (x0 - ox, y1 - oy)]
        indices += [(i, i + 1, i + 2), (i, i + 2, i + 3)]
    batch = batch_for_shader(shader, 'TRIS', {"pos": verts}, indices=indices)
    shader.bind()
    shader.uniform_float("color", color)
    batch.draw(shader)


def _draw_tris(shader, tris, color, ox, oy):
    if not tris:
        return
    verts = [(px - ox, py - oy) for tri in tris for px, py in tri]
    batch = batch_for_shader(shader, 'TRIS', {"pos": verts})
    shader.bind()
    shader.uniform_float("color", color)
    batch.draw(shader)


def _quad_tris(x0, y0, x1, y1):
    return [((x0, y0), (x1, y0), (x1, y1)), ((x0, y0), (x1, y1), (x0, y1))]


def _segment_tris(p, q, width):
    dx, dy = q[0] - p[0], q[1] - p[1]
    length = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / length * width / 2, dx / length * width / 2
    a, b = (p[0] + nx, p[1] + ny), (q[0] + nx, q[1] + ny)
    c, d = (q[0] - nx, q[1] - ny), (p[0] - nx, p[1] - ny)
    return [(a, b, c), (a, c, d)]


def _disc_tris(cx, cy, r, a0=0.0, a1=math.tau, segments=40):
    tris = []
    for i in range(segments):
        t0 = a0 + (a1 - a0) * i / segments
        t1 = a0 + (a1 - a0) * (i + 1) / segments
        tris.append(((cx, cy), (cx + r * math.cos(t0), cy + r * math.sin(t0)),
                     (cx + r * math.cos(t1), cy + r * math.sin(t1))))
    return tris


def _icon_shapes(kind, cx, cy, size):
    """Large vector copies of the Properties tab icons (Blender's own icons
    can't be drawn from Python). Returns [(color, tris), ...]."""
    u = size / 2
    bg = COL_BOX[:3] + (1.0,)
    if kind == 'OBJECT':
        orange = (0.93, 0.56, 0.20, 1.0)
        outer, t, inner = 0.78 * u, 0.13 * u, 0.36 * u
        frame = []
        for r in _frame((cx - outer + t, cy - outer + t, cx + outer - t, cy + outer - t), t):
            frame += _quad_tris(*r)
        return [(orange, frame),
                (orange, _quad_tris(cx - inner, cy - inner, cx + inner, cy + inner))]
    if kind == 'DATA':
        green = (0.02, 0.68, 0.53, 1.0)
        tl, tr, bot = (cx - 0.62 * u, cy + 0.5 * u), (cx + 0.62 * u, cy + 0.5 * u), (cx, cy - 0.62 * u)
        edges = _segment_tris(tl, tr, 0.13 * u) + _segment_tris(tr, bot, 0.13 * u) + _segment_tris(bot, tl, 0.13 * u)
        outer, inner = 0.22 * u, 0.1 * u
        corners = [p for c in (tl, tr, bot) for p in _quad_tris(c[0] - outer, c[1] - outer, c[0] + outer, c[1] + outer)]
        holes = [p for c in (tl, tr, bot) for p in _quad_tris(c[0] - inner, c[1] - inner, c[0] + inner, c[1] + inner)]
        return [(green, edges + corners), (bg, holes)]
    if kind == 'MATERIAL':
        pink = (0.72, 0.37, 0.40, 1.0)
        r, rim = 0.82 * u, 0.12 * u
        dark = _disc_tris(cx, cy, r - rim, math.pi / 2, math.pi) + _disc_tris(cx, cy, r - rim, -math.pi / 2, 0.0)
        return [(pink, _disc_tris(cx, cy, r)), (bg, dark)]
    return []


def _draw_text(text, x, y, size, color, ox, oy):
    font = 0
    _set_font_size(font, size)
    blf.color(font, *color)
    blf.position(font, x - ox, y - oy, 0)
    blf.draw(font, text)


def _draw_button(shader, rect, label, layout, ox, oy, color):
    _draw_rects(shader, [rect], color, ox, oy)
    font = 0
    _set_font_size(font, layout["foot_size"])
    w, h = blf.dimensions(font, label)
    cx = (rect[0] + rect[2] - w) / 2
    cy = (rect[1] + rect[3] - layout["foot_size"] * 0.7) / 2
    _draw_text(label, cx, cy, layout["foot_size"], COL_TEXT, ox, oy)


def draw_overlay():
    if not _state.active:
        return
    context = bpy.context
    window, area, region = context.window, context.area, context.region
    if window is None or area is None or region is None:
        return
    if window.as_pointer() != _state.window_ptr:
        return

    layout = _compute_layout(window.screen)
    _state.layout = layout
    s = layout["s"]
    ox, oy = region.x, region.y
    shader = _shader()
    gpu.state.blend_set('ALPHA')

    # Dim this region, except the highlighted holes. The main region also skips
    # the rects of regions that overlap it (e.g. transparent toolbars), since
    # those regions dim themselves and would otherwise be darkened twice.
    pad = 3 * s
    holes = [(h[0] + pad, h[1] + pad, h[2] - pad, h[3] - pad) for h in layout["holes"]]
    skip = list(holes) + list(layout["reveal"])
    if region.type == 'WINDOW':
        skip += [_region_rect(r) for r in area.regions
                 if r != region and r.width > 1 and r.height > 1]
    dim = COL_DIM_VIEW3D if (area.type == 'VIEW_3D' and region.type == 'WINDOW') else COL_DIM
    _draw_rects(shader, _subtract(_region_rect(region), skip), dim, ox, oy)

    # Highlight frames.
    for h in holes:
        _draw_rects(shader, _frame(h, 6 * s), COL_GLOW, ox, oy)
        _draw_rects(shader, _frame(h, 2 * s), COL_ACCENT, ox, oy)

    # Tooltip box.
    bx0, by0, bx1, by1 = layout["box"]
    p = layout["pad"]
    _draw_rects(shader, [layout["box"]], COL_BOX, ox, oy)
    _draw_rects(shader, [(bx0, by1 - 3 * s, bx1, by1)], COL_ACCENT, ox, oy)

    head_top = by1 - p
    title_x = bx0 + p
    if layout["icon"]:
        size = layout["icon_size"]
        icon_cx, icon_cy = bx0 + p + size / 2, head_top - size / 2
        for color, tris in _icon_shapes(layout["icon"], icon_cx, icon_cy, size):
            _draw_tris(shader, tris, color, ox, oy)
        title_x += size + 14 * s
    y = head_top - layout["head_h"] / 2 - layout["title_size"] * 0.35
    _draw_text(layout["title"], title_x, y, layout["title_size"], COL_TEXT, ox, oy)
    y = head_top - layout["head_h"] - 12 * s
    for line in layout["lines"]:
        y -= layout["line_h"]
        _draw_text(line, bx0 + p, y, layout["body_size"], COL_TEXT, ox, oy)

    nb = layout["next_btn"]
    _draw_text(layout["counter"], bx0 + p, nb[1] + 8 * s, layout["foot_size"], COL_SUBTLE, ox, oy)
    if layout["back_btn"]:
        _draw_button(shader, layout["back_btn"], "Back", layout, ox, oy, COL_BTN)
    _draw_button(shader, nb, layout["next_label"], layout, ox, oy, (0.85, 0.42, 0.05, 1.0))

    gpu.state.blend_set('NONE')


REGION_TYPES = (
    'WINDOW', 'HEADER', 'TOOL_HEADER', 'TOOLS', 'UI', 'CHANNELS', 'NAVIGATION_BAR',
    'EXECUTE', 'FOOTER', 'TOOL_PROPS', 'PREVIEW', 'ASSET_SHELF', 'ASSET_SHELF_HEADER',
)


def _space_types():
    for name in dir(bpy.types):
        if name.startswith("Space") and name != "Space":
            cls = getattr(bpy.types, name)
            if hasattr(cls, "draw_handler_add"):
                yield cls


def add_handlers():
    for space in _space_types():
        for region_type in REGION_TYPES:
            try:
                handle = space.draw_handler_add(draw_overlay, (), region_type, 'POST_PIXEL')
            except (TypeError, ValueError):
                continue  # region type doesn't exist for this editor
            _handlers.append((space, handle, region_type))


def remove_handlers():
    for space, handle, region_type in _handlers:
        try:
            space.draw_handler_remove(handle, region_type)
        except ValueError:
            pass
    _handlers.clear()


def redraw_all():
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            area.tag_redraw()


# ---------------------------------------------------------------------------
# Operator
# ---------------------------------------------------------------------------

def _inside(rect, x, y):
    return rect is not None and rect[0] <= x <= rect[2] and rect[1] <= y <= rect[3]


def _enter_step(screen):
    on_enter = _state.current().get("on_enter")
    if on_enter:
        on_enter(screen)
    redraw_all()


class WM_OT_interface_tour(bpy.types.Operator):
    """Step-by-step overlay explaining Blender's interface and basic object editing"""
    bl_idname = "wm.interface_tour"
    bl_label = "Interface Tour"

    tour: bpy.props.EnumProperty(
        name="Tour",
        items=[(key, title, "") for key, (title, _steps) in TOURS.items()],
    )
    step: bpy.props.IntProperty(name="Start Step", default=0, min=0)

    def invoke(self, context, event):
        if _state.active:
            self.report({'INFO'}, "A tour is already running")
            return {'CANCELLED'}
        _state.active = True
        _state.window_ptr = context.window.as_pointer()
        _state.steps = TOURS[self.tour][1]
        _state.step = min(self.step, len(_state.steps) - 1)
        _state.layout = None
        _state.signature = None
        _state.shading = _shading_snapshot(context.window.screen)
        add_handlers()
        context.window_manager.modal_handler_add(self)
        _enter_step(context.window.screen)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        return self.invoke(context, None)

    def _finish(self):
        _state.active = False
        _restore_shading(_state.shading)
        _state.shading = None
        remove_handlers()
        redraw_all()
        return {'FINISHED'}

    def _go(self, context, delta):
        new = _state.step + delta
        if new >= len(_state.steps):
            return self._finish()
        _state.step = max(0, new)
        _enter_step(context.window.screen)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if not _state.active:
            return self._finish()

        # The layout depends on area sizes; redraw everything if it changed
        # (e.g. the user resized an area or toggled the sidebar).
        signature = (_state.step, tuple(_area_rect(a) for a in context.window.screen.areas),
                     tuple(map(tuple, _resolve_holes(context.window.screen)[0])))
        if signature != _state.signature:
            _state.signature = signature
            redraw_all()

        if event.value != 'PRESS':
            return {'PASS_THROUGH'}

        if event.type in {'RIGHT_ARROW', 'SPACE', 'RET', 'NUMPAD_ENTER'}:
            return self._go(context, +1)
        if event.type in {'LEFT_ARROW', 'BACK_SPACE'}:
            return self._go(context, -1)
        if event.type == 'ESC':
            return self._finish()
        if event.type == 'M':
            bpy.ops.wm.url_open(url=MANUAL + _state.current()["url"])
            return {'RUNNING_MODAL'}

        layout = _state.layout
        if event.type == 'LEFTMOUSE' and layout:
            x, y = event.mouse_x, event.mouse_y
            if _inside(layout["next_btn"], x, y):
                return self._go(context, +1)
            if _inside(layout["back_btn"], x, y):
                return self._go(context, -1)
            if _inside(layout["box"], x, y):
                return {'RUNNING_MODAL'}  # swallow clicks on the tooltip itself

        return {'PASS_THROUGH'}


def menu_func(self, context):
    self.layout.separator()
    for key, (title, _steps) in TOURS.items():
        self.layout.operator(WM_OT_interface_tour.bl_idname, text=title, icon='HELP').tour = key


def register():
    bpy.utils.register_class(WM_OT_interface_tour)
    bpy.types.TOPBAR_MT_help.append(menu_func)


def unregister():
    _state.active = False
    _restore_shading(_state.shading)
    remove_handlers()
    bpy.types.TOPBAR_MT_help.remove(menu_func)
    bpy.utils.unregister_class(WM_OT_interface_tour)
