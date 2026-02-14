# Frontend-Backend Integration Guide: Position Validation with Speech Corrections

## Overview

The system is now fully integrated to use your ML models for real-time position validation and provide speech corrections. Here's how everything works together:

## Data Flow

```
Backend Models
    ↓
ML Classification (squat/pushup correctness)
    ↓
WebSocket: exercise_update message
    ├─ ml_class: "Correct Squat" | "Bad Knee Position" | etc.
    ├─ ml_confidence: 0-1
    ├─ form_quality: posture score
    ├─ feedback_codes: list of issues
    └─ rep_count, phase, confidence...
    ↓
Frontend useExercise Hook
    ├─ Captures: mlClass, mlConfidence
    ├─ Captures: formIssues, formQuality
    └─ Updates state with latest data
    ↓
PositionFeedbackPanel Component (NEW!)
    ├─ Displays ML classification with confidence
    ├─ Generates contextual correction messages
    ├─ Triggers speech synthesis for warnings
    └─ Visual feedback with status colors & icons
    ↓
QuickStartScreen
    ├─ Shows real-time position status at top
    ├─ Displays detailed feedback panel at bottom
    ├─ Integrates with rep counter and exercise flow
    └─ Handles pause/resume with feedback state
```

## Key Components Added

### 1. PositionFeedbackPanel Component
**File:** `components/fitness/position-feedback-panel.tsx`

```typescript
<PositionFeedbackPanel
  status="warning"  // "perfect" | "warning" | "error"
  message="Incorrect knee position"
  mlClass="Bad Knee Position"
  mlConfidence={0.85}
  formIssues={["knee_too_far_in", "knee_not_aligned"]}
  onSpeak={speak}  // Speech synthesis callback
  animated={true}
  className=""
/>
```

**Features:**
- ✅ Displays ML classification badge
- ✅ Shows confidence percentage
- ✅ Auto-generates French correction messages
- ✅ Lists form issues with icons
- ✅ Triggers speech on warnings
- ✅ Animated states for attention

### 2. QuickPositionStatus Component
**File:** `components/fitness/position-feedback-panel.tsx`

Quick status badge showing ML classification:
```typescript
<QuickPositionStatus 
  status="warning"
  mlClass="Knee Too Far"
  mlConfidence={0.92}
/>
```

## Integration in QuickStartScreen

The quick-start-screen now integrates position validation seamlessly:

```typescript
// Get ML data from backend
const exerciseState = useExercise();
const mlClass = exerciseState?.mlClass;
const mlConf = exerciseState?.mlConfidence;

// Get feedback with form issues
const feedbackState = useFeedback(); // Has issues[], status, message

// Speech synthesis
const { speak } = useVoice();

// Use the panel
<PositionFeedbackPanel
  status={postureStatus}
  message={postureFeedback}
  mlClass={mlClass}
  mlConfidence={mlConf}
  formIssues={feedbackState?.issues}
  onSpeak={speak}
  animated={!isPaused && !isResting}
/>
```

## How Speech Corrections Work

### Automatic Trigger
Speech is triggered when:
1. **Form has warning** (`status === "warning"`)
2. **Message changes** (detected a new issue)
3. **3-second throttle** between repeated same messages
4. **Not during rest** (paused sessions don't speak)

### Correction Messages
The component auto-generates French corrections based on ML classification:

```
ML Classification → French Correction
─────────────────────────────────────
"Correct Squat" → "Excellente position! Continuez comme ça."
"Knee Too Far" → "Vérifiez vos genoux. Gardez-les alignés avec vos pieds."
"Back Rounded" → "Colonne vertébrale droite. Rentrez légèrement le bassin."
"Bad Hip" → "Vérifiez la position de vos hanches. Gardez-les stables."
"Elbow Wrong" → "Positionnez correctement vos bras. Ils doivent être alignés."
```

## Backend Configuration for ML Integration

Ensure your backend is sending ML classification in the `exercise_update` message:

```python
# In exercise_engine.py update() method
exercise_result = {
    "exercise": exercise_type.value,
    "phase": self.state.phase,
    "rep_count": self.state.rep_count,
    "confidence": confidence,
    "form_quality": form_score,
    "feedback_codes": issues,
    # ML Classification from LSTM model
    "ml_label": ml_prediction,        # "Correct Squat", "Bad Knee", etc.
    "ml_confidence": ml_confidence,   # 0-1 confidence score
    "events": events
}
```

## Testing the Integration

### 1. Check Backend ML Output
```python
# Run backend and monitor logs
python main.py

# Look for:
# [EXERCISE-ERR] or successful exercise_update with ml_label
```

### 2. Check Frontend WebSocket
Open browser DevTools → Networks → WS → Filter for messages:
```json
{
  "type": "exercise_update",
  "data": {
    "ml_class": "Correct Squat",
    "ml_confidence": 0.92,
    "form_quality": 0.85,
    "feedback_codes": ["good_position"]
  }
}
```

### 3. Verify Speech Works
- Position in incorrect posture
- Listen for French correction message
- Check browser volume/permissions

### 4. Visual Feedback Test
- Look for status badge in top-left
- Bottom panel should show color changes
- Warning status = amber color + animation
- Perfect status = green/emerald color

## Customization Guide

### Change Correction Language
Edit `position-feedback-panel.tsx` in the `useEffect` that generates `correctionMessage`:

```typescript
// German example
if (mlClass.includes("Correct")) {
  correction = "Ausgezeichnete Position! Weitermachen.";
}
```

### Adjust Speech Throttle
Change the 3000ms timeout in `position-feedback-panel.tsx`:
```typescript
setTimeout(() => setIsSpoken(false), 3000); // Change this
```

### Modify Colors/Styling
Status colors are defined in `getStyles()`:
```typescript
case "perfect":
  return {
    bg: "bg-emerald-500/10",  // Change colors here
    border: "border-emerald-500/50",
    // ...
  }
```

### Add New Form Issues
Add mappings in the `useEffect` that generates corrections:
```typescript
} else if (mlClass.includes("Ankle")) {
  correction = "Vérifiez la position de vos chevilles...";
}
```

## Troubleshooting

### Speech Not Working
1. ✅ Check browser permissions (DevTools → Settings → Permissions)
2. ✅ Verify speaker volume isn't muted
3. ✅ Test `window.speechSynthesis.speak()` in console
4. ✅ Try different browser (Chrome/Edge better for TTS)

### ML Classification Not Showing
1. ✅ Check backend is sending `ml_class` in `exercise_update`
2. ✅ Verify WebSocket connection (should see "Connected" in top-left)
3. ✅ Check exerciseState has mlClass property
4. ✅ Ensure LSTM model is loaded on backend

### Wrong Corrections
1. ✅ Update ML classification labels in backend
2. ✅ Add new keywords to switch statement in position-feedback-panel.tsx
3. ✅ Test with print statements in backend

## Architecture Improvements Made

### Before
- Only basic form feedback
- No ML classification display
- No automatic speech corrections
- Manual posture status updates

### After ✨
- Real-time ML classification confidence display
- Automatic contextual speech corrections
- Visual feedback with status colors & icons
- Form issues listed with icons
- Integrated pause/resume with feedback state
- Throttled speech to avoid overwhelming user
- Animated feedback states

## Performance Notes

- **Speech**: Non-blocking (uses Web Speech API)
- **State Updates**: Minimal (throttled to 3s)
- **Rendering**: Optimized with React.memo (consider adding if needed)
- **WebSocket**: Already optimized in use-backend.ts

## Next Steps

1. ✅ Start backend: `python main.py` (from backend folder)
2. ✅ Start frontend: `npm run dev` (from frontend folder)
3. ✅ Open http://localhost:3000
4. ✅ Start a session and perform exercises
5. ✅ Listen for French corrections when form is bad
6. ✅ Watch status badges update with ML confidence

## API Reference

### ML Data Available in Frontend

From `useExercise()`:
- `mlClass: string | null` - e.g., "Correct Squat"
- `mlConfidence: number | null` - 0-1 confidence score
- `formQuality: number` - 0-1 posture quality score
- `formIssues: string[]` - List of detected issues

From `useFeedback()`:
- `status: "perfect" | "warning" | "error"`
- `message: string` - Main feedback text
- `issues: string[]` - Detailed issues list
- `mlClass: string | null`
- `mlConfidence: number | null`

### WebSocket Messages

**exercise_update** (includes ML classification):
```json
{
  "type": "exercise_update",
  "data": {
    "exercise": "squat",
    "phase": "descent",
    "rep_count": 5,
    "confidence": 0.95,
    "form_quality": 0.88,
    "feedback_codes": ["form_warning"],
    "ml_class": "Incorrect Squat",
    "ml_confidence": 0.87,
    "events": []
  }
}
```

**feedback** (includes form issues):
```json
{
  "type": "feedback",
  "data": {
    "status": "warning",
    "message": "Vérifiez votre posture!",
    "issues": ["knee_too_far", "back_rounded"],
    "ml_class": "Bad Knee Position",
    "ml_confidence": 0.92
  }
}
```

---

**Integration Complete!** 🎉

Your frontend is now fully integrated with backend ML models for real-time position validation with automatic French speech corrections.
