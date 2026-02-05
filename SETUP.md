# TouchDesigner Setup Commands

Run in TD textport/console.

## Init (run once per session)
```python
import sys; sys.path.insert(0, project.folder)
```

## Chat App
LLM chat interface with scrollable viewport and username extraction.
```python
exec(open(project.folder + '/setup_chat_app.py').read())
```

## Head Tracking
MediaPipe head rotation mapped to model. Call `recalibrate()` while looking at camera.
```python
exec(open(project.folder + '/setup_head_tracking.py').read())
```

## Mouth Deformation
Blendshape-driven lip sync on Zenna_body mesh.
```python
exec(open(project.folder + '/setup_mouth.py').read())
```