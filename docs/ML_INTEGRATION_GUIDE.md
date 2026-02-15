# Coach Sportif - ML Position Validation Integration

## 🎯 What's New

Your frontend is now **fully integrated** with your backend ML models for real-time position validation and automatic French speech corrections!

### Features
- ✅ **Real-time ML Classification** - Displays squat/pushup correctness
- ✅ **Confidence Scoring** - Shows how sure the model is (0-100%)
- ✅ **Automatic Speech Corrections** - French voice feedback on bad form
- ✅ **Visual Feedback** - Color-coded status (green=good, amber=warning)
- ✅ **Form Issues List** - Detailed corrections for each problem
- ✅ **Smart Throttling** - Speech not repeated < 3 seconds

## 🚀 Quick Start

### 1. Start Backend
```powershell
cd backend
python main.py
```

**Expected output:**
```
[STARTUP] Initializing systems...
[EXERCISE] Loaded LSTM model from models/model_lstm_tache2.h5
[STARTUP] Systems ready
[APP] Backend ready!
```

### 2. Start Frontend
```powershell
cd frontend
npm run dev
```

**Expected output:**
```
> next dev
  Local:        http://localhost:3000
  Ready in 2.5s
```

### 3. Open Browser
```
http://localhost:3000
```

### 4. Start a Workout
1. Click "Quick Start" or "Custom Chain"
2. Select exercises (Squat, Pushup recommended for ML)
3. **Perform exercises with bad form intentionally**
4. 👂 **Listen for French speech corrections!**

## 📍 Where to See ML Feedback

### Top-Left Corner
**Quick Position Status Badge** - Shows current ML classification
```
🟢 Correct Squat 92%
🟠 Knee Too Far 87%
🔴 Bad Pushup 95%
```

### Bottom-Left Panel
**Detailed Feedback** - Full corrections with explanation
```
┌─────────────────────────────────────┐
│ 🤖 Bad Knee Position                │
│    87% confidence                   │
│                                      │
│ 💡 Vérifiez vos genoux.            │
│    Gardez-les alignés avec vos     │
│    pieds.                           │
│                                      │
│ Issues:                             │
│  • knee_too_far_in                 │
│  • knee_not_aligned                │
└─────────────────────────────────────┘
```

### Top Badge
Updates automatically as you exercise

## 🗣️ Speech Feedback System

### Automatic Triggers
Speech activates when:
1. ✅ Form is incorrect (warning status)
2. ✅ New issue detected (message changed)
3. ✅ Not throttled within 3 seconds
4. ✅ Session is active (not paused/resting)

### Example Flow
```
You do a squat with knees too far in
    ↓
Backend LSTM predicts: "Squat Knee Caving" (0.89 confidence)
    ↓
Frontend receives exercise_update with ml_class
    ↓
PositionFeedbackPanel detects warning status
    ↓
Generates French correction: "Vérifiez vos genoux..."
    ↓
Browser speaks correction via Web Speech API
    ↓
You hear: "Vérifiez vos genoux. Gardez-les alignés avec vos pieds."
```

## 📊 ML Classification Reference

### Squat Classifications
- ✅ **Correct Squat** - Perfect form
- ❌ **Squat Shallow** - Not going low enough
- ❌ **Squat Forward Lean** - Leaning too far forward
- ❌ **Squat Knee Caving** - Knees turning inward
- ❌ **Squat Heels Off** - Heels lifting off ground
- ❌ **Squat Asymmetric** - Uneven side to side

### Pushup Classifications
- ✅ **Pushup Correct** - Perfect form
- ❌ **Pushup Incorrect** - General form issues

### Other Exercises
Uses Correction ONNX model for feedback

## 🔧 Testing the Integration

### Run Test Script
```powershell
python test_ml_integration.py
```

This verifies:
- ✅ Backend is running
- ✅ LSTM model is loaded
- ✅ WebSocket works
- ✅ Models are ready

### Manual Testing Checklist
- [ ] Backend logs show "Loaded LSTM model"
- [ ] Frontend connects (top bar shows "Connected")
- [ ] Start session with squat selected
- [ ] Status badge appears in top-left
- [ ] Perform bad-form squat
- [ ] Listen for French speech correction
- [ ] Panel updates with feedback
- [ ] Correction message changes with new form issue

### Debug Mode
Enable debug logs in browser:
```javascript
// In browser console
localStorage.setItem('debug', 'true');
```

Then check Network tab for WebSocket messages:
```json
{
  "type": "exercise_update",
  "data": {
    "ml_class": "Squat Knee Caving",
    "ml_confidence": 0.87,
    "form_quality": 0.65
  }
}
```

## 🎨 Component Structure

### New Components
- **PositionFeedbackPanel** - Main feedback display with speech
- **QuickPositionStatus** - Quick status badge

### Updated Components
- **quick-start-screen.tsx** - Integrated ML feedback
- **use-backend.ts** - Already captures ML data

### Data Flow
```
Backend ML Model
    ↓ (WebSocket)
exercise_update message
    ↓
useExercise() hook
    ↓
exerciseState.mlClass
exerciseState.mlConfidence
    ↓
PositionFeedbackPanel
    ├─ Displays classification
    ├─ Generates correction
    └─ Triggers speech
    ↓
User hears correction 🎵
```

## 🔊 Speech Customization

### Change Language
Edit `components/fitness/position-feedback-panel.tsx`:
```typescript
// Around line 60
useEffect(() => {
  if (!mlClass) return;

  let correction = "";
  if (mlClass.includes("Correct")) {
    correction = "Excellent position! Keep it up."; // English
  }
  // ...
}, [mlClass]);
```

### Adjust Speech Throttle
Change 3000ms timeout:
```typescript
// Around line 40
setTimeout(() => setIsSpoken(false), 5000); // 5 seconds instead
```

### Change Colors
Edit styling in `getStyles()`:
```typescript
case "perfect":
  return {
    bg: "bg-color/10",  // Change here
    border: "border-color/50",
  }
```

## 📱 Browser Compatibility

| Browser | Status | Web Speech |
|---------|--------|-----------|
| Chrome | ✅ Full | Yes |
| Edge | ✅ Full | Yes |
| Firefox | ⚠️ Limited | No |
| Safari | ✅ Full | Yes |

**Note:** Firefox doesn't support Web Speech API. Speech won't work in Firefox but visual feedback still shows.

## 🐛 Troubleshooting

### Speech Not Working
**Problem:** No audio feedback
```
Solutions:
1. Check browser volume isn't muted
2. Check browser permissions (DevTools → Settings → Permissions)
3. Try Chrome or Edge (Firefox has no Web Speech API)
4. Clear browser cache: Ctrl+Shift+Delete
5. Test in console: window.speechSynthesis.speak(new SpeechSynthesisUtterance("Test"))
```

### ML Classification Not Showing
**Problem:** Status badge doesn't appear
```
Solutions:
1. Backend running? Check port 8000
2. LSTM loaded? Check backend logs for "Loaded LSTM"
3. WebSocket connected? Check browser DevTools → Network → WS
4. Right exercise? Works best with squat/pushup
5. Form different enough? ML needs poor form to trigger
```

### Wrong Corrections
**Problem:** Speech says wrong thing
```
Solutions:
1. Check backend logs for ML predictions
2. Verify model confidence > 0.80
3. Update correction messages in position-feedback-panel.tsx
4. Add new keywords to switch statement
```

### Session Crashes
**Problem:** App stops responding
```
Solutions:
1. Check browser console for JS errors
2. Restart backend and frontend
3. Clear browser cache
4. Check backend logs for exceptions
```

## 📈 Performance Notes

- **ML Inference:** ~50-100ms per frame (background)
- **Speech:** Non-blocking (Web Speech API handles it)
- **UI Updates:** ~60fps
- **WebSocket:** 30fps keypoint updates

## 🎓 Understanding the Data

### exercise_update Message
```json
{
  "type": "exercise_update",
  "data": {
    "exercise": "squat",
    "phase": "descent",
    "rep_count": 5,
    "confidence": 0.95,
    "form_quality": 0.88,
    "ml_class": "Squat Correct",      // ML Classification ← NEW
    "ml_confidence": 0.92,            // Confidence 0-1 ← NEW
    "feedback_codes": ["good_form"],
    "events": []
  }
}
```

### feedback Message
```json
{
  "type": "feedback",
  "data": {
    "status": "perfect",
    "message": "Posture parfaite",
    "ml_class": "Correct Squat",      // Classification
    "ml_confidence": 0.92,            // Confidence
    "issues": []
  }
}
```

## 📚 Architecture

```
┌─────────────────┐
│  ML Models      │
├─────────────────┤
│ • LSTM (squat)  │
│ • LSTM (pushup) │
│ • ONNX (others) │
└────────┬────────┘
         │ Predictions
         ↓
┌──────────────────────┐
│  exercise_engine.py  │
├──────────────────────┤
│ Updates state with   │
│ ml_label &           │
│ ml_confidence        │
└────────┬─────────────┘
         │ WebSocket
         ↓
┌────────────────────────────────┐
│  Frontend (React)              │
├────────────────────────────────┤
│ useExercise() hook             │
│  → mlClass, mlConfidence       │
│  → Passed to PositionFeedback  │
│                                │
│ PositionFeedbackPanel          │
│  → Displays classification     │
│  → Generates correction text   │
│  → Triggers Web Speech API     │
│                                │
│ User sees & hears feedback! 🎵 │
└────────────────────────────────┘
```

## ✅ Next Steps

1. **Verify Setup**
   ```bash
   python test_ml_integration.py
   ```

2. **Start Backend**
   ```bash
   cd backend && python main.py
   ```

3. **Start Frontend**
   ```bash
   cd frontend && npm run dev
   ```

4. **Test Manually**
   - Do squats with bad form
   - Listen for French corrections
   - Check status badges update

5. **Customize as Needed**
   - Change speech language
   - Adjust correction messages
   - Modify colors/styling

## 📞 Support

If something isn't working:
1. Check backend logs for LSTM loading errors
2. Verify WebSocket connection in browser DevTools
3. Run `test_ml_integration.py` for diagnostics
4. Check browser console for JavaScript errors
5. Ensure LSTM model file exists: `backend/models/model_lstm_tache2.h5`

## 🎉 You're All Set!

Your Coach Sportif system is now fully integrated with:
- ✅ Real-time ML position validation
- ✅ Automatic speech corrections in French
- ✅ Visual feedback with confidence scoring
- ✅ Form issue detection and listing

Start a session and perform exercises with intentional bad form to hear the corrections in action! 🏋️
