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

## Auto-Scale
Scales Luna model based on detected face size (proxy for distance).
```python
exec(open(project.folder + '/setup_auto_scale.py').read())
```

## Window Manager
Multi-monitor view switching. Routes TOP and COMP views to 2+ screens via Python API.
```python
exec(open(project.folder + '/setup_window_manager.py').read())
```
After setup, wire video TOPs to the container's inputs, then:
```python
wm = op('/project1/window_manager').fetch('window_manager')
wm.open_all()                     # open windows on monitors
wm.switch_view(0, 'chat')         # switch screen 0 to chat
```