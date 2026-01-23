# Background Render Setup Guide

Two scripts are available to add the background.jpeg to your TouchDesigner project.

## 📂 Files Created

- `resources/background.jpeg` - Your background image
- `setup_background_render.py` - 3D render pipeline (full featured)
- `setup_background_simple.py` - 2D display (simple, direct)

## 🎨 Option 1: 3D Render Pipeline (Recommended)

Creates a complete 3D render setup with camera, lighting, and material.

### How to Run:

1. **Open TouchDesigner Textport:**
   - Press `Alt + T` or go to `Dialogs > Textport`

2. **Run the script:**
   ```python
   exec(open('c:/ARKHE/Projects/TouchDesigner/Eslem/setup_background_render.py').read())
   ```

3. **View the output:**
   - Navigate to `/project1/background_render/OUT`
   - This is your rendered background

### What it creates:

```
/project1/background_render/
├── bg_image (moviefileinTOP)      ← Loads background.jpeg
├── bg_camera (cameraCOMP)         ← Camera positioned at z=5
├── bg_light (lightCOMP)           ← Point light for the scene
├── bg_material (phongMAT)         ← Material with your image
├── bg_geometry (geometryCOMP)     ← 16:9 plane to display on
├── bg_render (renderTOP)          ← Renders the 3D scene
└── OUT (nullTOP)                  ← Final output (1920x1080)
```

## 🖼️ Option 2: Simple 2D Display

Creates a simple 2D image display (no 3D rendering overhead).

### How to Run:

1. **Open TouchDesigner Textport:**
   - Press `Alt + T`

2. **Run the script:**
   ```python
   exec(open('c:/ARKHE/Projects/TouchDesigner/Eslem/setup_background_simple.py').read())
   ```

3. **View the output:**
   - Navigate to `/project1/background_simple/OUT`

### What it creates:

```
/project1/background_simple/
├── bg_image (moviefileinTOP)      ← Loads background.jpeg
├── fit1 (fitTOP)                  ← Maintains aspect ratio
├── adjust (levelTOP)              ← Color/opacity adjustments
└── OUT (nullTOP)                  ← Final output
```

## 🔧 Customization

### 3D Pipeline:
- **Camera position:** Modify `bg_camera` parameters (tx, ty, tz, fov)
- **Lighting:** Adjust `bg_light` dimmer, position, type
- **Resolution:** Change `bg_render` resx/resy parameters

### 2D Pipeline:
- **Opacity:** Adjust `adjust` opacity parameter
- **Color:** Use `adjust` levelTOP for color correction
- **Scale:** Modify `fit1` parameters

## 🎭 Integration with Existing Project

Both pipelines are **completely separate** from your existing `woman_render` pipeline.

### To composite them together:

```python
# In your project, create a Composite TOP
comp = op('/project1').create(compositeTOP, 'final_composite')

# Layer background
comp.par.operand = 'background_render/OUT'

# Layer woman on top
comp.appendLayer('woman_render')

# This creates: Background + Woman character
```

## 📊 Which Should You Use?

- **Use 3D Pipeline if:**
  - You want to integrate with 3D scenes
  - You need camera control
  - You want lighting effects
  - You plan to animate the background in 3D space

- **Use 2D Pipeline if:**
  - You just want a static background
  - You want minimal performance overhead
  - You're compositing in 2D only

## ⚡ Quick Test

After running either script, check the output:

```python
# In Textport
op('/project1/background_render/OUT')    # For 3D version
op('/project1/background_simple/OUT')    # For 2D version
```

Both should show your background image!

## 🐛 Troubleshooting

### Image not loading?
- Check file path: `resources/background.jpeg` should exist
- Try absolute path in `bg_image.par.file`
- Click "Load on Start" button on bg_image operator

### Render shows black?
- Make sure `bg_light` dimmer is > 0
- Check `bg_camera` is positioned correctly (tz should be positive)
- Verify `bg_material` has the image connected

### Can't see output?
- Make sure you're looking at the `OUT` null operator
- Press `1` key over the operator to view it in viewer
- Check active flag is ON (green)

## 📝 Notes

- Both pipelines are resolution-independent
- Background image is loaded once (not streamed)
- Pipelines are color-coded in the network for easy identification
- You can have both versions in your project simultaneously
